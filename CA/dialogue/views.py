import datetime
import json
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
from dialogue.CommandClassifier import CommandClassifier
from dialogue.Command import Command


from concurrent.futures import ProcessPoolExecutor
from asgiref.sync import async_to_sync, sync_to_async
from daphne_brain.utils import _proc
import asyncio


from CA.dialogue.context import ContextClient



# URLS: /api/ca/cacommand

class CACommand(APIView):

    daphne_version = "EOSS"
    command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian', 'Teacher']
    condition_names = ['analyst', 'engineer', 'critic', 'historian', 'teacher']

    def set_allowed_commands(self, user_info, request):

        # --> 1. Delete old allowed commands
        AllowedCommand.objects.filter(user_information__exact=user_info).delete()

        # --> 2. Index current allowed commands
        if 'allowed_commands' in request.data:
            allowed_commands = json.loads(request.data['allowed_commands'])
            for command_type, command_list in allowed_commands.items():
                for command_number in command_list:
                    AllowedCommand.objects.create(user_information=user_info, command_type=command_type,
                                                  command_descriptor=command_number)



    def post(self, request, format=None):
        print('--> PROCESSING CA COMMAND')
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        # --> 1. Save command into DialogueHistory entry
        DialogueHistory.objects.create(user_information=user_info,
                                       voice_message=request.data["command"],
                                       visual_message_type="[\"text\"]",
                                       visual_message="[\"" + request.data["command"] + "\"]",
                                       dwriter="user",
                                       date=datetime.datetime.utcnow())

        # --> 2. Set allowed command info
        self.set_allowed_commands(user_info, request)

        # --> 3. Process command and return
        frontend_response = self.process_command(user_info, request)
        return Response({'response': frontend_response})



    """
         _____                                     _____                                                _ 
        |  __ \                                   / ____|                                              | |
        | |__) |_ __  ___    ___  ___  ___  ___  | |      ___   _ __ ___   _ __ ___    __ _  _ __    __| |
        |  ___/| '__|/ _ \  / __|/ _ \/ __|/ __| | |     / _ \ | '_ ` _ \ | '_ ` _ \  / _` || '_ \  / _` |
        | |    | |  | (_) || (__|  __/\__ \\__ \ | |____| (_) || | | | | || | | | | || (_| || | | || (_| |
        |_|    |_|   \___/  \___|\___||___/|___/  \_____|\___/ |_| |_| |_||_| |_| |_| \__,_||_| |_| \__,_|
                                                                                                
    """

    def process_command(self, user_info, request):
        context_client = ContextClient(user_info)
        context = context_client.context

        # --> 1. Create command object
        command = Command(request.data['command'])
        command = command.set_session(request.session)
        command = command.set_user_info(user_info)
        command = command.set_context_client(context_client)
        command = command.set_roles(self.command_options)
        command = command.set_conditions(self.condition_names)
        command = command.set_version(self.daphne_version)



        # --> 2. Determine if clarifying or answering
        if "is_clarifying_input" in context["dialogue"] and context["dialogue"]["is_clarifying_input"]:
            self.clarify(command, request, context)
        else:
            self.classify(command)


        # --> 3. Get last response inserted to DB and return to user
        db_answer = user_info.dialoguehistory_set.order_by("-date")[:1].get()
        return {
            "voice_message": db_answer.voice_message,
            "visual_message_type": json.loads(db_answer.visual_message_type),
            "visual_message": json.loads(db_answer.visual_message),
            "writer": "daphne",
        }



    def classify(self, command):
        print('--> CLASSIFYING')

        client = CommandClassifier(command)
        client.classify()
        command.process_intents()


    def clarify(self, command, request, context):
        print('--> CLARIFYING')

        # --> Determine: role, type, and condition
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

        # --> Set selected command in command obj
        user_turn = DialogueHistory.objects.filter(dwriter__exact="user").order_by("-date")[1]
        command.set_command(user_turn.voice_message.strip().lower())

        role_index = context["dialogue"]["clarifying_role"]
        role = self.command_options[role_index]
        condition = self.condition_names[role_index]

        # --> Answer command
        command.answer(role, condition, [choice])





class LMCommand(APIView):

    daphne_version = "CA"
    command_options = ['Basics', 'Spacecraft Bus', 'Mission Payloads']
    condition_names = ['Basics', 'Spacecraft Bus', 'Mission Payloads']


    def post(self, request, format=None):
        print('--> PROCESSING LM COMMAND')
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        # --> 1. Save command into DialogueHistory entry
        DialogueHistory.objects.create(user_information=user_info,
                                       voice_message=request.data["command"],
                                       visual_message_type="[\"text\"]",
                                       visual_message="[\"" + request.data["command"] + "\"]",
                                       dwriter="user",
                                       date=datetime.datetime.utcnow())


        # --> 2. Process command and return
        confidence = self.process_command(user_info, request)
        return Response({'response': json.dumps(confidence)})

    """
         _____                                     _____                                                _ 
        |  __ \                                   / ____|                                              | |
        | |__) |_ __  ___    ___  ___  ___  ___  | |      ___   _ __ ___   _ __ ___    __ _  _ __    __| |
        |  ___/| '__|/ _ \  / __|/ _ \/ __|/ __| | |     / _ \ | '_ ` _ \ | '_ ` _ \  / _` || '_ \  / _` |
        | |    | |  | (_) || (__|  __/\__ \\__ \ | |____| (_) || | | | | || | | | | || (_| || | | || (_| |
        |_|    |_|   \___/  \___|\___||___/|___/  \_____|\___/ |_| |_| |_||_| |_| |_| \__,_||_| |_| \__,_|

    """

    def process_command(self, user_info, request):
        context_client = ContextClient(user_info)
        context = context_client.context

        # --> 1. Create command object
        command = Command(request.data['command'])
        command = command.set_session(request.session)
        command = command.set_user_info(user_info)
        command = command.set_context_client(context_client)
        command = command.set_roles(self.command_options)
        command = command.set_conditions(self.condition_names)
        command = command.set_version(self.daphne_version)

        # --> 2. Classify command (no need to process intents)
        client = CommandClassifier(command, daphne_version='CA')
        client.classify(max_role_matches=3)

        # --> 3. Return confidence levels for learning modules and slides
        confidence = client.get_prediction_confidence()
        print('--> CONFIDENCE', confidence)
        return confidence










