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

    # query the database
    result = session.run(query)
    diagnosis = [node[0] for node in result]
    return diagnosis

print(diagnose_symptoms_neo4j(symptoms, session))

# Function that can take an anomaly or list of anomalies (names) and query the related procedures
def get_related_procedures(anomaly, session):
    query = ''
    if type(anomaly) is list:
        query = query + 'MATCH (a:Anomaly)-[r:Solution]->(p:Procedure) WHERE '
        for id, anom in enumerate(anomaly):
            if ((id + 1) < len(anomaly)):
                query = query + 'a.Title=\'' + anom + '\' and '
            else:
                query = query + 'a.Title=\'' + anom + '\' RETURN DISTINCT p.Title'
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
print(get_related_procedures(['CDRA Failure', 'N2 Tank Burst'], session))

'''
# Function that can take a specific procedure and return all steps, substeps, and subsubsteps as an ordered list
def get_procedure_steps(procedure, detail=3, session):
    # detail denotes the level of steps to return. (1->steps, 2->steps&substeps, 3->steps&substeps&subsubsteps)
    return steps

# Function that returns the equipment required for a procedure or list of procedures
def get_procedure_equipment(procedure, session):
    return equipment
'''
