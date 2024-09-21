import datetime
import json
import re
import sys
import urllib.parse
from collections import OrderedDict

import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response

# from daphne_brain.nlp_object import nlp
# from dialogue.nn_models import nn_models
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
        print("generated")
        session_state['generated'] = []
    # Neo4j database results
    if 'database_results' not in session_state:
        print("database_results")
        session_state['database_results'] = []
    # User input
    if 'user_input' not in session_state:
        print("user_input")
        session_state['user_input'] = []
    # Generated Cypher statements
    if 'cypher' not in session_state:
        print("cypher")
        session_state['cypher'] = []

    def generate_context(self, prompt, context_data='generated'):

        context = []

        print(self.session_state['generated'])
        # If any history exists
        if self.session_state['generated']:
            # Add the last three exchanges
            size = len(self.session_state['generated'])
            for i in range(max(size - 5, 0), size):
                context.append(
                    {'role': 'user', 'content': self.session_state['user_input'][i]})
                context.append(
                    {'role': 'assistant', 'content': self.session_state[context_data][i]})
        print(context)
        # Add the latest user prompt
        context.append({'role': 'user', 'content': str(prompt)})
        return context

    def run_cypher_query(self, graph, query):
        print("555555555555555555555555555555555555555555555555555555555555555555555555555555555555555", query)
        results = graph.query(query)
        return results

    def post(self, request, format=None):
        # Example usage
        try:
            # JSON changes
            load_dotenv()
            os.environ['OPENAI_API_KEY'] = os.getenv('api_key')
            chat = ChatOpenAI(model="ft:gpt-4o-mini-2024-07-18:seak-lab:daphne-third-test:A9i2G8En")

            messages = [
                SystemMessage(
                    content="You are a helpful assistant that helps know if the question is asking about current value or status of something, Answer in Yes or No only"
                ),
                HumanMessage(content=request.data['command']),
            ]

            response = chat(messages)
            print("RESPONSEEEEEEE:", response.content)
            templates = [r"^Check measurement (.+) status$", r"^Check (.+) status$",
                         r"^Show the current value of (.+) measurement$", r"^Show the current value of (.+)$",
                         r"^What is the current value of (.+) measurement$", r"^What is the current value of (.+)$",
                         r"^current value$", r"^What is the value of (.+) measurement currently$",
                         r"^What is the value of (.+) currently$", r"^What is the status of (.+) measurement$",
                         r"^What is the status of (.+)$", r"^status$",r"^What is current value of (.+) measurement$",
                         r"^What is current value of (.+)$", r"^What is status of (.+)$",
                         r"^What is status of (.+) measurement$"]
            flag = False
            for template in templates:
                pattern = re.compile(template, re.IGNORECASE)
                flag = bool(pattern.match(request.data['command']))
                print(flag)
                if flag:
                    response.content = 'Yes'
                    break
            if response.content == 'No':
                raise ValueError("Optional error message")

            sensor_data = json.loads(sim.get_sensor_data())
            print("typee: ", sensor_data)
            spec = JsonSpec(dict_=dict(sensor_data), max_value_length=sys.maxsize)
            toolkit = JsonToolkit(spec=spec)
            agent = create_json_agent(llm=ChatOpenAI(temperature=0, model="ft:gpt-4o-mini-2024-07-18:seak-lab:daphne-third-test:A9i2G8En"), toolkit=toolkit,
                                      max_iterations=sys.maxsize,
                                      verbose=True)
            response = agent.run(request.data['command'])

            return Response({"response": {
                "voice_message": response,
                "visual_message_type": ["text"],
                "visual_message": [response],
                "writer": "daphne"}
            })

        except Exception as e:
            print("Error:", e)
            print("hi: ", request.data['command'])

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
            # chain = GraphCypherQAChain.from_llm(
            #     ChatOpenAI(temperature=0), graph=graph, verbose=True, return_when_no_match=False, return_direct=True
            # )

            chatModel = ChatOpenAI(model="ft:gpt-4o-mini-2024-07-18:seak-lab:daphne-third-test:A9i2G8En")

            print("ques:", request.data['command'])
            #print(chain)
            try:
                temps = [r"^Show the image of component (.+)$", r"^Show the image of (.+)$"]
                image_link = ""
                image_name = ""

                flag1 = False
                for temp in temps:
                    pattern = re.compile(temp, re.IGNORECASE)
                    flag1 = bool(pattern.match(request.data['command']))
                    if flag1:
                        match = re.match(pattern, request.data['command'])
                        if match:
                            image_name = match.group(1)
                            image_name = image_name.replace(" ", "_")

                            encoded_file_path = urllib.parse.quote(
                                os.path.join("home", "ubuntu", "daphne-at-interface", "src", "images",
                                             image_name + ".png"), safe="")
                            image_link = f"https://daphne-at.selva-research.com/api/at/recommendation/figure?filename=%2F{encoded_file_path}"
                            image_name = image_name.replace("_", " ")
                        break
                if flag1:
                    res = "\nHere is the image<br>" + f'<a href="{image_link}" target="_blank">{image_name}</a>'
                    res_voice = "Here is the image you requested"
                    return Response({"response": {
                        "voice_message": res_voice,
                        "visual_message_type": ["text"],
                        "visual_message": [res],
                        "writer": "daphne"}
                    })
                # print(self.generate_context(request.data['command'], 'user_input'))

                # question = {'history' : self.generate_context(request.data['command'], 'user_input'), 'query' : request.data['command']}
                # print(question)
                ques_desc = f"Using this as history of conversation and context {self.generate_context(request.data['command'], 'generated')} answer the following question {request.data['command']}"
                print("QUES_DESC:", ques_desc)
                messagesChatModel = [
                    SystemMessage(
                        content="You are a virtual assistant that helps astronauts when there are spacecraft anomalies and mission control is not available. Astronauts will ask you questions about the anomalies, their signature, the procedures to solve those anomalies, and general questions etc. To answer the questions which need the database data, you can generate a Cypher statement to query a graph database. Use only the provided relationship types and properties in the schema. Do not use any other relationship types or properties that are not provided. If the Cypher query has an empty return, say 'no info available.' If multiple answers exist, mention all. Just list the query results; don't try to frame answers. But if the question does not need data from database, just give the natural language answer. If the question has data from database then give the cypher query only."
                    ),
                    HumanMessage(content=ques_desc),
                ]
                res1 = chatModel(messagesChatModel)
                print("resssssssssssssssssssssssssssssssssssssssssssssssssssss", res1)
                result1 = self.run_cypher_query(graph, res1.content)
                # result1 = chain.run(ques_desc)
                print("6666666666666666666666666666666666666", result1)

                self.session_state['user_input'].append(request.data['command'])
                self.session_state['database_results'].append(str(result1))

                # print(self.session_state['database_results'])
            except Exception as e:
                print('Error:', e)
                if request.data['command'] in self.session_state['user_input']:
                    ind = self.session_state['user_input'].index(request.data['command'])
                    return Response({"response": {
                        "voice_message": "Here is the what I found",
                        "visual_message_type": ["text"],
                        "visual_message": [self.session_state['generated'][ind]],
                        "writer": "daphne"}
                    })
                try:
                    messagesChatModel = [
                        SystemMessage(
                            content="You are a virtual assistant that helps astronauts when there are spacecraft anomalies and mission control is not available. Astronauts will ask you questions about the anomalies, their signature, the procedures to solve those anomalies, and general questions etc. To answer the questions which need the database data, you can generate a Cypher statement to query a graph database. Use only the provided relationship types and properties in the schema. Do not use any other relationship types or properties that are not provided. If the Cypher query has an empty return, say 'no info available.' If multiple answers exist, mention all. Just list the query results; don't try to frame answers. But if the question does not need data from database, just give the natural language answer. If the question has data from database then give the cypher query only."
                        ),
                        HumanMessage(content=request.data['command']),
                    ]
                    # result1 = chain.run(request.data['command'])
                    res1 = chatModel(messagesChatModel)
                    print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii", res1.content)
                    result1 = self.run_cypher_query(graph, res1)
                    print("888888888888888888888888888888888888888", result1)

                    self.session_state['user_input'].append(request.data['command'])
                    self.session_state['database_results'].append(str(result1))
                    # self.session_state['generated'].append(res1.content)
                    # self.generate_context(res1.content, 'generated')
                except Exception as err:
                    chat = ChatOpenAI(model="ft:gpt-4o-mini-2024-07-18:seak-lab:daphne-third-test:A9i2G8En")
                    ques_desc = f"Using this as history of conversation and context {self.generate_context(request.data['command'], 'generated')} answer the following question {request.data['command']}"
                    print("QUES_DESC:", ques_desc)
                    messages = [
                        SystemMessage(
                            content="You are a helpful assistant that helps present cipher query results to human readable form"
                        ),
                        HumanMessage(content=ques_desc),
                    ]
                    response = chat(messages)

                    print("444444444444444444444444444444444444444444444444444444444444")
                    self.session_state['user_input'].append(request.data['command'])
                    self.session_state['generated'].append(response.content)
                    self.generate_context(response.content, 'generated')

                    print(self.session_state)
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

            chat = ChatOpenAI(model="ft:gpt-4o-mini-2024-07-18:seak-lab:daphne-third-test:A9i2G8En")
            ques_desc = f"Using this as history of conversation and context {self.generate_context(request.data['command'], 'generated')} answer the following question {description}"
            print("QUES_DESC:", ques_desc)
            messages = [
                SystemMessage(
                    content="You are a helpful assistant that helps present cipher query results to human readable form, don't write any fullforms, present information as it is in sentences, give line breaks whereever required to improve formatting"
                ),
                HumanMessage(content=description),
            ]

            response = chat(messages)
            print("222222222222222222222222222222222222222222222222222222222222222222")

            response.content = response.content.replace('\n', '<br>')
            print("Yahoo:", response.dict)

            if link_flag == 1:
                response_final = response.content + "\nHere is the link\n" + f'<a href="{"api/at/recommendation/procedure?filename" + pdf_link}" target="_blank">{pdf_name}</a>'

                self.session_state['generated'].append(response_final)
                self.generate_context(response_final, 'generated')

                print(self.session_state)

                return Response({"response": {
                    "voice_message": response.content,
                    "visual_message_type": ["text"],
                    "visual_message": [response_final],
                    "writer": "daphne"}
                })

            self.session_state['generated'].append(response.content)
            self.generate_context(response.content, 'generated')

            # print(self.generate_context(response.content, 'generated'))

            return Response({"response": {
                "voice_message": response.content,
                "visual_message_type": ["text"],
                "visual_message": [response.content],
                "writer": "daphne"}
            })

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
