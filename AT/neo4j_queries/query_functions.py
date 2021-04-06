import itertools

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
        query = query + 'MATCH (m' + str(index) + ':Measurement)-[r' + str(index) + ':' + symp[
            'relationship'] + ']->(g:Anomaly) '
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
    # This function has several ugly patches and needs to be improved. This will probably require to do a deep refactor
    # of all the VA code.

    # Notation (needed to understand the function)
    #     Let A = {a1, a2, ..., aN} be the set of all anomalies.
    #     Let Sk = {sk1, sk2, ..., skM} be the set of symptoms of anomaly k (with 1<=k<=N).
    #     Let S = (Union of all Sk) = (s1, s2, ..., sM) be the set of all symptoms.
    #     Let X be a subset of S to be diagnosed (that is, the input of this function, X = "requested_symptoms").
    #     Let f be the diagnosis function. Then f is defined as:
    #           f: P(S) -> P(A), f(X) := {ak in A : (Sk intersection X) is nonempty}
    #     In other words, f return all the anomalies which have some of their symptoms in the symptoms to be diagnosed.
    #
    #     This code function computes f(requested_symptoms) and sorts the resulting list according to a certain score.
    #     Such score is defined as g(ak) = g1(ak) * g2(ak), where:
    #          g1(ak) = #(Sk intersection X) / #X
    #          g2(ak) = #(Sk intersection X) / #Sk
    #     Where #A is used to denote the cardinal of the set A.
    #

    # **************************************************
    # This first block of the function queries the neo4j graph. The result is f(X) (not sorted yet!)

    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build the query based on the symptoms list
    query = 'MATCH (m:Measurement)-[r]->(a:Anomaly) WHERE '
    for index, symptom in enumerate(requested_symptoms):
        measurement = symptom['measurement']
        clause = '(m.Name = "' + measurement + '")'
        if (index + 1) < len(requested_symptoms):
            clause = clause + ' OR '
        query = query + clause
    query = query + ' RETURN DISTINCT a.Title'

    # Query the database and parse the result (which is a list of the anomalies which symptoms have non empty
    # intersection with the requested symptoms)
    result = session.run(query)
    diagnosis = [node[0] for node in result]

    # **************************************************

    # **************************************************
    # This second section does some super ugly parsing that needs to be improved. The input of this function is a data
    # structure that looks as follows (disregarding all the previous notation):
    #     requested_symptoms = [symptDict1, symptDict2, ...., symptDictN]
    # Where:
    #     symptDictK = {measurement: 'Raw name of the measurement',
    #                   display_name: 'Raw name of the measurement + parameter group',
    #                   relationship: 'Threshold signature (as 'Exceeds_UWL')'}                      (*1)
    #
    # The output of the query in the first block, on the other hand, looks as follows:
    #     diagnosis = [anomaly1, anomaly2, ...., anomalyN]
    #
    # For each anomaly in the previous list, the set of its symptoms is retrieved (using another function within
    # this same script. The result looks as follows:
    #     symptoms_of_anomaly = {measurement: 'Raw name of the measurement + parameter group',
    #                            relationship: 'Threshold signature (as 'Upper Warning Limit')'}     (*2)
    #
    # To compute the desired intersections we will need to compare items like (*1) with items like (*2), and hence the
    # need to do some ugly parsing. Both types of items will be "translated" to the following common ground:
    #     symptCommonDict = {measurement: 'Raw name of the measurement + parameter group',
    #                        relationship: 'Threshold signature (as 'Exceeds_UWL')'}                 (*3)

    # The input is parsed from (*1) to (*3) ('measurement' field is substituted by 'display name' value, 'display_name'
    # field is stripped and 'relationship' field is left equal).
    parsed_input_symptoms = []
    for symptom in requested_symptoms:
        parsed_input_symptoms.append({'measurement': symptom['display_name'], 'relationship': symptom['relationship']})

    # For each anomaly of the diagnosis output, an object like (*2) is obtained and converted to (*3). The only parsing
    # needed is to convert the relationship format.
    symptoms_of_each_anomaly = {}
    for anomaly in diagnosis:
        # Retrieve symptoms of anomaly
        anomaly_symptoms = retrieve_symptoms_from_anomaly(anomaly)
        symptom_of_anomaly = []

        # For each symptom of the anomaly, parse the relationship field
        for symptom in anomaly_symptoms:
            relationship = symptom['relationship']
            if relationship == "Upper Warning Limit" or relationship == "Upper Critic Limit":
                relationship = 'Exceeds_UpperCautionLimit'
            else:
                relationship = 'Exceeds_LowerCautionLimit'
            symptom['relationship'] = relationship
            symptom_of_anomaly.append(symptom)

        # Append the resulting object to the dictionary
        symptoms_of_each_anomaly[anomaly] = symptom_of_anomaly

    # **************************************************

    # **************************************************
    # In this third part of the code, the cardinal of the said intersections is computed. Also, the amount of symptoms
    # of each anomaly is retrieved.

    # Let A and B be sets. A is looped. For each element in a, B is looped. For each element b in B, a and b are
    # compared, and the cardinal is increased if equal. This could  be done more efficiently, but the already poor
    # readability of this function would be completely obliterated.
    # A -> requested_symptoms
    # B -> anomaly_symptoms

    # Define auxiliary function to compare the symptom dictionaries
    def compare(anomaly_symptom, parsed_input_symptom):
        measurements_are_equal = (anomaly_symptom['measurement'] == parsed_input_symptom['measurement'])
        relationships_are_equal = (anomaly_symptom['relationship'] == parsed_input_symptom['relationship'])
        if measurements_are_equal and relationships_are_equal:
            return True
        else:
            return False

    # Initialize result storing variables
    cardinality_for_each_anomaly = {}
    size_of_each_anomaly = {}

    # Loop over the anomalies
    for anomaly in diagnosis:
        # Initialize the cardinal counter
        cardinal = 0
        # Loop over A
        for anomaly_symptom in symptoms_of_each_anomaly[anomaly]:
            # Loop over B
            for parsed_input_symptom in parsed_input_symptoms:
                # Compare
                are_equal = compare(anomaly_symptom, parsed_input_symptom)
                if are_equal:
                    cardinal += 1

        # Store the results
        cardinality_for_each_anomaly[anomaly] = cardinal
        size_of_each_anomaly[anomaly] = len(symptoms_of_each_anomaly[anomaly])

    # **************************************************

    # **************************************************
    # In this fourth part of the code, the score of each anomaly is computed and the final ordered list of anomalies is
    # built.

    # Create the result storing variable and parse the size of the requested symptoms set
    scored_diagnosis = {}
    total_requested_symptoms = len(requested_symptoms)

    # Loop over the anomalies, compute each of the partial scores and the total scores (g1, g2 and g)
    for anomaly in diagnosis:
        # Compute the score
        g1 = cardinality_for_each_anomaly[anomaly] / total_requested_symptoms
        g2 = cardinality_for_each_anomaly[anomaly] / size_of_each_anomaly[anomaly]
        g = g1 * g2
        # Round it for the frontend display
        score = round(g, 2)
        # Save it
        scored_diagnosis[anomaly] = score

    # Sort the result according to the scores
    ordered_diagnosis = {k: v for k, v in sorted(scored_diagnosis.items(), key=lambda item1: item1[1])}

    # Convert the dictionary to a list of its keys
    ordered_diagnosis = list(ordered_diagnosis.keys())
    ordered_diagnosis.reverse()

    # Cast list to top 7 items
    top_n_diagnosis = []
    size_limit = min(7, len(ordered_diagnosis))
    for i in range(0, size_limit):
        anomaly = ordered_diagnosis[i]
        score = scored_diagnosis[anomaly]
        text_score = ""
        if score < 0.33:
            text_score = "Least likely"
        elif score < 0.66:
            text_score = "Somewhat likely"
        else:
            text_score = "Very likely"

        top_n_diagnosis.append({'name': anomaly, 'score': score, 'text_score': text_score})

    # Return result
    final_diagnosis = top_n_diagnosis

    return final_diagnosis


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


def retrieve_procedures_fTitle_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[s:Solution]-(p:Procedure) WHERE a.Title='" + anomaly_name + "' RETURN p.fTitle ORDER BY s.Order"
    result = session.run(query)

    # Parse the result
    procedure_list = []
    for item in result:
        procedure_list.append(item[0])

    return procedure_list


def retrieve_procedures_title_from_anomaly(anomaly_name):
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

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[:Comprises]-(c:Component) WHERE p.pNumber='" + procedure + "' RETURN DISTINCT " \
                                                                                                 "c.Title "
    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[:Comprises]-(c:Component) WHERE p.fTitle='" + procedure + "' RETURN " \
                                                                                                    "DISTINCT " \
                                                                                                    "c.Title "

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[:Comprises]-(c:Component) WHERE p.Title='" + procedure + "' RETURN " \
                                                                                                   "DISTINCT " \
                                                                                                   "c.Title "
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

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure) WHERE p.pNumber='" + procedure + "' RETURN DISTINCT p.ETR"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure) WHERE p.fTitle='" + procedure + "' RETURN DISTINCT p.ETR"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure) WHERE p.Title='" + procedure + "' RETURN DISTINCT p.ETR"

    result = session.run(query)

    # Parse the result
    procedure_time_list = []
    for item in result:
        procedure_time_list.append(item[0])

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

    # Build and send the query to obtain the affected measurements that exceed the upper caution limit
    query_UpperCautionLimit = "MATCH (a:Anomaly)-[r:Exceeds_UpperCautionLimit]-(m:Measurement) WHERE a.Title='" + anomaly_name + \
                              "' RETURN DISTINCT m.Name, m.ParameterGroup"
    result_UpperCautionLimit = session.run(query_UpperCautionLimit)

    # Parse the result
    symptoms_list_UpperCautionLimit = []
    for item in result_UpperCautionLimit:
        measurement_name = item[0] + ' (' + item[1] + ')'
        symptoms_list_UpperCautionLimit.append(measurement_name)

    # Build and send the query to obtain the affected measurements that exceed the lower caution limit
    query_LowerCautionLimit = "MATCH (a:Anomaly)-[r:Exceeds_LowerCautionLimit]-(m:Measurement) WHERE a.Title='" + anomaly_name + \
                              "' RETURN DISTINCT m.Name, m.ParameterGroup"
    result_LowerCautionLimit = session.run(query_LowerCautionLimit)

    # Parse the result
    symptoms_list_LowerCautionLimit = []
    for item in result_LowerCautionLimit:
        measurement_name = item[0] + ' (' + item[1] + ')'
        symptoms_list_LowerCautionLimit.append(measurement_name)

    # Build the output (making the relationship explicit)
    symptoms_list = []
    for measurement in symptoms_list_LowerCautionLimit:
        symptom = {'measurement': measurement, 'relationship': 'Lower Caution Limit'}
        symptoms_list.append(symptom)
    for measurement in symptoms_list_UpperCautionLimit:
        symptom = {'measurement': measurement, 'relationship': 'Upper Warning Limit'}
        symptoms_list.append(symptom)

    return symptoms_list


def retrieve_thresholds_from_measurement(measurement_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (m:Measurement) WHERE m.Name='" + measurement_name + \
            "' RETURN m.ParameterGroup, m.LowerWarningLimit, m.LowerCautionLimit, m.UpperCautionLimit, " \
            "m.UpperWarningLimit "
    result = session.run(query)

    # Parse the result
    parsed_result = []
    for items in result:
        parsed_result.append(items)

    result_info = []
    # Check if the parsed result is empty and proceed accordingly
    if parsed_result:
        for item in parsed_result:
            thresholds_dict = {'ParameterGroup': item[0], 'LowerWarningLimit': item[1], 'LowerCautionLimit': item[2],
                               'UpperCautionLimit': item[3], 'UpperWarningLimit': item[4]}
            result_info.append(thresholds_dict)
    else:
        result_info = {'ParameterGroup': 'None', 'LowerWarningLimit': 'None', 'LowerCautionLimit': 'None',
                       'UpperCautionLimit': 'None', 'UpperWarningLimit': 'None'}

    return result_info


def retrieve_units_from_measurement(measurement_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (m:Measurement) WHERE m.Name='" + measurement_name + \
            "' RETURN DISTINCT m.Unit"
    result = session.run(query)

    # Parse the result
    parsed_result = ''
    for item in result:
        parsed_result = item

    units = parsed_result[0]

    return units


def retrieve_ordered_steps_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[:Has]-(st:Step) WHERE p.pNumber='" + \
                procedure + "' RETURN st.Action ORDER BY st.Title"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[:Has]-(st:Step) WHERE p.fTitle='" + \
                    procedure + "' RETURN st.Action ORDER BY st.Title"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[:Has]-(st:Step) WHERE p.Title='" + \
                    procedure + "' RETURN st.Action ORDER BY st.Title"

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

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query_step_labels = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query_step_actions = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query_step_figures = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.Link ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query_step_fNumbers = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.fNumber ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query_step_figures2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.Link2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query_step_fNumbers2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.pNumber=\'' + procedure + '\' RETURN s.fNumber2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query_step_labels = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_actions = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_figures = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.Link ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_fNumbers = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.fNumber ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_figures2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.Link2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_fNumbers2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.fTitle=\'' + procedure + '\' RETURN s.fNumber2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query_step_labels = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_actions = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_figures = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Link ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_fNumbers = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.fNumber ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_figures2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Link2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
            query_step_fNumbers2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.fNumber2 ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'

    # Run the queries
    result_step_labels = session.run(query_step_labels)
    result_step_actions = session.run(query_step_actions)
    result_step_figures = session.run(query_step_figures)
    result_step_fNumbers = session.run(query_step_fNumbers)
    result_step_figures2 = session.run(query_step_figures2)
    result_step_fNumbers2 = session.run(query_step_fNumbers2)

    step_labels = []
    for item in result_step_labels:
        step_labels.append(item[0])

    step_actions = []
    for item in result_step_actions:
        step_actions.append(item[0])

    step_figures = []
    for item in result_step_figures:
        step_figures.append(item[0])

    step_fNumbers = []
    step_hasFigure = []
    for item in result_step_fNumbers:
        step_fNumbers.append(item[0])
        if (item[0]) is not None:
            step_hasFigure.append(True)
        else:
            step_hasFigure.append(False)

    step_figures2 = []
    for item in result_step_figures2:
        step_figures2.append(item[0])

    step_fNumbers2 = []
    step_hasFigure2 = []
    for item in result_step_fNumbers2:
        step_fNumbers2.append(item[0])
        if (item[0]) is not None:
            step_hasFigure2.append(True)
        else:
            step_hasFigure2.append(False)

    # Parse the result
    steps = []
    label_counter = {
        'steps': 0,
        'substeps': 0,
        'subsubsteps': 0
    }
    for index, step in enumerate(step_labels):
        isStep = True
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
            isStep = False
        if depth == 2:
            if label_counter['steps'] == 1 and label_counter['substeps'] == 1 and label_counter['subsubsteps'] == 0:
                is_enabled = True
            label_counter['subsubsteps'] += 1
            isStep = False

        # Build the parsed item
        step_item = {'depth': depth,
                     'label': step_labels[index],
                     'action': step_actions[index],
                     'figure': step_figures[index],
                     'fNumber': step_fNumbers[index],
                     'hasFigure': step_hasFigure[index],
                     'figure2': step_figures2[index],
                     'fNumber2': step_fNumbers2[index],
                     'hasFigure2': step_hasFigure2[index],
                     'isDone': False,
                     'isStep': isStep}

        steps.append(step_item)

    return steps


def retrieve_objective_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure) WHERE p.pNumber='" + procedure + "' RETURN p.Objective"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure) WHERE p.fTitle='" + procedure + "' RETURN p.Objective"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure) WHERE p.Title='" + procedure + "' RETURN p.Objective"

    result = session.run(query)

    # Parse the result
    objective_list = []
    for item in result:
        objective_list.append(item[0])

    if len(objective_list) == 0:
        objective = 'ERROR: missing objective description.'
    else:
        objective = objective_list[0]

    return objective


def retrieve_equipment_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[Uses]->(e:Equipment) WHERE p.pNumber='" + procedure + "' RETURN e.Title"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[Uses]->(e:Equipment) WHERE p.fTitle='" + procedure + "' RETURN e.Title"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[Uses]->(e:Equipment) WHERE p.Title='" + procedure + "' RETURN e.Title"

    result = session.run(query)

    # Parse the result
    equipment_list = []
    for item in result:
        equipment_list.append(item[0])

    if len(equipment_list) == 0:
        equipment = ['ERROR: missing equipment list.']
    else:
        equipment = equipment_list

    return equipment


def retrieve_references_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.pNumber='" + procedure + "' RETURN r.Title"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.fTitle='" + procedure + "' RETURN r.Title"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.Title='" + procedure + "' RETURN r.Title"

    result = session.run(query)

    # Parse the result
    reference_list = []
    for item in result:
        reference_list.append(item[0])

    return reference_list


def retrieve_reference_links_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.pNumber='" + procedure + "' RETURN r.Procedure"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.fTitle='" + procedure + "' RETURN r.Procedure"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[:Uses]->(r:Reference) WHERE p.Title='" + procedure + "' RETURN r.Procedure"

    result = session.run(query)

    # Parse the result
    reference_list = []
    for item in result:
        reference_list.append(item[0])

    return reference_list


def retrieve_figures_from_procedure(procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH(p:Procedure)-[r:Has]->(f:Figure) WHERE p.pNumber=\'" + procedure + \
                "\'RETURN f.Link ORDER BY f.Number"

    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH(p:Procedure)-[r:Has]->(f:Figure) WHERE p.fTitle=\'" + procedure + \
                    "\'RETURN f.Link ORDER BY f.Number"

        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH(p:Procedure)-[r:Has]->(f:Figure) WHERE p.Title=\'" + procedure + \
                    "\'RETURN f.Link ORDER BY f.Number"

    result = session.run(query)

    # Parse the result
    figure_list = []
    for item in result:
        figure_list.append(item[0])

    return figure_list


def retrieve_all_components():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query1 = 'MATCH (n) WHERE EXISTS(n.Link) RETURN DISTINCT n.Link AS Link UNION ALL MATCH ()-[r]-() WHERE ' \
             'EXISTS(r.Link) RETURN DISTINCT r.Link AS Link '
    query2 = 'MATCH (n) WHERE EXISTS(n.Link2) RETURN DISTINCT n.Link2 AS Link2 UNION ALL MATCH ()-[r]-() WHERE ' \
             'EXISTS(r.Link2) RETURN DISTINCT r.Link2 AS Link2 '
    result1 = session.run(query1)
    result2 = session.run(query2)

    components_list = []
    for items in itertools.chain(result1, result2):
        for item in items:
            components_list.append(item)

    return components_list


def retrieve_all_procedure_numbers():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (p:Procedure) RETURN DISTINCT p.pNumber"
    result = session.run(query)

    # Parse the result
    procedure_numbers = []
    for item in result:
        procedure_numbers.append(item[0])

    return procedure_numbers


def retrieve_all_step_numbers():
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = 'MATCH (n) WHERE EXISTS(n.SubStep) RETURN DISTINCT n.Title AS Title UNION ALL MATCH (m) WHERE ' \
            'EXISTS(m.SubSubStep) RETURN DISTINCT m.Title AS Title'
    result = session.run(query)

    # Parse the result
    step_numbers = []
    for item in result:
        step_numbers.append(item[0])

    return step_numbers


#
# def retrieve_procedures_numbers_from_names(procedure_name):
#     # Setup neo4j database connection
#     driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
#     session = driver.session()
#
#     # Build and send the query
#     query = "MATCH (p:Procedure) WHERE p.Title='" + procedure_name + "' RETURN p.pNumber"
#     result = session.run(query)
#
#     # Parse the result
#     procedure_number = []
#     for item in result:
#         procedure_number.append(item[0])
#
#     return procedure_number[0]
#
#
# def retrieve_procedures_from_pNumber(pNumber):
#     # Setup neo4j database connection
#     driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
#     session = driver.session()
#
#     # Build and send the query
#     query = "MATCH (p:Procedure) WHERE p.pNumber='" + pNumber + "' RETURN p.Title"
#     result = session.run(query)
#
#     # Parse the result
#     procedure = []
#     for item in result:
#         procedure.append(item[0])
#
#     return procedure
#
#
# def retrieve_step_from_procedure(step_number, procedure_number):
#     # Setup neo4j database connection
#     driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
#     session = driver.session()
#
#     # Build and send the query
#     query = "MATCH (p:Procedure)-[:Has]->(s) WHERE p.pNumber='" + procedure_number + \
#             "' AND s.Title='" + step_number + "' RETURN s.Action"
#     result = session.run(query)
#
#     # Parse the result
#     step = []
#     for item in result:
#         step.append(item[0])
#
#     return step


def retrieve_step_from_procedure(step_number, procedure):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    try:
        float(procedure)
        # Build and send the query because procedure is a number
        query = "MATCH (p:Procedure)-[:Has]->(s) WHERE p.pNumber='" + procedure + \
                "' AND s.Title='" + step_number + "' RETURN s.Action"
    except ValueError:
        print("Not a number.")

        # check if it is full title by checking if it starts with a number
        try:
            float(procedure[0])
            # Build and send the query because procedure is a full title
            query = "MATCH (p:Procedure)-[:Has]->(s) WHERE p.fTitle='" + procedure + \
                    "' AND s.Title='" + step_number + "' RETURN s.Action"
        except ValueError:
            print("Not a full title.")
            # Build and send the query because procedure is just a name
            query = "MATCH (p:Procedure)-[:Has]->(s) WHERE p.Title='" + procedure + \
                    "' AND s.Title='" + step_number + "' RETURN s.Action"

    result = session.run(query)

    # Parse the result
    step = []
    for item in result:
        step.append(item[0])

    return step
