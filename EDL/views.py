import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from EDL import sensitivity_analysis, edl_data_mining, edl_db_loader

from auth_API.helpers import get_user_information
from EDL.models import EDLContextScorecards
from EDL.dialogue.dialogue_functions import create_cormat, load_scorecard
import pickle
import scipy
from py2neo import Graph, Node, Relationship, NodeMatcher
from daphne_context.models import UserInformation


class MetricsOfInterest(APIView):
    def get(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        return Response({ "metrics_list": json.loads(user_info.edlcontext.current_metrics_of_interest)})

class ChatHistory(APIView):
    def get(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        return Response({ "chat_list": ["this", 'is', 'the', 'chat']})

class SensitivityAnalysis(APIView):
    def post(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        metric_name = request.data['metric_name']
        input_data_type = request.data["input_data_type"]
        event_selection = request.data["event_selection"]
        metric_type = request.data["data_type"]
        boundary = request.data["divide_data_by"]
        cutoff_val = request.data['cutoff_val']
        cutoff_val2 = request.data['cutoff_val2']
        event_options = request.data['event_opts']
        dataset_opts= request.data['dataset_opts']
        dataset_min = request.data['dataset_min']
        dataset_max= request.data['dataset_max']
        event_start = request.data['event_start']

        sub_df = sensitivity_analysis.run_SA(metric_name, metric_type, input_data_type, event_selection, boundary,
                                             cutoff_val, cutoff_val2, event_options, dataset_opts, dataset_min, dataset_max, event_start, user_info)
        p_vals = (sub_df['p_vals']).tolist()
        input_name = (sub_df['metric_name']).tolist()
        input_descr = (sub_df['description']).tolist()
        input_label = (sub_df['label']).tolist()
        # input_model = (sub_df['model']).tolist()
        distance = (sub_df['distance']).tolist()
        # input_label = []
        input_model = []
        # input_descr = []
        return Response({"pvals": p_vals, "input_name": input_name, "input_description": input_descr,
                         "input_label": input_label, "input_model": input_model, "distance": distance})


class ImportDataAvail(APIView):
    def post(self, request, format = None):
        user_info = get_user_information(request.session, request.user)

        file_to_load = request.data['filename']
        file_to_load = file_to_load
        user_info.edlcontext.current_mat_file = os.path.join('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/edl_datasets/', file_to_load)
        user_info.edlcontext.current_mat_file_for_print = file_to_load
        user_info.edlcontext.save()

        file_to_load = os.path.basename(user_info.edlcontext.current_mat_file)
        file_to_search = file_to_load.replace(".mat", ".yml")

        scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
        if scorecard_query.count() > 0:
            scorecard_status = 'Scorecard for this simulation cases exists'
            scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
            scorecard = scorecard_query.first()
            flagged_df = pickle.loads(scorecard.current_scorecard_df_fail)
            out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_flag)
            scorecard_df = pickle.loads(scorecard.current_scorecard_df)
            metrics_of_interest = list(flagged_df['metric_name']) + list(out_of_spec_df['metric_name'])
            user_info.edlcontext.current_metrics_of_interest = json.dumps(metrics_of_interest)
            user_info.edlcontext.save()
            metrics_available = list(scorecard_df['metric_name'])

        else:
            scorecard_status = "Scorecard did not exist, new scorecard was created"
            scorecard_operation = load_scorecard('None', user_info.edlcontext.current_mat_file, user_info)
            scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
            scorecard = scorecard_query.first()
            flagged_df = pickle.loads(scorecard.current_scorecard_df_fail)
            out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_flag)
            scorecard_df = pickle.loads(scorecard.current_scorecard_df)
            scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
            metrics_available = list(scorecard_df['metric_name'])
        ''' Check if correlation matrix exists '''
        if scorecard_query.first().current_corr_mat_status == 'false':
            cormat_status = 'Correlation matrix does not exist, was created now'
            message = create_cormat(user_info.edlcontext.current_mat_file, user_info)

        else:
            cormat_status = 'Correlation matrix already exists'

        list_mat_variables = [i[0] for i in scipy.io.whosmat(user_info.edlcontext.current_mat_file)]
        return Response({'file_status': 'data loaded', 'scorecard_status': scorecard_status, 'cormat_status': cormat_status,
                         'metrics_available': metrics_available, 'list_variables': list_mat_variables})

# class PostScorecardStatus(APIView):
#     def get(self, request, format = None):
#         user_info = get_user_information(request.session, request.user)
#         file_to_load = os.path.basename(user_info.edlcontext.current_mat_file)
#         file_to_search = file_to_load.replace(".mat", ".yml")
#         scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
#         if scorecard_query.count() > 0:
#             scorecard = scorecard_query.first()
#             scorecard_status = 'Scorecard for this simulation cases exists'
#         else:
#             scorecard_status = "Scorecard does not exist"
#         return Response({'scorecard_status': scorecard_status})
class EDLDataMining(APIView):
    def post(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        cases_option = request.data['cases_option']
        percentile = request.data['percentile']
        direction = request.data['direction']

        if cases_option == 'plot-selection':
            selected_cases = request.data['selected_cases_dm']
        else:
            selected_cases = 'all'
        metric_name = request.data['metric_name']

        matfile = user_info.edlcontext.current_mat_file
        features = edl_data_mining.run_datamining_edl(selected_cases, metric_name, matfile, cases_option, percentile, direction, user_info)
        rules = [o.expression for o in features]
        complexity = [o.complexity for o in features]
        recall = [o.metrics[3] for o in features]
        precision = [o.metrics[2] for o in features]



        status = 'loading'

        return Response({'data_mining_status':status, 'rules': rules, 'complexity': complexity, 'recall':recall,
                         'precision': precision})

class ImportDataToDB(APIView):
    def post(self, request, format = None):
        user_info = get_user_information(request.session, request.user)

        file_to_load = request.data['filename']
        mission_name = request.data['mission_name']
        db_ID = request.data['db_ID']
        description = request.data['db_description']
        file_to_search = os.path.basename(file_to_load.replace(".mat", ".yml"))
        scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)

        # ''' Connect to graph'''
        graph = Graph("http://localhost:7474", user="neo4j", password="edldb")
        # check if node exists in database
        sim_query = """MATCH (s: Simulation{name: '""" + file_to_load + """'}) RETURN s"""
        res = list(graph.run(sim_query))

        # if len(res) > 0:
        #     return Response({'file_status': 'Simulation Case already exists in database.'})
        #
        # else:
        csv_status, list_of_dicts = edl_db_loader.create_csv_to_load(file_to_load, mission_name, db_ID, user_info)

        # Check if file exists in Database
        if mission_name == 'Mars2020':
            dataset_trans = edl_db_loader.db_transaction(list_of_dicts, file_to_load, mission_name, db_ID, description, user_info)
        return Response({'file_status': 'Simulation Loaded to DB !'})
