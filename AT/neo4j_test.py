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
