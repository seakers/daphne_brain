from __future__ import division, absolute_import, print_function
import os
import pandas as pd
import pickle
from scipy.io import loadmat
import scipy.io
from EDL.dialogue.func_helpers import CalculateFuncs, ScorecardDataFrameFuncs, get_variable_info, correlation_multiprocessing
import yaml
import csv
from py2neo import Graph, Node, Relationship, NodeMatcher
import json
from scipy import stats
from sklearn.utils import resample
from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import get_variable_info, ScorecardDataFrameFuncs
from EDL.models import EDLContextScorecards
from auth_API.helpers import get_or_create_user_information, get_user_information
import numpy as np
from collections import OrderedDict


def create_csv_to_load(file_to_load, mission_name, ext_id,  user_info):
    mission_name = user_info.edlcontext.current_mission
    matout_path = user_info.edlcontext.current_mat_file
    file_to_search = os.path.basename(matout_path.replace(".mat", ".yml"))
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)

    if scorecard_query.count() > 0 & scorecard_query.first().current_scorecard_df_db.nbytes > 0:
        scorecard = scorecard_query.first()
        db_template = pickle.loads(scorecard.current_scorecard_df_db)
    elif scorecard_query.count() > 0 & scorecard_query.first().current_scorecard_df_db.nbytes < 1:
        scorecard = scorecard_query.first()
        db_template = pickle.loads(scorecard.current_scorecard_df_db)
    else:
        scorecard = scorecard_query.first()
        df_labeled = pickle.loads(scorecard.current_scorecard_df)

        scorecard_path = '/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecards/' + file_to_search
        with open(scorecard_path, encoding='utf-8') as file_to_search:
            scorecard_dict = yaml.load(file_to_search)
            df_yaml = pd.DataFrame(scorecard_dict)

        db_template = ScorecardDataFrameFuncs.scorecard_df_for_db(matout_path, user_info)

        db_template['event_id'] = db_template['event_ext'].astype(str) + ext_id
        db_template['seg_id'] = db_template['segment_name'].astype(str) + ext_id
        db_template['metric_id'] = db_template['metric_name'].astype(str) + ext_id

        # save the dataframe
        loc_db = EDLContextScorecards.objects.get(scorecard_name=file_to_load.replace(".mat", ".yml")).id
        db_row = EDLContextScorecards.objects.get(id=loc_db)
        db_row.current_scorecard_df_db = pickle.dumps(db_template)
        db_row.save()


    list_of_dicts = db_template.T.apply(lambda x: x.dropna().to_dict()).tolist()
    # export_csv = db_template.to_csv('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/db_templates/db_temp_no_dupl.csv')

    return 'Temporary csv with data has been created', list_of_dicts

def db_transaction(list_of_dicts, file_to_load, mission_name, ext_id, description, user_info):
    ''' This script creates a new Architecture (simulation) node along with its children nodes'''
    csv.field_size_limit(100000000)
    node_type = 'Simulation'
    new_arch_name = file_to_load
    new_arch_dataset_type = "simulation"
    new_arch_description = description
    new_arch_path = '/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/db_templates/db_temp_no_dupl.csv'

    landing_site = 'JEZ'
    # ''' Connect to graph'''
    graph = Graph("http://localhost:7474", user="neo4j", password="edldb")

    # ''' Begin transaction'''
    new_trans = graph.begin()
    new_sim = Node(node_type, new_arch_name, name=new_arch_name, desc=new_arch_description, dtype=new_arch_dataset_type,
                   landing_site=landing_site)
    new_trans.create(new_sim)
    new_trans.commit()

    # """ Create relationship"""
    rel_query = """
    MATCH (a:Mission),(b:Simulation)
    WHERE a.name = 'Mars2020' AND b.name = '""" + str(new_arch_name) + """'
    CREATE (a)-[r:HAS_SIMULATION { name: a.name + '<->' + b.name }]->(b)
    RETURN type(r), r.name
    """
    graph.run(rel_query)
    with open(new_arch_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        reader2 = list_of_dicts
        for row in reader2:
            # Pass dict to Cypher and build query.
            query = """
            UNWIND {segment} AS e

            MERGE (segment:Segment {id:e.seg_id})
            SET segment.id = e.seg_id,
                segment.name = e.segment_name

            MERGE (a:Simulation { name: '""" + new_arch_name + """'})
            MERGE (a)-[:HAS_SEGMENT]->(segment)

            MERGE (event:Event {id:e.event_id})
            SET event.id = e.event_id,
                event.name = e.event_name,
                event.event_ext = e.event_ext

            MERGE (segment)-[:HAS_EVENT]->(event)

            MERGE (metric:Metric {id:e.metric_id})
            SET metric.id = e.metric_id,
                metric.name = e.metric_name,
                metric.prctile_1 = e.prctile_1,
                metric.prctile_99 = e.prctile_99,
                metric.average = e.average,
                metric.variance = e.variance,
                metric.units = e.units
                

            MERGE (event)-[:HAS_METRIC]->(metric)
            """

            # Send Cypher query.
            graph.run(query, segment=row)
            print("Segment with events added !\n")

    # ''' ADD RELATIONSHIPS TO EVENTS AND SEGMENTS'''
    seg_query = """
    MATCH (n:Segment) RETURN (n.name)
    """
    current_segments = [item[0] for item in list(graph.run(seg_query)._result._records)]
    order = [2,3, 1]
    segments_sorted = [x for y, x in sorted(zip(order, current_segments))]
    segments_sorted = ['entry', 'parachute_descent', 'powered_flight']

    # ''' ADD RELATIONSHIPS TO EVENTS AND SEGMENTS'''
    ev_query = """
    MATCH (n:Event) RETURN (n.name)
    """
    current_events = [item[0] for item in list(graph.run(ev_query)._result._records)]
    order = [2, 3, 7, 8, 4, 6 , 5, 10, 9, 1]
    events_sorted = [x for y, x in sorted(zip(order, current_events))]
    events_sorted = ['entry_interface', 'parachute_deploy', 'heatshield_separation', 'backshell_separation',
                       'powered_approach',
                       'constant_velocity', 'constant_deceleration', 'throttle_down', 'skycrane', 'touchdown']

    for i in range(len(segments_sorted) - 1):
        query = """
        MATCH (a:Segment),(b:Segment)
        WHERE a.name = '""" + segments_sorted[i] + """' AND b.name = '""" + segments_sorted[i + 1] + """'
        CREATE (a)-[r:IS_AFTER { name: a.name + '<->' + b.name }]->(b)
        RETURN type(r), r.name
        """
        graph.run(query)

    for i in range(len(events_sorted) - 1):
        query = """
        MATCH (a:Event),(b:Event)
        WHERE a.name = '""" + events_sorted[i] + """' AND b.name = '""" + events_sorted[i + 1] + """'
        CREATE (a)-[r:IS_AFTER { name: a.name + '<->' + b.name }]->(b)
        RETURN type(r), r.name
        """
        graph.run(query)

    return 'Graph has been added'