import datetime
import json
import re
import urllib.parse
from collections import OrderedDict

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
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


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

    def post(self, request, format=None):
        # Example usage
        print("hi: ", request.data['command'])
        templates = [r"^Check measurement (.+) status$", r"^Check (.+) status$",
                     r"^Show the current value of (.+) measurement$", r"^Show the current value of (.+)$",
                     r"^Show the image of component (.+)$", r"^Show the image of (.+)$",
                     r"^Read steps of procedure (.+)", r"^Read steps of (.+)", "Next", "previous", "Repeat",
                     "Previous", "next", "repeat"]
        flag = False
        for template in templates:
            pattern = re.compile(template, re.IGNORECASE)
            flag = bool(pattern.match(request.data['command']))
            print(flag)
            if flag:
                break
        if flag == False:
            # langchain changes
            graph = Neo4jGraph(
                url="bolt://13.58.54.49:7687",
                username="neo4j",
                password="goSEAKers!"
            )

            # os.environ['OPENAI_API_KEY'] = "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"
            # os.environ['OPENAI_API_KEY'] = "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"
            load_dotenv()
            os.environ['OPENAI_API_KEY'] = os.getenv('api_key')
            print("HERE")
            chain = GraphCypherQAChain.from_llm(
                ChatOpenAI(temperature=0), graph=graph, verbose=True, return_when_no_match=False, return_direct=True
            )

            CYPHER_GENERATION_TEMPLATE = """
    
                            Task:Generate Cypher statement to query a graph database.
    
                            Instructions:
                            You are a virtual assistant that helps astronauts when there are spacecraft anomalies and 
                            mission control is not available. Astronauts will ask you questions about the anomalies, 
                            their signature, the procedures to solve those anomalies, etc. To answer these questions, 
                            you can generate a Cypher statement to query a graph database.
                            
                            Use only the provided relationship types and properties in the schema.
                            Do not use any other relationship types or properties that are not provided.
                            If the cipher query has empty return say no info available.
                            If multiple answers exists mention all.
                            Just list the query results don't try to frame answers.
    
                            Schema:
                            {schema}
    
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
                            # how long will it take to complete fuel cell maintenance. Mention all times with correspnding procesdures, give the higher value first
                            MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                            WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'Biological Filter Saturation') AS similarity, procedure
                            WHERE similarity > 0.85
                            RETURN procedure.ETR
    
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
    
                            # read steps of procedure 3.109
                            MATCH (procedure:Procedure)-[:Has]->(step:Step)
                            WHERE procedure.pNumber = '3.109'
                            RETURN step.Title, step.Action
    
                            # how long will it take to solve wrs off nominal ph level.
                            MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                            WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'WRS Off Nominal pH Level') AS similarity, procedure
                            WHERE similarity > 0.85
                            RETURN procedure.ETR, procedure.Title, procedure.pNumber
    
                            # What are the procedures for cdra failure
                            MATCH (anomaly:Anomaly)-[:Solution]->(procedure:Procedure)
                            WITH apoc.text.sorensenDiceSimilarity(anomaly.Name,'CDRA Failure') AS similarity, procedure
                            WHERE similarity > 0.85
                            RETURN procedure.Title, procedure.pNumber
    
                            Note: answer the question like -> The title of the procedure is "CDRA Zeolite Filter Swapout" and the procedure number is 3.104.
    
                            # read steps cdra zeolite filter swap out
                            MATCH (procedure:Procedure)-[:Has]->(s)
                            WHERE procedure.Title = 'CDRA Zeolite Filter Swapout'
                            RETURN step.Title, step.Action
                            ORDER BY step.Step,step.Substep,step.SubSubStep
    
                            Note: always check all nodes connected through has relationship
    
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
                            The question is:
                            {question}"""

            CYPHER_GENERATION_PROMPT = PromptTemplate(
                input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
            )

            chain = GraphCypherQAChain.from_llm(
                ChatOpenAI(temperature=0, model="gpt-3.5-turbo"), graph=graph, verbose=True,
                cypher_prompt=CYPHER_GENERATION_PROMPT, return_direct=True
            )
            print(request.data['command'])
            print(chain)
            try:
                result1 = chain.run(request.data['command'])
            except Exception as e:
                chat = ChatOpenAI()

                messages = [
                    SystemMessage(
                        content="You are a helpful assistant that helps present cipher query results to human readable form"
                    ),
                    HumanMessage(content=request.data['command']),
                ]

                response = chat(messages)
                return Response({"response": {
                    "voice_message": response.content,
                    "visual_message_type": ["text"],
                    "visual_message": [response.content],
                    "writer": "daphne"}
                })

            folder_path = os.path.join("./", "AT", "databases", "procedures")
            # folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
            desired_string = 'Title'
            matching_keys = []
            if len(result1) > 0:
                matching_keys = [key for key in result1[0].keys() if desired_string in key]
                print("matching_keys ", matching_keys)
            link_flag = 0
            file_path = ""
            pdf_link = None
            pdf_name = None
            for key in matching_keys:
                value = result1[0].get(key, 'Key not found')
                print("VALUE: " + value)
                print(os.path.join(folder_path, value + ".pdf"))

                if os.path.exists(os.path.join(folder_path, value + ".pdf")):
                    file_path = os.path.join(folder_path, value + ".pdf")
                    print("File_PATH ", file_path)
                    procedure_pdfs = os.listdir(folder_path)
                    print("PP:", procedure_pdfs)
                    if value + ".pdf" in procedure_pdfs:
                        pdf_name = value + ".pdf"
                        folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
                        filepath = os.path.join(folder_path, pdf_name)
                        path = os.path.join(os.getcwd(), "AT", "databases", "procedures", pdf_name)
                        pdf_link = urllib.parse.urlencode({"": path})
                        print("res[0]: ", result1[0])
                        link_flag = 1

            # Create a descriptive string
            response = ""
            result_string = ", ".join(str(item) if isinstance(item, dict) else item for item in result1)
            print("RS:", result_string)
            print("RES:", result1)
            description = "No Results Found"
            if result1:
                description = "{} present the information in human readable form".format(
                    result_string)
            # Just list the above information as bullet-points without additional text
            # Print or use the description as needed
            print("Description:", description)
            # conversation.run(description)

            chat = ChatOpenAI()

            messages = [
                SystemMessage(
                    content="You are a helpful assistant that helps present cipher query results to human readable form"
                ),
                HumanMessage(content=description),
            ]

            response = chat(messages)
            # print("Yahoo:", response.dict)

            if link_flag == 1:
                response.content = response.content + "\nHere is the link\n" + f'<a href="{"api/at/recommendation/procedure?filename" + pdf_link}" target="_blank">{pdf_name}</a>'
            return Response({"response": {
                "voice_message": response.content,
                "visual_message_type": ["text"],
                "visual_message": [response.content],
                "writer": "daphne"}
            })

        # End of langchain changes
        else:
            # Define context and see if it was already defined for this session

            user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

            # Obtain the merged context
            context = self.get_current_context(user_info)

            # Save user input as part of the dialogue history
            DialogueHistory.objects.create(user_information=user_info,
                                           voice_message=request.data["command"],
                                           visual_message_type="[\"text\"]",
                                           visual_message="[\"" + request.data["command"] + "\"]",
                                           writer="user",
                                           date=datetime.datetime.utcnow())

            print("hi: ", request.data)

            # Experiment-specific code to limit what can be asked to Daphne
            AllowedCommand.objects.filter(user_information__exact=user_info).delete()

            if 'allowed_commands' in request.data:
                allowed_commands = json.loads(request.data['allowed_commands'])
                for command_type, command_list in allowed_commands.items():
                    for command_number in command_list:
                        AllowedCommand.objects.create(user_information=user_info, command_type=command_type,
                                                      command_descriptor=command_number)

            # If this a choice between three options, check the one the user chose and go on with that
            if "is_clarifying_input" in context["dialogue"] and context["dialogue"]["is_clarifying_input"]:
                user_choice = request.data['command'].strip().lower()
                choices = json.loads(context["dialogue"]["clarifying_commands"])
                if user_choice == "first":
                    choice = choices[0]
                elif user_choice == "second":
                    choice = choices[1]
                elif user_choice == "third":
                    choice = choices[2]
                else:
                    choice = choices[0]
                user_turn = DialogueHistory.objects.filter(writer__exact="user").order_by("-date")[1]

                # Preprocess the command
                processed_command = nlp(user_turn.voice_message.strip().lower())

                role_index = context["dialogue"]["clarifying_role"]
                command_class = self.command_options[role_index]
                condition_name = self.condition_names[role_index]

                new_dialogue_contexts = self.create_dialogue_contexts()
                dialogue_turn = command_processing.answer_command(processed_command, choice, command_class,
                                                                  condition_name, user_info, context,
                                                                  new_dialogue_contexts, request.session)
                self.save_dialogue_contexts(new_dialogue_contexts, dialogue_turn)

            else:
                # Preprocess the command
                processed_command = nlp(request.data['command'].strip())

                # Classify the command, obtaining a command type
                command_roles = command_processing.classify_command_role(processed_command, self.daphne_version)

                # Act based on the types
                for command_role in command_roles:
                    command_class = self.command_options[command_role]
                    condition_name = self.condition_names[command_role]

                    command_predictions = command_processing.command_type_predictions(processed_command,
                                                                                      self.daphne_version,
                                                                                      command_class)

                    # If highest value prediction is over 95%, take that question. If over 90%, ask the user to make sure
                    # that is correct by choosing over 3. If less, call BS
                    max_value = np.amax(command_predictions)
                    if max_value > 0.95:
                        command_type = command_processing.get_top_types(command_predictions, self.daphne_version,
                                                                        command_class, top_number=1)[0]
                        new_dialogue_contexts = self.create_dialogue_contexts()
                        dialogue_turn = command_processing.answer_command(processed_command, command_type,
                                                                          command_class,
                                                                          condition_name, user_info, context,
                                                                          new_dialogue_contexts, request.session)
                        self.save_dialogue_contexts(new_dialogue_contexts, dialogue_turn)
                    elif max_value > 0.90:
                        command_types = command_processing.get_top_types(command_predictions, self.daphne_version,
                                                                         command_class, top_number=3)
                        command_processing.choose_command(command_types, self.daphne_version, command_role,
                                                          command_class,
                                                          user_info)
                    else:
                        command_processing.not_answerable(user_info)

            frontend_response = command_processing.think_response(user_info)

            return Response({'response': frontend_response})

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
