# Neo4j testing script
from neo4j import GraphDatabase, basic_auth

driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
session = driver.session()

# Query and print all procedure numbers
query = "MATCH (p:Procedure) RETURN p.pNumber"
result = session.run(query)
for node in result:
    print(node[0])

# Query and print a specific procedure
query = "MATCH (p:Procedure) WHERE p.pNumber=117 RETURN p.Title"
result = session.run(query)
for node in result:
    print(node[0])

# Query and print all measurement names
query = "MATCH (m:Measurement) RETURN m.Name"
result = session.run(query)
for node in result:
    print(node[0])

# Query and print the anomalies associated with a measurement and relationship
query = "MATCH (a:Anomaly)-[:Exceeds_UWL]-(m:Measurement) WHERE m.Name='Pressure' RETURN a.Title"
result = session.run(query)
for node in result:
    print(node[0])

# Query steps for a procedure and append to a list
query = "match (p:Procedure)-[:Has]-(s:Step) where p.pNumber=117 return s.Action order by s.Step"
result = session.run(query)
steps = [node[0] for node in result]
print(steps)

# Diagnose anomaly RWGSR malfunction
'''
query =  MATCH (m1:Measurement)-[r1:Exceeds_LWL]->(g:Anomaly)
         MATCH (m2:Measurement)-[r2:Exceeds_UWL]->(g:Anomaly)
         MATCH (m3:Measurement)-[r3:Exceeds_UWL]->(g:Anomaly)
         WHERE m1.Name='ppO2' and m2.Name='ppCO2' and m3.Name='Water Level'
         RETURN DISTINCT g.Title
'''

print()

# Function that can take the intersection of multiple symptom queries
# Fabricate detection skill output (list of dictionaries)
symptom1, symptom2, symptom3 = {}, {}, {}
symptom1['measurement'], symptom1['relationship'] = 'ppO2', 'Exceeds_LWL'
symptom2['measurement'], symptom2['relationship'] = 'ppCO2', 'Exceeds_UWL'
symptom3['measurement'], symptom3['relationship'] = 'Water Level', 'Exceeds_UWL'
symptoms = [symptom1, symptom2, symptom3]

def diagnose_symptoms_neo4j(symptoms):
    # setup neo4j database connection
    driver = GraphDatabase.driver("bolt://13.58.54.49:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

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

print(diagnose_symptoms_neo4j(symptoms))
