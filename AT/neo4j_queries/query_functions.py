from neo4j import GraphDatabase, basic_auth


def set_up_connection():
    # setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()
    return session


def diagnose_symptoms_by_subset_of_anomaly(symptoms):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # build the query based on the symptoms list
    query = ''
    for index, symp in enumerate(symptoms):
        query = query + 'MATCH (m' + str(index) + ':Measurement)-[r' + str(index) + ':' + symp['relationship'] + ']->(g:Anomaly) '
    query = query + 'WHERE '
    for index, symp in enumerate(symptoms):
        if (index + 1) < len(symptoms):
            query = query + 'm' + str(index) + '.Name=\'' + symp['measurement'] + '\' AND '
        else:
            query = query + 'm' + str(index) + '.Name=\'' + symp['measurement'] + '\' RETURN DISTINCT g.Title'

    # query the database
    result = session.run(query)
    diagnosis = [node[0] for node in result]
    return diagnosis


def diagnose_symptoms_by_intersection_with_anomaly(requested_symptoms):
    # Symptoms dictionary for comparison
    comparison_symptoms = []
    for symptom in requested_symptoms:
        display_name = symptom['display_name']
        relationship = symptom['relationship']
        item = {'measurement': display_name, 'relationship': relationship}
        comparison_symptoms.append(item)

    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build the query based on the symptoms list
    query = ''
    for index, symp in enumerate(requested_symptoms):
        query = query + 'MATCH (m' + str(index) + ':Measurement)-[r' + str(index) + ':' + symp['relationship'] + ']->(g:Anomaly) '
    query = query + 'WHERE '
    for index, symp in enumerate(requested_symptoms):
        if (index + 1) < len(requested_symptoms):
            query = query + 'm' + str(index) + '.Name=\'' + symp['measurement'] + '\' OR '
        else:
            query = query + 'm' + str(index) + '.Name=\'' + symp['measurement'] + '\' RETURN DISTINCT g.Title'

    # Query the database and parse the result (which is a list of the anomalies which symptoms have non empty
    # intersection with the requested symptoms)
    result = session.run(query)
    diagnosis = [node[0] for node in result]

    # For each anomaly, build a dictionary where each key is the anomaly and the value is a list of its symptoms
    symptoms_of_each_anomaly = {}
    for anomaly in diagnosis:
        anomaly_symptoms = retrieve_symptoms_from_anomaly(anomaly)
        aux = []
        for symptom in anomaly_symptoms:
            relationship = symptom['relationship']
            if relationship == "Upper Warning Limit" or relationship == "Upper Critic Limit":
                relationship = 'Exceeds_UWL'
            else:
                relationship = 'Exceeds_LWL'
            symptom['relationship'] = relationship
            aux.append(symptom)
        symptoms_of_each_anomaly[anomaly] = aux

    # For each anomaly, build a dictionary where each key is the anomaly and the value is the cardinality of
    # (requested symptoms INTERSECTED WITH the symptoms of that anomaly)
    cardinality_for_each_anomaly = {}
    size_of_each_anomaly = {}
    for anomaly in diagnosis:
        cardinal = 0
        anomaly_symptoms = symptoms_of_each_anomaly[anomaly]
        for anomaly_symptom in anomaly_symptoms:
            for comparison_symptom in comparison_symptoms:
                measurements_are_equal = (anomaly_symptom['measurement'] == comparison_symptom['measurement'])
                relationships_are_equal = (anomaly_symptom['relationship'] == comparison_symptom['relationship'])
                if measurements_are_equal and relationships_are_equal:
                    cardinal += 1
        cardinality_for_each_anomaly[anomaly] = cardinal
        size_of_each_anomaly[anomaly] = len(anomaly_symptoms)

    # Ordered anomalies by cardinality of the intersection
    ordered_anomalies = {k: v for k, v in sorted(cardinality_for_each_anomaly.items(), key=lambda item1: item1[1])}

    # Convert to list
    ordered_diagnosis = list(ordered_anomalies.keys())

    # Cast list to top 7 items
    top_n_diagnosis = []
    sizelimit = min(7, len(ordered_diagnosis))
    for i in range(0, sizelimit):
        top_n_diagnosis.append(ordered_diagnosis[i])

    # Add score
    fancy_diagnosis = []
    print(size_of_each_anomaly)
    print(cardinality_for_each_anomaly)
    for anomaly in top_n_diagnosis:
        # Parsing
        total_requested_symptoms = len(requested_symptoms)
        cardinality = cardinality_for_each_anomaly[anomaly]
        total_anomaly_symptoms = size_of_each_anomaly[anomaly]
        # Scores
        score_intersection_fulfils_all_requested_symptoms = cardinality / total_requested_symptoms
        score_intersection_fulfils_all_anomaly_symptoms = cardinality / total_anomaly_symptoms
        score = score_intersection_fulfils_all_anomaly_symptoms * score_intersection_fulfils_all_requested_symptoms
        score = round(score, 2)
        item = {'name': anomaly, 'score': score}
        fancy_diagnosis.append(item)

    # Return result
    diagnosis = fancy_diagnosis

    return diagnosis


def retrieve_all_anomalies():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = 'MATCH (n:Anomaly) RETURN DISTINCT n.Title'
    result = session.run(query)

    # Parse the result
    anomaly_list = []
    for item in result:
        anomaly_list.append(item[0])

    return anomaly_list


def retrieve_all_measurements():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = 'MATCH (m:Measurement) RETURN DISTINCT m.Name'
    result = session.run(query)

    # Parse the result
    measurement_list = []
    for item in result:
        measurement_list.append(item[0])

    return measurement_list


def retrieve_all_measurements_parameter_groups():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = 'MATCH (m:Measurement) RETURN DISTINCT m.ParameterGroup'
    result = session.run(query)

    # Parse the result
    measurement_list = []
    for item in result:
        if item[0] is not None and item[0] != '':
            measurement_list.append(item[0])

    return measurement_list


def retrieve_all_procedures():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = 'MATCH (p:Procedure) RETURN DISTINCT p.Title'
    result = session.run(query)

    # Parse the result
    procedure_list = []
    for item in result:
        procedure_list.append(item[0])

    return procedure_list


def retrieve_procedures_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[s:Solution]-(p:Procedure) WHERE a.Title='" + anomaly_name + "' RETURN p.Title ORDER BY s.Order"
    result = session.run(query)

    # Parse the result
    procedure_list = []
    for item in result:
        procedure_list.append(item[0])

    return procedure_list


def retrieve_affected_components_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (p:Procedure)-[:Comprises]-(c:Component) WHERE p.Title='" + procedure + "' RETURN DISTINCT c.Title"
    result = session.run(query)

    # Parse the result
    component_list = []
    for item in result:
        component_list.append(item[0])

    return component_list


def retrieve_time_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (p:Procedure) WHERE p.Title='" + procedure + "' RETURN DISTINCT p.ETR"
    result = session.run(query)

    # Parse the result
    procedure_time_list = []
    for item in result:
        time_string = item[0]
        time_int = int(time_string.strip(' Minutes'))
        procedure_time_list.append(time_int)
    time = procedure_time_list[0]

    return time


def retrieve_risks_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[:Can_Cause]-(r:Risk) WHERE a.Title='" + anomaly_name + "' RETURN DISTINCT r.Title"
    result = session.run(query)

    # Parse the result
    risks_list = []
    for item in result:
        risks_list.append(item[0])

    return risks_list


def retrieve_affected_subsystems_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[:Affects]-(s:SubSystem) WHERE a.Title='" + anomaly_name + "' RETURN DISTINCT s.Title"
    result = session.run(query)

    # Parse the result
    subsystems_list = []
    for item in result:
        subsystems_list.append(item[0])

    return subsystems_list


def retrieve_symptoms_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query to obtain the affected measurements that exceed the UWL
    query_uwl = "MATCH (a:Anomaly)-[r:Exceeds_UWL]-(m:Measurement) WHERE a.Title='" + anomaly_name +\
                "' RETURN DISTINCT m.Name, m.ParameterGroup"
    result_uwl = session.run(query_uwl)

    # Parse the result
    symptoms_list_uwl = []
    for item in result_uwl:
        measurement_name = item[0] + ' (' + item[1] + ')'
        symptoms_list_uwl.append(measurement_name)

    # Build and send the query to obtain the affected measurements that exceed the UWL
    query_lwl = "MATCH (a:Anomaly)-[r:Exceeds_LWL]-(m:Measurement) WHERE a.Title='" + anomaly_name + \
                "' RETURN DISTINCT m.Name, m.ParameterGroup"
    result_lwl = session.run(query_lwl)

    # Parse the result
    symptoms_list_lwl = []
    for item in result_lwl:
        measurement_name = item[0] + ' (' + item[1] + ')'
        symptoms_list_lwl.append(measurement_name)

    # Build the output (making the relationship explicit)
    symptoms_list = []
    for measurement in symptoms_list_lwl:
        symptom = {'measurement': measurement, 'relationship': 'Lower Warning Limit'}
        symptoms_list.append(symptom)
    for measurement in symptoms_list_uwl:
        symptom = {'measurement': measurement, 'relationship': 'Upper Warning Limit'}
        symptoms_list.append(symptom)

    return symptoms_list


def retrieve_thresholds_from_measurement(measurement_name, parameter_group):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (m:Measurement) WHERE m.Name='" + measurement_name + "' AND m.ParameterGroup='" + parameter_group +\
            "' RETURN DISTINCT m.LCL, m.LWL, m.UWL, m.UCL"
    result = session.run(query)

    # Parse the result
    parsed_result = ''
    for item in result:
        parsed_result = item

    # Check if the parsed result is empty and proceed accordingly
    if parsed_result != '':
        thresholds_dict = {'LCL': parsed_result[0], 'LWL': parsed_result[1],
                           'UWL': parsed_result[2], 'UCL': parsed_result[3]}
    else:
        thresholds_dict = {'LCL': 'None', 'LWL': 'None',
                           'UWL': 'None', 'UCL': 'None'}

    return thresholds_dict


def retrieve_units_from_measurement(measurement_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (m:Measurement) WHERE m.Name='" + measurement_name +\
            "' RETURN DISTINCT m.Unit"
    result = session.run(query)

    # Parse the result
    parsed_result = ''
    for item in result:
        parsed_result = item

    units = parsed_result[0]

    return units


def retrieve_ordered_steps_from_procedure(procedure_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (p:Procedure)-[:Has]-(st:Step) WHERE p.Title='" +\
            procedure_name + "' RETURN st.Action ORDER BY st.Title"
    result = session.run(query)

    # Parse the result
    steps_list = []
    for item in result:
        steps_list.append(item[0])

    return steps_list


def retrieve_fancy_steps_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build the queries
    query_step_labels = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
    query_step_actions = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'

    # Run the queries
    result_step_labels = session.run(query_step_labels)
    result_step_actions = session.run(query_step_actions)

    step_labels = []
    for item in result_step_labels:
        step_labels.append(item[0])

    step_actions = []
    for item in result_step_actions:
        step_actions.append(item[0])

    # Parse the result
    steps = []
    label_counter = {
        'steps': 0,
        'substeps': 0,
        'subsubsteps': 0
    }
    for index, step in enumerate(step_labels):
        # Retrieve the depth from the label points
        label_points = 0
        for char in step_labels[index]:
            if char == '.':
                label_points += 1
        depth = label_points

        # Decide whether the step should be initially enabled or not
        is_enabled = False
        if depth == 0:
            if label_counter['steps'] == 0:
                is_enabled = True
            label_counter['steps'] += 1
        if depth == 1:
            if label_counter['steps'] == 1 and label_counter['substeps'] == 0:
                is_enabled = True
            label_counter['substeps'] += 1
        if depth == 1:
            if label_counter['steps'] == 1 and label_counter['substeps'] == 1 and label_counter['subsubsteps'] == 0:
                is_enabled = True
            label_counter['subsubsteps'] += 1

        # Build the parsed item
        step_item = {'depth': depth,
                     'label': step_labels[index],
                     'action': step_actions[index],
                     'isDone': False,}

        steps.append(step_item)

    return steps

