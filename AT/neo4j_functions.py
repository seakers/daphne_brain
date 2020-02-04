# Testing for neo4j query functions
from neo4j import GraphDatabase, basic_auth

# setup neo4j database connection
driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
session = driver.session()

# Function that can take the intersection of multiple symptom queries
# Fabricate detection skill output (list of dictionaries)
symptom1, symptom2, symptom3 = {}, {}, {}
symptom1['measurement'], symptom1['relationship'] = 'ppO2', 'Exceeds_LWL'
symptom2['measurement'], symptom2['relationship'] = 'ppCO2', 'Exceeds_UWL'
symptom3['measurement'], symptom3['relationship'] = 'Water Level', 'Exceeds_UWL'
symptoms = [symptom1, symptom2, symptom3]

def diagnose_symptoms_neo4j(symptoms, session):
    # build the query based on the symptoms list
    query = ''
    for id, symp in enumerate(symptoms):
        query = query + 'MATCH (m' + str(id) + ':Measurement)-[r' + str(id) + ':' + symp['relationship'] + ']->(g:Anomaly) '
    query = query + 'WHERE '
    for id, symp in enumerate(symptoms):
        if ((id + 1) < len(symptoms)):
            query = query + 'm' + str(id) + '.Name=\'' + symp['measurement'] + '\' and '
        else:
            query = query + 'm' + str(id) + '.Name=\'' + symp['measurement'] + '\' RETURN DISTINCT g.Title'

    print(query)
    # query the database
    result = session.run(query)
    diagnosis = [node[0] for node in result]
    return diagnosis

print(diagnose_symptoms_neo4j(symptoms, session))

# Function that can take an anomaly or list of anomalies (names) and query the related procedures
def get_related_procedures(anomaly, session):
    query = ''
    if type(anomaly) is list:
        for id, anom in enumerate(anomaly):
            query = query + 'MATCH (a' + str(id) + ':Anomaly)-[r' + str(id) + ':Solution]->(p:Procedure) '
        query = query + 'WHERE '
        for id, anom in enumerate(anomaly):
            if ((id + 1) < len(anomaly)):
                query = query + 'a' + str(id) + '.Title=\'' + anom + '\' and '
            else:
                query = query + 'a' + str(id) + '.Title=\'' + anom + '\' RETURN DISTINCT p.Title'
    else:
        query = query + 'MATCH (a:Anomaly)-[r:Solution]->(p:Procedure) WHERE a.Title=\'' + str(anomaly) + '\' RETURN DISTINCT p.Title'

    print(query)
    result = session.run(query)
    procedures = [node[0] for node in result]
    if not procedures:
        return None
    else:
        return procedures

print(get_related_procedures('CDRA Failure', session))
print(get_related_procedures(['CDRA Failure', 'Excess CO2 in Cabin'], session))

# Function that can take a specific procedure and return all steps, substeps, and subsubsteps as an ordered list
def get_procedure_steps(procedure, session, detail=3):
    # detail denotes the level of steps to return. (1->steps, 2->steps&substeps, 3->steps&substeps&subsubsteps)
    if (detail == 1):
        #Return only highest level steps
        query1 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' and (s:Step) RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' and (s:Step) RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
    elif (detail == 2):
        #Return Steps and substeps
        query1 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' and (s:Step OR s:SubStep) RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' and (s:Step OR s:SubStep) RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
    else:
        #Return all steps, substeps, and subsubsteps
        query1 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Title ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'
        query2 = 'MATCH(p:Procedure)-[r:Has]->(s) WHERE p.Title=\'' + procedure + '\' RETURN s.Action ORDER BY s.Step, s.SubStep, s.SubSubStep, s.Note'

    steps = []
    result1 = session.run(query1)
    step_titles = [node[0] for node in result1]
    result2 = session.run(query2)
    step_actions = [node[0] for node in result2]
    for id, step in enumerate(step_titles):
        steps.append(step_titles[id] + ' - ' + step_actions[id])

    if not steps:
        return None
    else:
        return steps

print(get_procedure_steps('Zeolite Filter Swapout', session, 3))


'''
# Function that returns the equipment required for a procedure or list of procedures
def get_procedure_equipment(procedure, session):
    return equipment
'''
