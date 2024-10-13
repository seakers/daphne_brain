import datetime
import json
import re
import sys
from collections import OrderedDict
import urllib.parse
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response

from daphne_brain.nlp_object import nlp
from dialogue.nn_models import nn_models
import dialogue.command_processing as command_processing
from auth_API.helpers import get_or_create_user_information
from daphne_context.models import DialogueHistory, DialogueContext
from experiment.models import AllowedCommand

# Begin of langchain
from dotenv import load_dotenv
import openai
import langchain
import os
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import AT.simulator_thread.simulator_routine_by_real_eclss as sim

from langchain.agents import create_json_agent
from langchain.agents.agent_toolkits import JsonToolkit
from langchain.tools.json.tool import JsonSpec


# from django.http import HttpResponse
# from django.http import FileResponse, Http404
# end of langchain changes

class Command(APIView):
    """
    Process a command
    """
    daphne_version = ""
    command_options = []
    condition_names = []
    # def __init__(self):
    # Initialize session_state dictionary in the constructor
    session_state = {}
    # Generated natural language
    if 'generated' not in session_state:
        print("helooooooooo3")
        session_state['generated'] = []
    # Neo4j database results
    if 'database_results' not in session_state:
        print("helooooooooo4")
        session_state['database_results'] = []
    # User input
    if 'user_input' not in session_state:
        print("helooooooooo5")
        session_state['user_input'] = []
    # Generated Cypher statements
    if 'cypher' not in session_state:
        print("helooooooooo6")
        session_state['cypher'] = []

    def generate_context(self, prompt, context_data='generated'):

        print("helooooooooo")
        context = []

        print("helooooooooo1")
        # print(self.session_state['generated'])
        # If any history exists
        if self.session_state['generated']:
            print("helooooooooo2")
            # Add the last three exchanges
            size = len(self.session_state['generated'])
            for i in range(max(size - 5, 0), size):
                context.append(
                    {'role': 'user', 'content': self.session_state['user_input'][i]})
                context.append(
                    {'role': 'assistant', 'content': self.session_state[context_data][i]})
        # print(context)
        # Add the latest user prompt
        context.append({'role': 'user', 'content': str(prompt)})
        return context

    def run_cypher_query(self, graph, query):
        results = graph.query(query)
        return results

    def post(self, request, format=None):
        # Example usage
        try:
            # JSON changes
            load_dotenv()
            api_key = os.environ['OPENAI_API_KEY'] = os.getenv('api_key')

            intent_classification_template = """
                                                You are an AI assistant. Your job is to classify the following question as either a 'parameter query', 'knowledge graph query', 'image request', 'storage query', or a general question.
                                                Answer only with 'parameter query', 'knowledge graph query', 'image request', 'storage query' or 'general query'.
                                                Below are some examples:

                                                # PARAMETER QUERY Questions
                                                Question: Show the current value of measurement temperature.
                                                Question: Show the value of the temperature measurement.
                                                Question: Show the value of X.
                                                Question: Provide the current value of measurement X.
                                                Question: Provide the value of the X measurement.
                                                Question: Provide the value of X.
                                                Question: What is the current value of measurement X?
                                                Question: What is the value of the X measurement?
                                                Question: What is the value of X?
                                                Question: X measurement current value.
                                                Question: X measurement value.
                                                Question: X value.
                                                Question: Is measurement X normal?.
                                                Question: Is measurement X nominal?.
                                                Question: Is measurement X correct?.
                                                Question: Is X normal?.
                                                Question: Is X nominal?.
                                                Question: Is X correct?.
                                                Question: Check the X status.
                                                Question: Check measurement X status.
                                                Question: Check X status.
                                                Question: The status of which of them in nominal
                                                Question: The status of which of them is not nominal
                                                Question: Which have a status not nominal
                                                Answer: parameter query

                                                # KNOWLEDGE GRAPH QUERY Questions
                                                Question: Next
                                                Question: next
                                                Question: Previous
                                                Question: previous
                                                Question: Show the thresholds of measurement X.
                                                Question: Show the X thresholds.
                                                Question: Provide the X limits.
                                                Question: Provide the thresholds of measurement X.
                                                Question: Provide the X measurement limits.
                                                Question: What are the measurement X thresholds?
                                                Question: What are the X thresholds?
                                                Question: X thresholds.
                                                Question: X limits.
                                                Question: What are the risks of anomaly X?
                                                Question: What are the potential risks of anomaly X?
                                                Question: Give me the pdf for procedure 3.104
                                                Question: what is the difference in symptoms between cdra failure and main cabin fan failure
                                                Question: what are the symptoms of cdra failure and main cabin fan failure
                                                Question: difference in symptoms between cdra failure and main cabin fan failure
                                                Question: compare symptoms between cdra failure and main cabin fan failure
                                                Question: What are the risks of X?
                                                Question: What are the risks of main cabin fan failure?
                                                Question: Risks of main cabin fan failure?
                                                Question: What are the potential risks of X?
                                                Question: What are the hazards of anomaly X?
                                                Question: What are the potential hazards of anomaly X?
                                                Question: What are the hazards of X?
                                                Question: What are the potential hazards of X?
                                                Question: Why is anomaly X dangerous?
                                                Question: Why is X dangerous?
                                                Question: Why is anomaly X hazardous?
                                                Question: Why is X hazardous?
                                                Question: What is the signature of anomaly X?
                                                Question: What is the signature of X?
                                                Question: What parameters does anomaly X affect?
                                                Question: What parameters does X affect?
                                                Question: What are the measurements affected by anomaly X?
                                                Question: What are the measurements affected by X?
                                                Question: What are the symptoms of anomaly X?
                                                Question: What are the symptoms of X?
                                                Question: Anomaly X signature.
                                                Question: Anomaly X symptoms.
                                                Question: X signature.
                                                Question: X symptoms.
                                                Question: What subsystems does anomaly X affect?
                                                Question: What subsystems does X affect?
                                                Question: What components does anomaly X affect?
                                                Question: What components does X affect?
                                                Question: What are the components affected by anomaly X?
                                                Question: What are the components affected by X?
                                                Question: Anomaly X subsystems.
                                                Question: Anomaly X components.
                                                Question: X subsystems.
                                                Question: X components.
                                                Question: What are the procedures for anomaly X?
                                                Question: What is the procedure for X?
                                                Question: Are there any procedures for anomaly X?
                                                Question: Are there any procedures for X?
                                                Question: Provide anomaly X procedures.
                                                Question: Show me the procedure to solve X.
                                                Question: Procedure X.
                                                Question: Anomaly X procedure.
                                                Question: Give me the procedure for X.
                                                Question: Next
                                                Question: provide the pdf for procedure 3.104
                                                Question: give me the pdf for CDRA Zeolite Filter Swapout
                                                Question: give the pdf for procedure
                                                Question: Will procedure X impact other components?
                                                Question: Which components will procedure X impact?
                                                Question: Show the affected components by procedure X.
                                                Question: How much time will it take to apply procedure X?
                                                Question: What is the estimated time of completion for procedure X?
                                                Question: How long will it take to do X.
                                                Question: How long is procedure X?
                                                Question: Provide procedure X.
                                                Question: Show me procedure X.
                                                Question: Provide X pdf.
                                                Question: Show me X pdf.
                                                Question: Display pdf for X.
                                                Question: What anomaly would cause high ppCO2 and low ppO2?
                                                Question: High ppCO2 and low ppO2 would be the symptoms of what anomaly?
                                                Answer: knowledge graph query

                                                # IMAGE REPONSE Questions
                                                Question: Show me the image of X.
                                                Question: Provide me the image for X.
                                                Question: Give the image of X.
                                                Question: Show me the picture of X.
                                                Question: Provide me the picture for X.
                                                Question: Give the picture of X.
                                                Question: Show me the image of component X.
                                                Question: Provide me the image for component X.
                                                Question: Give the image of component X.
                                                Question: Show me the picture of component X.
                                                Question: Provide me the picture for component X.
                                                Question: Give the picture of component X.
                                                Question: Show me the visual of component X.
                                                Question: Display an image of component X.
                                                Question: Retrieve the picture of component X.
                                                Question: Can you bring up the visual for component X?
                                                Question: Can you provide a visual of X?
                                                Question: I'd like to see the image of X.
                                                Question: Can you give me a look at X's picture?
                                                Answer: image request

                                                # STORAGE QUERY Questions
                                                Question: Where is the X?
                                                Question: Where is X stored?
                                                Question: Can you tell me the location of X?
                                                Question: Where can i find X?
                                                Question: Where is X kept?
                                                Question: Where can i locate X?
                                                Question: Where is X located?
                                                Question: Can you find the location of X?
                                                Question: Where is the X?                              
                                                Answer: storage query

                                                All other questions are classified as 'general query'. 
                                                Now, classify the following question:
                                                Question: {question}
                                                Answer:
                                                """
            images_list = ['532_T_Handle_Allen_Ranch', 'Allen_Wrench', 'Anemometer', 'Auxiliary_Cabin_Fan_Power',
                           'Auxiliary_Cabin_Fan_Tug_Connectors', 'Auxiliary_Electrolysis_Module',
                           'Aux_Electrolysis_Can_Within_Aux_Electrolysis_Module', 'Black_Box_Side_Cover',
                           'Bottom_Retaining_Hex_Bolts', 'Cabin_Fan_Power_Switches_1', 'Cabin_Fan_Power_Switches_2',
                           'Cabin_Output_Vent_CD', 'Cabin_Output_Vent_CD_And_Cabin_Output_Vent_DE',
                           'Cabin_Output_Vent_DE', 'Carbon_Dioxide_Removal_Assembly', 'CDRA', 'Circuit', 'Circuit1',
                           'Circuit2', 'Circuit3', 'Circuit_Board1', 'Circuit_Breaker_Panel', 'Combined_CBC_CP',
                           'Compartment', 'Compartment_circle', 'control_cables', 'Control_Panel',
                           'Control_Panel_Cable', 'Coolant_Pump_Module', 'Coolant_Pump_Syringe_Kit', 'Coolant_Valve',
                           'Distillation_Gas_Vent_Valve', 'ECM_Unit', 'Elbow_Joint', 'Emergency_O2_Generation_System',
                           'Emergency_O2_System_Inside', 'Fan', 'Fan_Dampener_Assembly_Pump', 'Filter_Screen',
                           'Filter_Sleeve_And_Rechargeable_Trap_Filter', 'Final_Floor_Configuration', 'Floor_Panel',
                           'Floor_Panel_Closed', 'Fuel_Cell_Control_Panel', 'Fuel_Cell_Operate_Light',
                           'Fuel_Cell_Standby_Light', 'Fuel_Cell_Temperature_Sensor', 'H2O_O2_Separator_Module',
                           'handles', 'HSS_Main_Cabin_Fan_Power', 'HSS_Parameter_Display', 'Injector_Active_Light',
                           'Injector_Armed_Light', 'Injector_Line_Heater_Switch', 'Injector_Panel',
                           'Inside_Of_TCCS_With_Charcoal_Filter', 'Installed_Biological_Filter', 'Installed_RWGSR_1',
                           'Installed_RWGSR_2', 'L1A_Subfloor_Removed', 'LiOH_Canister_Assembly', 'LiOH_Cannister',
                           'LiOH_Cannister_Assembly', 'loader', 'Main_Cabin_Fan_Power', 'Main_Pump_Power_Switch',
                           'Mechanical_Worktable', 'Metal_Cover_Off', 'Microbial_Filter', 'Moxie_Kit',
                           'N2_Ballast_Tank_Alarm_Switch', 'N2_Ballast_Tank_Line_Valve', 'PDU_display', 'Power_Cable',
                           'Power_Connector', 'Rechargeable_Trap_Filter_Cover', 'Rechargeable_Trap_Lever', 'Reconnect',
                           'Removing_Ballast_Tank_Brackets', 'Removing_N2_Ballast_Tank_Line',
                           'Replacement_Cover_Slide_In', 'Replacement_Fan', 'Replacement_Fan_Slide_In', 'RF',
                           'RF_Arrow', 'RF_Board', 'RF_Board_I', 'Rubber_Gasket', 'Sabatier_Panel',
                           'Side_View_Of_Electrolysis_Canister_Top', 'Solid_Polymer_Electrolysis_System',
                           'SPE_Syringe_And_Filler_Hose', 'Syringe', 'TCCS_Panel', 'Top_Retaining_Hex_Bolts',
                           'Uncovered_RF', 'Zeolite_Cannister_Rack', 'Zeolite_Filter_Assembly', 'ZRU',
                           'ZRU_Connected_To_Sabatier', 'ZRU_Power_Switch']

            graph = Neo4jGraph(
                url="bolt://13.58.54.49:7687",
                username="neo4j",
                password="goSEAKers!"
            )

            schema = graph.schema
            anomaly_name = self.run_cypher_query(graph, "MATCH (n:Anomaly) RETURN n.Name")
            measurement_name = self.run_cypher_query(graph, "MATCH (n:Measurement) RETURN n.Name")
            procedure_name = self.run_cypher_query(graph, "MATCH (n:Procedure) RETURN n.Title")

            cypher_template = f"""Task:Generate Cypher statement to query a graph database.

                                                               Instructions:
                                                               You are a virtual assistant designed to assist astronauts in resolving spacecraft anomalies when mission control is unavailable. Astronauts will ask you questions regarding anomalies, their causes, signatures, procedures for fixing them, related risks, etc. To answer these questions, generate appropriate Cypher statements to query a graph database.

                                                               Here is the Schema for the graph database:
                                                               {schema}

                                                               Here are the anomaly names - {anomaly_name}
                                                               Here are the procedure names - {procedure_name}
                                                               Here are the measurement names - {measurement_name}

                                                               Use only the provided relationship types and properties in the schema.
                                                               Do not use any other relationship types or properties that are not provided.
                                                               If a query returns no results, output "No information available." If there are multiple possible answers, list all. Your response should include only the query results, without explanations or framing sentences.

                                                               Cypher examples:
                                                               # Risks of main cabin fan failure include what?
                                                               MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
                                                               WITH apoc.text.sorensenDiceSimilarity(a.Name,'main cabin fan failure') AS similarity, risk
                                                               WHERE similarity > 0.85
                                                               Return
                                                               CASE WHEN risk IS NULL
                                                                 THEN 'No risks found'
                                                                 ELSE risk.Title
                                                                 END

                                                               # What are the potential risks of nitrogen tank leak
                                                               MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'N2 Ballast Tank Line Leak') AS similarity, risk
                                                               WHERE similarity > 0.85
                                                               Return
                                                               CASE WHEN risk IS NULL
                                                                 THEN 'No risks found'
                                                                 ELSE risk.Title
                                                                 END

                                                               # What are the potential risks of a nitrogen tank burst and a nitrogen tank line leak.
                                                               MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
                                                               WHERE anomaly.Name IN ['N2 Tank Burst', 'N2 Ballast Tank Line Leak']
                                                               RETURN risk.Title
                                                               Instructions : give answers from return value

                                                               # What are the potential risks of a reduced cabin fan capacity. Don't give answers from the web
                                                               # What are the potential risks of a reduced cabin fan capacity. Don't give answers from the web
                                                               MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Reduced Main Cabin Fan #1 Capacity') AS similarity, risk
                                                               WHERE similarity > 0.85
                                                               RETURN
                                                                 CASE WHEN risk IS NULL
                                                                 THEN 'No risks found'
                                                                 ELSE risk.Title
                                                                 END
                                                               Instructions :  Don't give answers from the web

                                                               # what are the potential risks of trace contaminants. Don't give answers from the web
                                                               # what are the risks of trace contaminants. Don't give answers from the web
                                                               # What are the potential risks of trace contaminants. Don't give answers from the web
                                                               MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Trace Contaminants') AS similarity, risk
                                                               WHERE similarity > 0.85
                                                               RETURN
                                                                 CASE WHEN risk IS NULL
                                                                 THEN 'No risks found'
                                                                 ELSE risk.Title
                                                                 END

                                                               # what is the signature of CDRA Failure. Mention all m.Name, m.ParameterGroup, r
                                                               # what is the signature associated with cdra failure. Mention all m.Name, m.ParameterGroup, r
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement, relationship
                                                               WHERE similarity > 0.85
                                                               RETURN measurement.Name, measurement.ParameterGroup, relationship
                                                               # Note: Give answers from query results

                                                               # what are the symptoms of cdra failure. Mention all m.Name, m.ParameterGroup, r
                                                               # if cdra failure was occurring what symptoms would I expect to see. Give answer from the query result
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement, relationship
                                                               WHERE similarity > 0.85
                                                               RETURN measurement.Name, measurement.ParameterGroup, relationship

                                                               # what measurements are affected by main cabin fan failure
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Main Cabin Fan Failure') AS similarity, measurement, relationship
                                                               WHERE similarity > 0.85
                                                               RETURN measurement.Name, measurement.ParameterGroup, relationship

                                                               # Note: Give answers from query results

                                                               # what are the characteristic symptoms of cdra lioh filter clogged. Mention all m.Name, m.ParameterGroup, r
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,cdra lioh filter clogged') AS similarity, measurement, relationship
                                                               WHERE similarity > 0.85
                                                               RETURN measurement.Name, measurement.ParameterGroup, relationship

                                                               # what can low ppN2 cause
                                                               # what anomalies would result in low ppN2
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit  | Exceeds_LowerWarningLimit]->(anomaly:Anomaly) WITH apoc.text.sorensenDiceSimilarity(measurement.Name,'ppN2') AS similarity, anomaly,measurement, relationship WHERE similarity > 0.85 RETURN anomaly.Name, measurement.Name, measurement.ParameterGroup, relationship

                                                               # what can high ppCO2 cause
                                                               # what anomalies would result in high ppCO2
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly) WITH apoc.text.sorensenDiceSimilarity(measurement.Name,'ppCO2') AS similarity, anomaly,measurement, relationship WHERE similarity > 0.85 RETURN anomaly.Name, measurement.Name, measurement.ParameterGroup, relationship

                                                               # what anomaly would cause high ppCO2 and low ppO2
                                                               # High ppCO2 and low ppO2 would be the symptoms of what anomaly
                                                               # what could cause high ppCO2 and low ppO2
                                                               MATCH (measurement:Measurement)-[relationship:Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly) WITH apoc.text.sorensenDiceSimilarity(measurement.Name,'ppCO2') AS similarity, anomaly, measurement, relationship WHERE similarity > 0.85 MATCH (measurement2:Measurement)-[relationship2:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit]->(anomaly2:Anomaly) WITH apoc.text.sorensenDiceSimilarity(measurement2.Name,'ppO2') AS similarity2, anomaly2, measurement2, relationship2, anomaly, relationship, measurement WHERE similarity2 > 0.85 AND anomaly.Name = anomaly2.Name RETURN anomaly.Name, measurement.Name, measurement.ParameterGroup, relationship, measurement2.Name, measurement2.ParameterGroup, relationship2

                                                               # Note: Give answers from query results

                                                               # what subsystems does biological filter saturation affect. Answer SubSystem's Title value
                                                               MATCH (anomaly:Anomaly)-[:Affects]->(subsystem:SubSystem)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, subsystem
                                                               WHERE similarity > 0.85
                                                               RETURN subsystem.Title
                                                               # Note: Answer subsystem.Title value

                                                               # how do i fix biological filter saturation. Mention the procedure titlte
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, procedure
                                                               WHERE similarity > 0.85
                                                               RETURN procedure.Title
                                                               # Note: Mention the procedure title

                                                               Note: Do not include any explanations or apologies in your responses.
                                                               Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
                                                               Do not include any text except the generated Cypher statement.
                                                               If multiple answers list all

                                                               # how long will it take me to solve biological filter saturation
                                                               # what is the average timeframe for resolving biological filter saturation
                                                               # how long will it take to biological filter saturation. Mention all times with correspnding procesdures, give the higher value first
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, procedure WHERE similarity > 0.85 RETURN procedure.ETR

                                                               # how long will it take to complete fuel cell #2 and pdu failure.
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Fuel Cell #2 and PDU Failure') AS similarity, procedure WHERE similarity > 0.85 RETURN procedure.Title, procedure.ETR

                                                               #Instructions: Mention all times in order with correspnding procesdures titles and number

                                                               # how long is 3.109
                                                               # time of completion 3.101
                                                               MATCH (procedure:Procedure)
                                                               WHERE procedure.pNumber = '3.109'
                                                               RETURN procedure.ETR

                                                               # how long would electrolysis system biological filter swap out take to complete
                                                               MATCH (procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(procedure.Title,'Electrolysis System Biological Filter Swapout') AS similarity, procedure
                                                               WHERE similarity > 0.85
                                                               RETURN procedure.ETR

                                                               # how long will it take to complete procedure system activation.
                                                               MATCH (procedure:Procedure) WITH apoc.text.sorensenDiceSimilarity(procedure.Title,'Electrolysis System Activation') AS similarity, procedure WHERE similarity > 0.85 RETURN procedure.Title, procedure.ETR

                                                               # read steps of procedure 3.109
                                                               MATCH (procedure:Procedure)-[:Has]->(step:Step)
                                                               WHERE procedure.pNumber = '3.109'
                                                               RETURN step.Title, step.Action

                                                               #read steps of procedure 4.303
                                                               MATCH (procedure:Procedure)-[:Has]->(step:Step) WHERE procedure.pNumber = '4.303' RETURN step.Title, step.Action

                                                               #read steps of procedure 2.101
                                                               MATCH (procedure:Procedure)-[:Has]->(step:Step) WHERE procedure.pNumber = '2.101' RETURN step.Title, step.Action

                                                               # how long will it take to solve wrs off nominal ph level.
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'WRS Off Nominal pH Level') AS similarity, procedure
                                                               WHERE similarity > 0.85
                                                               RETURN procedure.ETR, procedure.Title, procedure.pNumber

                                                               # What are the procedures for cdra failure
                                                               # Provide the link for cdra failure
                                                               # Provide the pdf for cdra failure
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, procedure
                                                               WHERE similarity > 0.85
                                                               RETURN procedure.Title, procedure.pNumber

                                                               # Give me the link for cdra failure
                                                               # Givde me the pdf for cdra failure
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, procedure
                                                               WHERE similarity > 0.85
                                                               RETURN procedure.Title, procedure.pNumber

                                                               # Provide the pdf for wrs off nominal ph level
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'WRS Off-nominal pH Level') AS similarity, procedure WHERE similarity > 0.85 RETURN procedure.Title, procedure.pNumber

                                                               Note: answer the question like -> The title of the procedure is "CDRA Zeolite Filter Swapout" and the procedure number is 3.104.

                                                               # provide the link for procedure 3.104
                                                               # provide the pdf for procedure 3.104
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WHERE procedure.pNumber = '3.104'
                                                               RETURN procedure.Title, procedure.pNumber

                                                               # How can I resolve a moxie ecm failure
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'MOXIE ECM Failure') AS similarity, procedure WHERE similarity > 0.85 RETURN procedure.Title, procedure.pNumber

                                                               # read steps for cdra zeolite filter swap out
                                                               MATCH (procedure:Procedure)-[:Has]->(step:Step)
                                                               WHERE procedure.Title = 'CDRA Zeolite Filter Swapout'

                                                               RETURN step.Title, step.Action

                                                               Note: always check all nodes connected through has relationship

                                                               # tell me the steps for tccs auxiliary fan swapout
                                                               MATCH (procedure:Procedure)-[:Has]->(step:Step)
                                                               WHERE procedure.Title = 'TCCS Auxiliary Fan Swapout'

                                                               RETURN step.Title, step.Action

                                                               # list all substeps of step 1 of procedure 3.106
                                                               MATCH (procedure:Procedure)-[:Has]->(ss)
                                                               WHERE procedure.pNumber = '3.106' AND ss.Step = 1
                                                               RETURN ss.Title, ss.Action
                                                               ORDER BY ss.SubStep

                                                               Note: always check all nodes connected through has relationship

                                                               # what is the procedure for Fuel Cell #1 and PDU Failure
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               Where anomaly.Name='Fuel Cell #1 and PDU Failure'
                                                               RETURN procedure.Title, procedure.pNumber

                                                               Note: use the name of the node type as the variable for that node

                                                               #what anomalies are related to the ppCO2
                                                               MATCH (measurement:Measurement)-[]->(anomaly:Anomaly)
                                                               WHERE measurement.Name = 'ppCO2'
                                                               RETURN anomaly.Name, measurement.ParameterGroup

                                                               # give me a list of possible anomalies regarding the Sabatier system
                                                               Match(anomaly:Anomaly)-[:Affects]->(subsystem:SubSystem)
                                                               WITH apoc.text.sorensenDiceSimilarity(subsystem.Title,'Sabatier') AS similarity, anomaly
                                                               WHERE similarity > 0.85
                                                               return anomaly.Name

                                                               # what is step 1.1 of procedure 3.124
                                                               MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
                                                               WHERE procedure.pNumber = '3.124' AND substep.Step = 1 AND substep.SubStep = 1
                                                               RETURN substep.Title, substep.Action

                                                               # next
                                                               MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
                                                               WHERE procedure.pNumber = '3.124' AND substep.Step = 1 AND substep.SubStep = 2
                                                               RETURN substep.Title, substep.Action

                                                               # what is step 4.2 of procedure 3.104
                                                               MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
                                                               WHERE procedure.pNumber = '3.124' AND substep.Step = 1 AND substep.SubStep = 1
                                                               RETURN substep.Title, substep.Action

                                                               # next
                                                               MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
                                                               WHERE procedure.pNumber = '3.104' AND substep.Step = 4 AND substep.SubStep = 3
                                                               RETURN substep.Title, substep.Action

                                                               # how long it takes to solve tccs fan failure
                                                               MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                                                               WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'TCCS Aux Fan #1 Failure') AS similarity, procedure
                                                               WHERE similarity > 0.8
                                                               RETURN procedure.ETR, procedure.Title, procedure.pNumber

                                                               # tell me the list of possible anomalies of trace contaminant control system
                                                               Match(anomaly:Anomaly)-[:Affects]->(subsystem:SubSystem) WITH apoc.text.sorensenDiceSimilarity(subsystem.Title,'Trace Contaminant Control System') AS similarity, anomaly WHERE similarity > 0.85 return anomaly.Name

                                                               # what is step 4.2 of procedure 3.113
                                                               MATCH (procedure:Procedure)-[:Has]->(substep:SubStep) WHERE procedure.pNumber = '3.113' AND substep.Step = 4 AND substep.SubStep = 2 RETURN substep.Title, substep.Action

                                                               # what is the difference in symptoms between cdra failure and main cabin fan failure
                                                               MATCH (measurement:Measurement)-[r:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
                                                               WHERE anomaly.Name IN ['CDRA Failure', 'Main Cabin Fan Failure']
                                                               RETURN anomaly.Name,  measurement.Name,  measurement.ParameterGroup, type(r)

                                                               # what is the difference in symptoms between n2 tank burst, emergency O2 system maintenance and fuel cell degrade
                                                               MATCH (measurement:Measurement)-[r:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly) WHERE anomaly.Name IN ['N2 Tank Burst', 'Emergency O2 System Maintenance', 'Fuel Cell Degrade'] RETURN anomaly.Name,  measurement.Name,  measurement.ParameterGroup, type(r)

                                                               # What is the confidence score of 'ppCO2','Exceeds_UpperWarningLimit','L2','ppCO2','Exceeds_UpperWarningLimit','L1','ppO2','Exceeds_LowerCautionLimit','L1','ppO2','Exceeds_LowerCautionLimit','L2' for cdra failure
                                                               MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_LowerCautionLimit]->(anomaly:Anomaly) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement WHERE similarity > 0.8 AND measurement.Name = 'ppCO2' AND type(r) = 'Exceeds_UpperWarningLimit' OR measurement.Name = 'ppO2' AND type(r) = 'Exceeds_LowerCautionLimit' WITH COUNT(DISTINCT measurement) AS measurementCount MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_UpperCautionLimit|Exceeds_LowerCautionLimit|Exceeds_LowerWarningLimit]->(anomaly:Anomaly) WHERE anomaly.Name = 'CDRA Failure' WITH COUNT(DISTINCT measurement) AS totalCount, measurementCount WITH measurementCount * 1.0 / totalCount AS ratio WITH ratio, CASE WHEN ratio < 0.12 THEN 'Extremely Unlikely : 0-0.11' WHEN 0.12 <= ratio < 0.23 THEN 'Highly Unlikely : 0.12-0.22' WHEN 0.23 <= ratio < 0.34 THEN 'Unlikely : 0.23-0.33' WHEN 0.34 <= ratio < 0.45 THEN 'Moderately Unlikely : 0.34-0.44' WHEN 0.45 <= ratio < 0.56 THEN 'Equally Likely and Unlikely : 0.45-0.55' WHEN 0.56 <= ratio < 0.67 THEN 'Moderately Likely : 0.56-0.66' WHEN 0.67 <= ratio < 0.78 THEN 'Likely : 0.67-0.77' WHEN 0.78 <= ratio < 0.89 THEN 'Highly Likely : 0.78-0.88' ELSE 'Extremely Likely : 0.89-1.0' END AS text_score RETURN ratio, text_score

                                                               # What is the confidence score of 'Acetaldehyde','Exceeds_UpperWarningLimit','L2','Acetaldehyde','Exceeds_UpperWarningLimit','L1','Aux Cabin Fan #1','Exceeds_LowerCautionLimit','L1','Aux Cabin Fan #1','Exceeds_LowerCautionLimit','L2' for tccs auxilary fan 1 failure
                                                               MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_LowerCautionLimit]->(anomaly:Anomaly) WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'TCCS Auxiliary Fan #1 Failure') AS similarity, measurement WHERE similarity > 0.8 AND measurement.Name = 'Acetaldehyde' AND type(r) = 'Exceeds_UpperWarningLimit' OR measurement.Name = 'Aux Cabin Fan #1' AND type(r) = 'Exceeds_LowerCautionLimit' WITH COUNT(DISTINCT measurement) AS measurementCount MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_UpperCautionLimit|Exceeds_LowerCautionLimit|Exceeds_LowerWarningLimit]->(anomaly:Anomaly) WHERE anomaly.Name = 'CDRA Failure' WITH COUNT(DISTINCT measurement) AS totalCount, measurementCount WITH measurementCount * 1.0 / totalCount AS ratio WITH ratio, CASE WHEN ratio < 0.12 THEN 'Extremely Unlikely : 0-0.11' WHEN 0.12 <= ratio < 0.23 THEN 'Highly Unlikely : 0.12-0.22' WHEN 0.23 <= ratio < 0.34 THEN 'Unlikely : 0.23-0.33' WHEN 0.34 <= ratio < 0.45 THEN 'Moderately Unlikely : 0.34-0.44' WHEN 0.45 <= ratio < 0.56 THEN 'Equally Likely and Unlikely : 0.45-0.55' WHEN 0.56 <= ratio < 0.67 THEN 'Moderately Likely : 0.56-0.66' WHEN 0.67 <= ratio < 0.78 THEN 'Likely : 0.67-0.77' WHEN 0.78 <= ratio < 0.89 THEN 'Highly Likely : 0.78-0.88' ELSE 'Extremely Likely : 0.89-1.0' END AS text_score RETURN ratio, text_score

                                                               Note: if multiple answers list all

                                                               """

            client = OpenAI(api_key=api_key)

            #########################
            # Intent Classification #
            #########################

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": intent_classification_template.format(
                        question=request.data['command'])}
                ],
                temperature=0,
            )
            classify_answer = response.choices[0].message.content.strip()
            print("classify intent: ", classify_answer)

            ###################################################################################################################################
            if classify_answer == 'parameter query':
                try:
                    sensor_data = json.loads(sim.get_sensor_data())
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system",
                             "content": f"You are a helpful assistant that answers questions based on sensor data which is given to you as a JSON data - {sensor_data}. According to the question asked, provide clear, natural, and conversational answers strictly based on the information found in the data. If the data doesn't contain the requested information,say that the info is not available, without offering external information or suggestions. All answers should remain within the context of the data."},
                            {"role": "user",
                             "content": f"This is the history of previous conversations for your context: {self.generate_context(request.data['command'], 'generated')}. Answer the question - {request.data['command']}"}
                        ],
                        temperature=0,
                    )

                    response = res.choices[0].message.content.strip()

                    self.session_state['user_input'].append(request.data['command'])
                    self.session_state['generated'].append(response)
                    self.generate_context(response, 'generated')

                    print("parameter query response: ", response)
                    return Response({"response": {
                        "voice_message": response,
                        "visual_message_type": ["text"],
                        "visual_message": [response],
                        "writer": "daphne"}
                    })
                except Exception as e:
                    return Response({"response": {
                        "voice_message": 'No info available',
                        "visual_message_type": ["text"],
                        "visual_message": ["No info available"],
                        "writer": "daphne"}
                    })
            ##################################################################################################################
            ##################################################################################################################
            elif classify_answer == 'knowledge graph query' or classify_answer == 'general query':

                history = self.generate_context(request.data['command'], 'generated')
                user_question = f"This is the history of previous conversations for your context: {history}. Now give the cypher query for this question. If an exact match is not found, select the closest possible match based on similarity or relevance in the given data to you. Only give the query. Do NOT format it as code. Do NOT include any backticks or language indicators like cypher. Only output the query as plain text. The question is: {request.data['command']}"

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": cypher_template},
                        {"role": "user",
                         "content": user_question}
                    ],
                    temperature=0,
                )

                cypher_query = response.choices[0].message.content.strip()
                print("cypher query response: ", cypher_query)
                graph_result = self.run_cypher_query(graph, cypher_query)

                if len(graph_result) == 0 and classify_answer == 'general query':
                    user_question = f"This is the history of previous conversations for your context: {self.generate_context(request.data['command'], 'generated')}. Now give the answer for this question. The question is: {request.data['command']}"
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system",
                             "content": "You are a virtual assistant designed to assist astronauts in resolving spacecraft anomalies when mission control is unavailable. Astronauts will ask you questions regarding anomalies, their causes, signatures, procedures for fixing them, related risks, etc."},
                            {"role": "user", "content": user_question}
                        ],
                        temperature=0,
                    )
                    final_answer = response.choices[0].message.content.strip()

                    print("general query: ", final_answer)

                    return Response({"response": {
                        "voice_message": final_answer,
                        "visual_message_type": ["text"],
                        "visual_message": [final_answer],
                        "writer": "daphne"}
                    })

                print("graph result: ", graph_result)

                self.session_state['user_input'].append(request.data['command'])
                self.session_state['database_results'].append(str(graph_result))

                ques_desc = f"This is the history of previous conversations for your context: {self.generate_context(request.data['command'], 'generated')} . These are the cypher query result - {graph_result}. Now, answer the following question - {request.data['command']}"

                print("question desc for cypher query presenting", ques_desc)

                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system",
                         "content": "You are a helpful assistant that helps present cypher query results in a human readable form and give clear, natural, and conversational answers. If asked to provide a pdf or link do NOT say that you cannot provide it. Only present cypher query results without any additional instructions or comments. Do not ask for clarification or specify methods of receiving the document. Do NOT write any fullforms and present information as it is in sentences, give line breaks wherever required to improve formatting. Give the answer with each item on a new line to improve formatting. For list items or multiple points, ensure that each starts on a new line with a gap. If the answer has L1 and L2 parameter groups, do NOT say L1 and L2 parameter groups, just say L1 and L2, that is sufficient.' If the cypher query results are empty, return No info available.  If the cypher query results are NOT empty, present the cypher query results."},
                        {"role": "user",
                         "content": ques_desc}
                    ],
                    temperature=0,
                )

                final_answer = final_response.choices[0].message.content.strip()
                print("final answer for presenting cypher query results", final_answer)
                print(final_answer)
                ##################################################################################################################
                ##################################################################################################################
                folder_path = os.path.join("./", "AT", "databases", "procedures")
                # folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
                desired_string = 'procedure.Title'
                matching_keys = []
                try:
                    if len(graph_result) > 0:
                        matching_keys = [key for key in graph_result[0].keys() if desired_string in key]
                        print("matching_keys ", matching_keys)
                        link_flag = 0
                        file_path = ""
                        pdf_link = None
                        pdf_name = None
                        for key in matching_keys:
                            value = graph_result[0].get(key, 'Key not found')
                            print("VALUE: " + value)
                            print(os.path.join(folder_path, value + ".pdf"))
                            try:
                                file_path = os.path.join(folder_path, value + ".pdf")
                                print("File_PATH ", file_path)
                                procedure_pdfs = os.listdir(folder_path)
                                print("PP:", procedure_pdfs)
                                if value + ".pdf" in procedure_pdfs:
                                    pdf_name = value + ".pdf"
                                    folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases",
                                                               "procedures")
                                    filepath = os.path.join(folder_path, pdf_name)
                                    path = os.path.join(os.getcwd(), "AT", "databases", "procedures", pdf_name)
                                    pdf_link = urllib.parse.urlencode({"": path})
                                    # print("res[0]: ", result1[0])
                                    link_flag = 1
                            except Exception as e:
                                break

                        if link_flag == 1:
                            response_final = final_answer + "\nHere is the link\n" + f'<a href="{"api/at/recommendation/procedure?filename" + pdf_link}" target="_blank">{pdf_name}</a>'

                            self.session_state['generated'].append(response_final)
                            self.generate_context(response_final, 'generated')

                            print(self.session_state)

                            return Response({"response": {
                                "voice_message": final_answer,
                                "visual_message_type": ["text"],
                                "visual_message": [response_final],
                                "writer": "daphne"}
                            })
                except Exception as e:
                    pass
                    ##################################################################################################################
                    ##################################################################################################################

                self.session_state['user_input'].append(request.data['command'])
                self.session_state['generated'].append(final_answer)
                self.generate_context(final_answer, 'generated')

                print(self.session_state)
                print("cypher query final response: ", final_answer)
                return Response({"response": {
                    "voice_message": final_answer,
                    "visual_message_type": ["text"],
                    "visual_message": [final_answer],
                    "writer": "daphne"}
                })

            ##################################################################################################################
            ##################################################################################################################

            elif classify_answer == 'image request':
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": f"You are a helpful assistant that gives the image name from the image name list. When a user asks to see an image related to a specific object or term, look through the list of available image names below and return the name that matches the user's request most closely. Consider spelling variations or synonyms and prioritize the closest match based on object names or descriptions. The list of available image names is: {images_list}. If the image name is not in the list, give the image name that matches closest to the ones in the image list provided. Just give the image name from the list. Don't output anything else other than the name."},
                        {"role": "user", "content": request.data['command']}
                    ],
                    temperature=0,
                )

                image_name = response.choices[0].message.content.strip()
                image_name = image_name.replace("'", "")

                print("image query name: ", image_name)

                encoded_file_path = urllib.parse.quote(
                    os.path.join("home", "ubuntu", "daphne-at-interface", "src", "images",
                                 image_name + ".png"), safe="")
                encoded_file_path = f"home%2Fubuntu%2Fdaphne-at-interface%2Fsrc%2Fimages%2F{image_name}.png"
                image_link = f"https://daphne-at.selva-research.com/api/at/recommendation/figure?filename=%2F{encoded_file_path}"
                image_name = image_name.replace("_", " ")

                print("image query link: ", image_link)

                res = "\nHere is the image<br>" + f'<a href="{image_link}" target="_blank">{image_name}</a>'
                res_voice = "Here is the image you requested"
                return Response({"response": {
                    "voice_message": res_voice,
                    "visual_message_type": ["text"],
                    "visual_message": [res],
                    "writer": "daphne"}
                })

                ##################################################################################################################
                ##################################################################################################################

            elif classify_answer == 'storage query':
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": f"You are a helpful assistant that gives the location of the item asked, using the list containing the items and their corresponding locations provided to you. When a user asks for the location of an item, look through the list of available item names and return the loation of the item that matches the user's request most closely. Consider spelling variations or synonyms and prioritize the closest match based on object names or descriptions. The storage list is: {images_list}. According to the question asked, provide clear, natural, and conversational answers strictly based on the information found in the data. If the data doesn't contain the requested information,say that the info is not available, without offering external information or suggestions. All answers should remain within the context of the data."},
                        {"role": "user", "content": request.data['command']}
                    ],
                    temperature=0,
                )

                image_name = response.choices[0].message.content.strip()
                image_name = image_name.replace("'", "")

                print("image query name: ", image_name)

                encoded_file_path = urllib.parse.quote(
                    os.path.join("home", "ubuntu", "daphne-at-interface", "src", "images",
                                 image_name + ".png"), safe="")
                encoded_file_path = f"home%2Fubuntu%2Fdaphne-at-interface%2Fsrc%2Fimages%2F{image_name}.png"
                image_link = f"https://daphne-at.selva-research.com/api/at/recommendation/figure?filename=%2F{encoded_file_path}"
                image_name = image_name.replace("_", " ")

                print("image query link: ", image_link)

                res = "\nHere is the image<br>" + f'<a href="{image_link}" target="_blank">{image_name}</a>'
                res_voice = "Here is the image you requested"
                return Response({"response": {
                    "voice_message": res_voice,
                    "visual_message_type": ["text"],
                    "visual_message": [res],
                    "writer": "daphne"}
                })

            ##################################################################################################################
            ##################################################################################################################

            # elif classify_answer == 'general query':
            else:
                user_question = f"This is the history of previous conversations for your context: {self.generate_context(request.data['command'], 'generated')}. Now give the answer for this question. The question is: {request.data['command']}"
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system",
                         "content": "You are a virtual assistant designed to assist astronauts in resolving spacecraft anomalies when mission control is unavailable. Astronauts will ask you questions regarding anomalies, their causes, signatures, procedures for fixing them, related risks, etc."},
                        {"role": "user", "content": user_question}
                    ],
                    temperature=0,
                )
                final_answer = response.choices[0].message.content.strip()

                print("general query: ", final_answer)

                return Response({"response": {
                    "voice_message": final_answer,
                    "visual_message_type": ["text"],
                    "visual_message": [final_answer],
                    "writer": "daphne"}
                })

        #################################a#################################################################################
        ##################################################################################################################
        except Exception as e:
            print('Error:', e)
            load_dotenv()
            api_key = os.environ['OPENAI_API_KEY'] = os.getenv('api_key')
            client = OpenAI(
                api_key=api_key)
            user_question = f"This is the history of previous conversations for your context: {self.generate_context(request.data['command'], 'generated')}. Now give the answer for this question. The question is: {request.data['command']}"

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "You are a virtual assistant designed to assist astronauts in resolving spacecraft anomalies when mission control is unavailable. Astronauts will ask you questions regarding anomalies, their causes, signatures, procedures for fixing them, related risks, etc."},
                    {"role": "user", "content": user_question}
                ],
                temperature=0,
            )
            final_answer = response.choices[0].message.content.strip()
            print("general query: ", final_answer)

            return Response({"response": {
                "voice_message": final_answer,
                "visual_message_type": ["text"],
                "visual_message": [final_answer],
                "writer": "daphne"}
            })

        #     chat = ChatOpenAI(model="gpt-4o")
        #
        #     messages = [
        #         SystemMessage(
        #             content="You are a helpful assistant that helps know if the question is asking about current value or status of something, Answer in Yes or No only"
        #         ),
        #         HumanMessage(content=request.data['command']),
        #     ]
        #
        #     response = chat(messages)
        #     print("RESPONSEEEEEEE:", response.content)
        #     templates = [r"^Check measurement (.+) status$", r"^Check (.+) status$",
        #                  r"^Show the current value of (.+) measurement$", r"^Show the current value of (.+)$",
        #                  r"^What is the current value of (.+) measurement$", r"^What is the current value of (.+)$",
        #                  r"^current value$", r"^What is the value of (.+) measurement currently$",
        #                  r"^What is the value of (.+) currently$", r"^What is the status of (.+) measurement$",
        #                  r"^What is the status of (.+)$", r"^status$",r"^What is current value of (.+) measurement$",
        #                  r"^What is current value of (.+)$", r"^What is status of (.+)$",
        #                  r"^What is status of (.+) measurement$"]
        #     flag = False
        #     for template in templates:
        #         pattern = re.compile(template, re.IGNORECASE)
        #         flag = bool(pattern.match(request.data['command']))
        #         print(flag)
        #         if flag:
        #             response.content = 'Yes'
        #             break
        #     if response.content == 'No':
        #         raise ValueError("Optional error message")
        #
        #     sensor_data = json.loads(sim.get_sensor_data())
        #     print("typee: ", sensor_data)
        #     spec = JsonSpec(dict_=dict(sensor_data), max_value_length=sys.maxsize)
        #     toolkit = JsonToolkit(spec=spec)
        #     agent = create_json_agent(llm=ChatOpenAI(temperature=0, model="gpt-4o"), toolkit=toolkit,
        #                               max_iterations=sys.maxsize,
        #                               allow_dangerous_requests=True,
        #                               verbose=True)
        #     response = agent.run(request.data['command'])
        #
        #     return Response({"response": {
        #         "voice_message": response,
        #         "visual_message_type": ["text"],
        #         "visual_message": [response],
        #         "writer": "daphne"}
        #     })
        #
        # except Exception as e:
        #     print("Error:", e)
        #     print("hi: ", request.data['command'])
        #     # templates = [r"^Check measurement (.+) status$", r"^Check (.+) status$",
        #     #              r"^Show the current value of (.+) measurement$", r"^Show the current value of (.+)$",
        #     #              r"^Read steps of procedure (.+)", r"^Read steps of (.+)", "Next", "previous", "Repeat",
        #     #              "Previous", "
        #
        #     ", "repeat"]
        #     # flag = False
        #     # for template in templates:
        #     #     pattern = re.compile(template, re.IGNORECASE)
        #     #     flag = bool(pattern.match(request.data['command']))
        #     #     print(flag)
        #     #     if flag:
        #     #         break
        #     # if flag == False:
        #     # langchain changes
        #     graph = Neo4jGraph(
        #         url="bolt://13.58.54.49:7687",
        #         username="neo4j",
        #         password="goSEAKers!"
        #     )
        #
        #
        #     load_dotenv()
        #     os.environ['OPENAI_API_KEY'] = os.getenv('api_key')
        #     print("HERE")
        #     # chain = GraphCypherQAChain.from_llm(
        #     #     ChatOpenAI(temperature=0), graph=graph, verbose=True, return_when_no_match=False, return_direct=True
        #     # )
        #
        #     CYPHER_GENERATION_TEMPLATE = """
        #
        #                         Task:Generate Cypher statement to query a graph database.
        #
        #                         Instructions:
        #                         You are a virtual assistant that helps astronauts when there are spacecraft anomalies and
        #                         mission control is not available. Astronauts will ask you questions about the anomalies,
        #                         their signature, the procedures to solve those anomalies, etc. To answer these questions,
        #                         you can generate a Cypher statement to query a graph database.
        #
        #                         Use only the provided relationship types and properties in the schema.
        #                         Do not use any other relationship types or properties that are not provided.
        #                         If the cipher query has empty return say no info available.
        #                         If multiple answers exists mention all.
        #                         Just list the query results don't try to frame answers.
        #
        #                         Schema:
        #                         {schema}
        #
        #                         Cypher examples:
        #                         # Risks of main cabin fan failure include what?
        #                         MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
        #                         WITH apoc.text.sorensenDiceSimilarity(a.Name,'main cabin fan failure') AS similarity, risk
        #                         WHERE similarity > 0.85
        #                         Return
        #                         CASE WHEN risk IS NULL
        #                           THEN 'No risks found'
        #                           ELSE risk.Title
        #                           END
        #
        #                         # What are the potential risks of nitrogen tank leak
        #                         MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'N2 Ballast Tank Line Leak') AS similarity, risk
        #                         WHERE similarity > 0.85
        #                         Return
        #                         CASE WHEN risk IS NULL
        #                           THEN 'No risks found'
        #                           ELSE risk.Title
        #                           END
        #
        #                         # What are the potential risks of a nitrogen tank burst and a nitrogen tank line leak.
        #                         MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
        #                         WHERE anomaly.Name IN ['N2 Tank Burst', 'N2 Ballast Tank Line Leak']
        #                         RETURN risk.Title
        #                         Instructions : give answers from return value
        #
        #                         # What are the potential risks of a reduced cabin fan capacity. Don't give answers from the web
        #                         # What are the potential risks of a reduced cabin fan capacity. Don't give answers from the web
        #                         MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Reduced Main Cabin Fan #1 Capacity') AS similarity, risk
        #                         WHERE similarity > 0.85
        #                         RETURN
        #                           CASE WHEN risk IS NULL
        #                           THEN 'No risks found'
        #                           ELSE risk.Title
        #                           END
        #                         Instructions :  Don't give answers from the web
        #
        #                         # what are the potential risks of trace contaminants. Don't give answers from the web
        #                         # what are the risks of trace contaminants. Don't give answers from the web
        #                         # What are the potential risks of trace contaminants. Don't give answers from the web
        #                         MATCH (anomaly:Anomaly)-[:Can_Cause]->(risk:Risk)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Trace Contaminants') AS similarity, risk
        #                         WHERE similarity > 0.85
        #                         RETURN
        #                           CASE WHEN risk IS NULL
        #                           THEN 'No risks found'
        #                           ELSE risk.Title
        #                           END
        #
        #                         # what is the signature of CDRA Failure. Mention all m.Name, m.ParameterGroup, r
        #                         # what is the signature associated with cdra failure. Mention all m.Name, m.ParameterGroup, r
        #                         MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement, relationship
        #                         WHERE similarity > 0.85
        #                         RETURN measurement.Name, measurement.ParameterGroup, relationship
        #                         # Note: Give answers from query results
        #
        #                         # what are the symptoms of cdra failure. Mention all m.Name, m.ParameterGroup, r
        #                         # if cdra failure was occurring what symptoms would I expect to see. Give answer from the query result
        #                         MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement, relationship
        #                         WHERE similarity > 0.85
        #                         RETURN measurement.Name, measurement.ParameterGroup, relationship
        #
        #                         # what measurements are affected by main cabin fan failure
        #                         MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Main Cabin Fan Failure') AS similarity, measurement, relationship
        #                         WHERE similarity > 0.85
        #                         RETURN measurement.Name, measurement.ParameterGroup, relationship
        #
        #                         # Note: Give answers from query results
        #
        #                         # what are the characteristic symptoms of cdra lioh filter clogged. Mention all m.Name, m.ParameterGroup, r
        #                         MATCH (measurement:Measurement)-[relationship:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,cdra lioh filter clogged') AS similarity, measurement, relationship
        #                         WHERE similarity > 0.85
        #                         RETURN measurement.Name, measurement.ParameterGroup, relationship
        #
        #
        #                         # Note: Give answers from query results
        #
        #                         # what subsystems does biological filter saturation affect. Answer SubSystem's Title value
        #                         MATCH (anomaly:Anomaly)-[:Affects]->(subsystem:SubSystem)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, subsystem
        #                         WHERE similarity > 0.85
        #                         RETURN subsystem.Title
        #                         # Note: Answer subsystem.Title value
        #
        #                         # how do i fix biological filter saturation. Mention the procedure titlte
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.Title
        #                         # Note: Mention the procedure title
        #
        #                         Note: Do not include any explanations or apologies in your responses.
        #                         Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
        #                         Do not include any text except the generated Cypher statement.
        #                         If multiple answers list all
        #
        #                         # how long will it take me to solve biological filter saturation
        #                         # what is the average timeframe for resolving biological filter saturation
        #                         # how long will it take to complete fuel cell maintenance. Mention all times with correspnding procesdures, give the higher value first
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.ETR
        #
        #                         #Instructions: Mention all times in order with correspnding procesdures titles and number
        #
        #                         # how long is 3.109
        #                         # time of completion 3.101
        #                         MATCH (procedure:Procedure)
        #                         WHERE procedure.pNumber = '3.109'
        #                         RETURN procedure.ETR
        #
        #                         # how long would electrolysis system biological filter swap out take to complete
        #                         MATCH (procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(procedure.Title,'Electrolysis System Biological Filter Swapout') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.ETR
        #
        #                         # read steps of procedure 3.109
        #                         MATCH (procedure:Procedure)-[:Has]->(step:Step)
        #                         WHERE procedure.pNumber = '3.109'
        #                         RETURN step.Title, step.Action
        #
        #                         # how long will it take to solve wrs off nominal ph level.
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'WRS Off Nominal pH Level') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.ETR, procedure.Title, procedure.pNumber
        #
        #                         # What are the procedures for cdra failure
        #                         # Provide the link for cdra failure
        #                         # Provide the pdf for cdra failure
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.Title, procedure.pNumber
        #
        #                         # Give me the link for cdra failure
        #                         # Givde me the pdf for cdra failure
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, procedure
        #                         WHERE similarity > 0.85
        #                         RETURN procedure.Title, procedure.pNumber
        #
        #                         Note: answer the question like -> The title of the procedure is "CDRA Zeolite Filter Swapout" and the procedure number is 3.104.
        #
        #                         # provide the link for procedure 3.104
        #                         # provide the pdf for procedure 3.104
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WHERE procedure.pNumber = '3.104'
        #                         RETURN procedure.Title, procedure.pNumber
        #
        #                         # read steps cdra zeolite filter swap out
        #                         MATCH (procedure:Procedure)-[:Has]->(step:Step)
        #                         WHERE procedure.Title = 'CDRA Zeolite Filter Swapout'
        #
        #                         MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
        #                         WHERE procedure.Title = 'CDRA Zeolite Filter Swapout'
        #
        #
        #                         MATCH (procedure:Procedure)-[:Has]->(subsubstep:SubSubStep)
        #                         WHERE procedure.Title = 'CDRA Zeolite Filter Swapout'
        #                         RETURN step.Title, step.Action, substep.Title, substep.Action, subsubstep.Title, subsubstep.Action
        #
        #                         ORDER BY step.Step,subsubstep.SubSubStep,substep.SubStep
        #
        #                         Note: always check all nodes connected through has relationship
        #
        #                         # list all substeps of step 1 of procedure 3.106
        #                         MATCH (procedure:Procedure)-[:Has]->(ss)
        #                         WHERE procedure.pNumber = '3.106' AND ss.Step = 1
        #                         RETURN ss.Title, ss.Action
        #                         ORDER BY ss.SubStep
        #
        #                         Note: always check all nodes connected through has relationship
        #
        #                         # what is the procedure for Fuel Cell #1 and PDU Failure
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         Where anomaly.Name='Fuel Cell #1 and PDU Failure'
        #                         RETURN procedure.Title, procedure.pNumber
        #
        #                         Note: use the name of the node type as the variable for that node
        #
        #                         #what anomalies are related to the ppCO2
        #                         MATCH (measurement:Measurement)-[]->(anomaly:Anomaly)
        #                         WHERE measurement.Name = 'ppCO2'
        #                         RETURN anomaly.Name, measurement.ParameterGroup
        #
        #                         # give me a list of possible anomalies regarding the Sabatier system
        #                         Match(anomaly:Anomaly)-[:Affects]->(subsystem:SubSystem)
        #                         WITH apoc.text.sorensenDiceSimilarity(subsystem.Title,'Sabatier') AS similarity, anomaly
        #                         WHERE similarity > 0.85
        #                         return anomaly.Name
        #
        #                         # what is step 1.1 of procedure 3.124
        #                         MATCH (procedure:Procedure)-[:Has]->(substep:SubStep)
        #                         WHERE procedure.pNumber = '3.124' AND substep.Step = 1 AND substep.SubStep = 1
        #                         RETURN substep.Title, substep.Action
        #
        #                         # how long it takes to solve tccs fan failure
        #                         MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'TCCS Aux Fan #1 Failure') AS similarity, procedure
        #                         WHERE similarity > 0.8
        #                         RETURN procedure.ETR, procedure.Title, procedure.pNumber
        #
        #                         # what is the difference in symptoms between cdra failure and main cabin fan failure
        #                         MATCH (measurement:Measurement)-[r:Exceeds_LowerCautionLimit | Exceeds_LowerWarningLimit | Exceeds_UpperCautionLimit | Exceeds_UpperWarningLimit]->(anomaly:Anomaly)
        #                         WHERE anomaly.Name IN ['CDRA Failure', 'Main Cabin Fan Failure']
        #                         RETURN anomaly.Name,  measurement.Name,  measurement.ParameterGroup, type(r)
        #
        #                         # What is the confidence score of 'ppCO2','Exceeds_UpperWarningLimit','L2','ppCO2','Exceeds_UpperWarningLimit','L1','ppO2','Exceeds_LowerCautionLimit','L1','ppO2','Exceeds_LowerCautionLimit','L2' for cdra failure
        #                         MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_LowerCautionLimit]->(anomaly:Anomaly)
        #                         WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, measurement
        #                         WHERE similarity > 0.8 AND
        #                         measurement.Name = 'ppCO2' AND type(r) = 'Exceeds_UpperWarningLimit' OR
        #                         measurement.Name = 'ppO2' AND type(r) = 'Exceeds_LowerCautionLimit'
        #                         WITH COUNT(DISTINCT measurement) AS measurementCount
        #
        #                         MATCH (measurement:Measurement)-[r:Exceeds_UpperWarningLimit|Exceeds_UpperCautionLimit|Exceeds_LowerCautionLimit|Exceeds_LowerWarningLimit]->(anomaly:Anomaly)
        #                         WHERE anomaly.Name = 'CDRA Failure'
        #                         WITH COUNT(DISTINCT measurement) AS totalCount, measurementCount
        #
        #
        #                         WITH measurementCount * 1.0 / totalCount AS ratio
        #
        #
        #                         WITH ratio,
        #                         CASE
        #                             WHEN ratio < 0.12 THEN "Extremely Unlikely : 0-0.11"
        #                             WHEN 0.12 <= ratio < 0.23 THEN "Highly Unlikely : 0.12-0.22"
        #                             WHEN 0.23 <= ratio < 0.34 THEN "Unlikely : 0.23-0.33"
        #                             WHEN 0.34 <= ratio < 0.45 THEN "Moderately Unlikely : 0.34-0.44"
        #                             WHEN 0.45 <= ratio < 0.56 THEN "Equally Likely and Unlikely : 0.45-0.55"
        #                             WHEN 0.56 <= ratio < 0.67 THEN "Moderately Likely : 0.56-0.66"
        #                             WHEN 0.67 <= ratio < 0.78 THEN "Likely : 0.67-0.77"
        #                             WHEN 0.78 <= ratio < 0.89 THEN "Highly Likely : 0.78-0.88"
        #                             ELSE "Extremely Likely : 0.89-1.0"
        #                         END AS text_score
        #
        #                         RETURN ratio, text_score
        #
        #                         The question is:
        #                         {question}"""
        #
        #     CYPHER_GENERATION_PROMPT = PromptTemplate(
        #         input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
        #     )
        #
        #     chain = GraphCypherQAChain.from_llm(
        #         ChatOpenAI(temperature=0, model="gpt-4o"), allow_dangerous_requests=True, graph=graph, verbose=True,
        #         cypher_prompt=CYPHER_GENERATION_PROMPT, return_direct=True, top_k=sys.maxsize, validate_cypher=True
        #     )
        #     print("ques:", request.data['command'])
        #     print(chain)
        #     try:
        #         temps = [r"^Show the image of component (.+)$", r"^Show the image of (.+)$"]
        #         image_link = ""
        #         image_name = ""
        #
        #         flag1 = False
        #         for temp in temps:
        #             pattern = re.compile(temp, re.IGNORECASE)
        #             flag1 = bool(pattern.match(request.data['command']))
        #             if flag1:
        #                 match = re.match(pattern, request.data['command'])
        #                 if match:
        #                     image_name = match.group(1)
        #                     image_name = image_name.replace(" ", "_")
        #
        #                     encoded_file_path = urllib.parse.quote(
        #                         os.path.join("home", "ubuntu", "daphne-at-interface", "src", "images",
        #                                      image_name + ".png"), safe="")
        #                     image_link = f"https://daphne-at.selva-research.com/api/at/recommendation/figure?filename=%2F{encoded_file_path}"
        #                     image_name = image_name.replace("_", " ")
        #                 break
        #         if flag1:
        #             res = "\nHere is the image<br>" + f'<a href="{image_link}" target="_blank">{image_name}</a>'
        #             res_voice = "Here is the image you requested"
        #             return Response({"response": {
        #                 "voice_message": res_voice,
        #                 "visual_message_type": ["text"],
        #                 "visual_message": [res],
        #                 "writer": "daphne"}
        #             })
        #         # print(self.generate_context(request.data['command'], 'user_input'))
        #
        #         # question = {'history' : self.generate_context(request.data['command'], 'user_input'), 'query' : request.data['command']}
        #         # print(question)
        #         ques_desc = f"Using this as history of conversation and context {self.generate_context(request.data['command'], 'generated')} answer the following question {request.data['command']}"
        #         print("QUES_DESC:", ques_desc)
        #         result1 = chain.run(ques_desc)
        #
        #         self.session_state['user_input'].append(request.data['command'])
        #         self.session_state['database_results'].append(str(result1))
        #
        #         # print(self.session_state['database_results'])
        #     except Exception as e:
        #         print('Error:', e)
        #         if request.data['command'] in self.session_state['user_input']:
        #             ind = self.session_state['user_input'].index(request.data['command'])
        #             return Response({"response": {
        #                 "voice_message": "Here is the what I found",
        #                 "visual_message_type": ["text"],
        #                 "visual_message": [self.session_state['generated'][ind]],
        #                 "writer": "daphne"}
        #             })
        #         try:
        #             result1 = chain.run(request.data['command'])
        #
        #             self.session_state['user_input'].append(request.data['command'])
        #             self.session_state['database_results'].append(str(result1))
        #         except Exception as err:
        #             chat = ChatOpenAI(model="gpt-4o")
        #
        #             messages = [
        #                 SystemMessage(
        #                     content="You are a helpful assistant that helps present cipher query results to human readable form"
        #                 ),
        #                 HumanMessage(content=request.data['command']),
        #             ]
        #
        #             response = chat(messages)
        #             self.session_state['user_input'].append(request.data['command'])
        #             self.session_state['generated'].append(response.content)
        #             self.generate_context(response.content, 'generated')
        #
        #             print(self.session_state)
        #             return Response({"response": {
        #                 "voice_message": response.content,
        #                 "visual_message_type": ["text"],
        #                 "visual_message": [response.content],
        #                 "writer": "daphne"}
        #             })
        #
        #     folder_path = os.path.join("./", "AT", "databases", "procedures")
        #     # folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
        #     desired_string = 'Title'
        #     matching_keys = []
        #     if len(result1) > 0:
        #         matching_keys = [key for key in result1[0].keys() if desired_string in key]
        #         print("matching_keys ", matching_keys)
        #     link_flag = 0
        #     file_path = ""
        #     pdf_link = None
        #     pdf_name = None
        #     for key in matching_keys:
        #         value = result1[0].get(key, 'Key not found')
        #         print("VALUE: " + value)
        #         print(os.path.join(folder_path, value + ".pdf"))
        #
        #         if os.path.exists(os.path.join(folder_path, value + ".pdf")):
        #             file_path = os.path.join(folder_path, value + ".pdf")
        #             print("File_PATH ", file_path)
        #             procedure_pdfs = os.listdir(folder_path)
        #             print("PP:", procedure_pdfs)
        #             if value + ".pdf" in procedure_pdfs:
        #                 pdf_name = value + ".pdf"
        #                 folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
        #                 filepath = os.path.join(folder_path, pdf_name)
        #                 path = os.path.join(os.getcwd(), "AT", "databases", "procedures", pdf_name)
        #                 pdf_link = urllib.parse.urlencode({"": path})
        #                 print("res[0]: ", result1[0])
        #                 link_flag = 1
        #
        #         # Create a descriptive string
        #         response = ""
        #     result_string = ", ".join(str(item) if isinstance(item, dict) else item for item in result1)
        #     print("RS:", result_string)
        #     print("RES:", result1)
        #     description = "No Results Found"
        #     if result1:
        #         description = "{} present the information in human readable form".format(
        #             result_string)
        #         # Just list the above information as bullet-points without additional text
        #         # Print or use the description as needed
        #     print("Description:", description)
        #     # conversation.run(description)
        #
        #     chat = ChatOpenAI(model="gpt-4o")
        #
        #     messages = [
        #         SystemMessage(
        #             content="You are a helpful assistant that helps present cipher query results to human readable form, don't write any fullforms, present information as it is in sentences, give line breaks whereever required to improve formatting"
        #         ),
        #         HumanMessage(content=description),
        #     ]
        #
        #     response = chat(messages)
        #
        #     response.content = response.content.replace('\n', '<br>')
        #     print("Yahoo:", response.dict)
        #
        #     if link_flag == 1:
        #         response_final = response.content + "\nHere is the link\n" + f'<a href="{"api/at/recommendation/procedure?filename" + pdf_link}" target="_blank">{pdf_name}</a>'
        #
        #         self.session_state['generated'].append(response_final)
        #         self.generate_context(response_final, 'generated')
        #
        #         print(self.session_state)
        #
        #         return Response({"response": {
        #             "voice_message": response.content,
        #             "visual_message_type": ["text"],
        #             "visual_message": [response_final],
        #             "writer": "daphne"}
        #         })
        #
        #     self.session_state['generated'].append(response.content)
        #     self.generate_context(response.content, 'generated')
        #
        #     # print(self.generate_context(response.content, 'generated'))
        #
        #     return Response({"response": {
        #         "voice_message": response.content,
        #         "visual_message_type": ["text"],
        #         "visual_message": [response.content],
        #         "writer": "daphne"}
        #     })

        # End of langchain changes
        # else:
        #     # Define context and see if it was already defined for this session
        #
        #     user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)
        #
        #     # Obtain the merged context
        #     context = self.get_current_context(user_info)
        #
        #     # Save user input as part of the dialogue history
        #     DialogueHistory.objects.create(user_information=user_info,
        #                                    voice_message=request.data["command"],
        #                                    visual_message_type="[\"text\"]",
        #                                    visual_message="[\"" + request.data["command"] + "\"]",
        #                                    writer="user",
        #                                    date=datetime.datetime.utcnow())
        #
        #     print("hi: ", request.data)
        #
        #     # Experiment-specific code to limit what can be asked to Daphne
        #     AllowedCommand.objects.filter(user_information__exact=user_info).delete()
        #
        #     if 'allowed_commands' in request.data:
        #         allowed_commands = json.loads(request.data['allowed_commands'])
        #         for command_type, command_list in allowed_commands.items():
        #             for command_number in command_list:
        #                 AllowedCommand.objects.create(user_information=user_info, command_type=command_type,
        #                                               command_descriptor=command_number)
        #
        #     # If this a choice between three options, check the one the user chose and go on with that
        #     if "is_clarifying_input" in context["dialogue"] and context["dialogue"]["is_clarifying_input"]:
        #         user_choice = request.data['command'].strip().lower()
        #         choices = json.loads(context["dialogue"]["clarifying_commands"])
        #         if user_choice == "first":
        #             choice = choices[0]
        #         elif user_choice == "second":
        #             choice = choices[1]
        #         elif user_choice == "third":
        #             choice = choices[2]
        #         else:
        #             choice = choices[0]
        #         user_turn = DialogueHistory.objects.filter(writer__exact="user").order_by("-date")[1]
        #
        #         # Preprocess the command
        #         processed_command = nlp(user_turn.voice_message.strip().lower())
        #
        #         role_index = context["dialogue"]["clarifying_role"]
        #         command_class = self.command_options[role_index]
        #         condition_name = self.condition_names[role_index]
        #
        #         new_dialogue_contexts = self.create_dialogue_contexts()
        #         dialogue_turn = command_processing.answer_command(processed_command, choice, command_class,
        #                                                           condition_name, user_info, context,
        #                                                           new_dialogue_contexts, request.session)
        #         self.save_dialogue_contexts(new_dialogue_contexts, dialogue_turn)
        #
        #     else:
        #         # Preprocess the command
        #         processed_command = nlp(request.data['command'].strip())
        #
        #         # Classify the command, obtaining a command type
        #         command_roles = command_processing.classify_command_role(processed_command, self.daphne_version)
        #
        #         # Act based on the types
        #         for command_role in command_roles:
        #             command_class = self.command_options[command_role]
        #             condition_name = self.condition_names[command_role]
        #
        #             command_predictions = command_processing.command_type_predictions(processed_command,
        #                                                                               self.daphne_version,
        #                                                                               command_class)
        #
        #             # If highest value prediction is over 95%, take that question. If over 90%, ask the user to make sure
        #             # that is correct by choosing over 3. If less, call BS
        #             max_value = np.amax(command_predictions)
        #             if max_value > 0.95:
        #                 command_type = command_processing.get_top_types(command_predictions, self.daphne_version,
        #                                                                 command_class, top_number=1)[0]
        #                 new_dialogue_contexts = self.create_dialogue_contexts()
        #                 dialogue_turn = command_processing.answer_command(processed_command, command_type,
        #                                                                   command_class,
        #                                                                   condition_name, user_info, context,
        #                                                                   new_dialogue_contexts, request.session)
        #                 self.save_dialogue_contexts(new_dialogue_contexts, dialogue_turn)
        #             elif max_value > 0.90:
        #                 command_types = command_processing.get_top_types(command_predictions, self.daphne_version,
        #                                                                  command_class, top_number=3)
        #                 command_processing.choose_command(command_types, self.daphne_version, command_role,
        #                                                   command_class,
        #                                                   user_info)
        #             else:
        #                 command_processing.not_answerable(user_info)
        #
        #     frontend_response = command_processing.think_response(user_info)
        #
        #     return Response({'response': frontend_response})

    def get_current_context(self, user_info):
        context = {}
        context['dialogue'] = ""  # quick patch
        return context

    def create_dialogue_contexts(self):
        dialogue_context = DialogueContext(is_clarifying_input=False)
        contexts = OrderedDict()
        contexts["dialogue_context"] = dialogue_context
        return contexts

    def save_dialogue_contexts(self, dialogue_contexts, dialogue_turn):
        dialogue_contexts["dialogue_context"].dialogue_history = dialogue_turn
        dialogue_contexts["dialogue_context"].save()


class Dialogue(APIView):
    """
    Get the last 50 messages (by default)
    """
    daphne_version = ""

    def get(self, request, format=None):
        # Define context and see if it was already defined for this session
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        last_dialogue = user_info.dialoguehistory_set.order_by("-date")[:50]
        dialogue_list = [
            {
                "voice_message": piece.voice_message,
                "visual_message_type": json.loads(piece.visual_message_type),
                "visual_message": json.loads(piece.visual_message),
                "writer": piece.writer
            } for piece in last_dialogue
        ]
        dialogue_list.reverse()

        response_json = {
            "dialogue_pieces": dialogue_list
        }

        return Response(response_json)


class ClearHistory(APIView):
    """
    Clear all past dialogue
    """
    daphne_version = ""

    def post(self, request, format=None):
        # Define context and see if it was already defined for this session
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        user_info.dialoguehistory_set.all().delete()

        return Response({
            "result": "Dialogue deleted successfully"
        })


class MixedInitiative(APIView):
    """
      Initiate diagnosis by daphne
      """
    daphne_version = "AT"

    def post(self, request, format=None):
        # Define context and see if it was already defined for this session
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        user_info.dialoguehistory_set.all().delete()

        return Response({
            "result": "Dialogue deleted successfully"
        })
