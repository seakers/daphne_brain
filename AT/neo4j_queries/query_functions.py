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


def retrieve_procedures_from_anomaly(anomaly_name):
    # Setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    # Build and send the query
    query = "MATCH (a:Anomaly)-[:Solution]-(p:Procedure) WHERE a.Title='" + anomaly_name + "' RETURN p.Title"
    result = session.run(query)

    # Parse the result
    procedure_list = []
    for item in result:
        procedure_list.append(item[0])

    return procedure_list


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
