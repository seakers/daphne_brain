from neo4j import GraphDatabase, basic_auth


def set_up_connection():
    # setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()
    return session


def diagnose_symptoms(symptoms):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # build the query based on the symptoms list
    query = ''
    for id, symp in enumerate(symptoms):
        query = query + 'MATCH (m' + str(id) + ':Measurement)-[r' + str(id) + ':' + symp['relationship'] + ']->(g:Anomaly) '
    query = query + 'WHERE '
    for id, symp in enumerate(symptoms):
        if (id + 1) < len(symptoms):
            query = query + 'm' + str(id) + '.Name=\'' + symp['measurement'] + '\' and '
        else:
            query = query + 'm' + str(id) + '.Name=\'' + symp['measurement'] + '\' RETURN DISTINCT g.Title'

    # query the database
    result = session.run(query)
    diagnosis = [node[0] for node in result]
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


def retrieve_procedures_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[:Solution]-(p:Procedure) WHERE a.Title='" + anomaly_name + "' RETURN DISTINCT p.Title"
    result = session.run(query)

    # Parse the result
    procedure_list = []
    for item in result:
        procedure_list.append(item[0])

    return procedure_list


def retrieve_risks_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[:Risk]-(r:Risk) WHERE a.Title='" + anomaly_name + "' RETURN DISTINCT r.Title"
    result = session.run(query)

    # Parse the result
    risks_list = []
    for item in result:
        risks_list.append(item[0])

    return risks_list


def retrieve_thresholds_from_measurement(measurement_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (m:Measurement) WHERE m.Name='" + measurement_name +\
            "' RETURN DISTINCT m.LCL, m.LWL, m.UWL, m.UCL"
    result = session.run(query)

    # Parse the result
    parsed_result = ''
    for item in result:
        parsed_result = item

    thresholds_dict = {'LCL': parsed_result[0], 'LWL': parsed_result[1],
                       'UWL': parsed_result[2], 'UCL': parsed_result[3]}

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
