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





class NonBlockingCommand(APIView):
    """
    Process a non-blocking command
    - Runs models in async subprocess to maximize CPU utilization while freeing GIL
    """

    daphne_version = ""
    command_options = []
    condition_names = []

    def post(self, request, format=None):


        # --> 1. Get userinfo and current context
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)
        context = self.get_current_context(user_info)


        # --> 2. Save command into dialogue history
        DialogueHistory.objects.create(user_information=user_info,
                                       voice_message=request.data["command"],
                                       visual_message_type="[\"text\"]",
                                       visual_message="[\"" + request.data["command"] + "\"]",
                                       dwriter="user",
                                       date=datetime.datetime.utcnow())


        # --> 3. Set allowed command info
        self.set_allowed_commands(user_info, request)


        # --> 4. Process command
        frontend_response = async_to_sync(self.process_command)(user_info, request, context)
        return Response({'response': frontend_response})



    # --> Sync processing of command in new subprocess

    def process_command(self, user_info, request, context):

        # --> 1. Create command object
        command = Command(request.data['command'])
        command = command.set_roles(self.command_options)
        command = command.set_conditions(self.condition_names)
        command = command.set_version(self.daphne_version)
        command = command.set_create_context_func(self.create_dialogue_contexts)
        command = command.set_save_context_func(self.save_dialogue_contexts)
        command = command.set_user_info(user_info)
        command = command.set_session(request.session)
        command = command.set_current_context(context)


        # --> 2. Determine if clarifying or answering
        if "is_clarifying_input" in context["dialogue"] and context["dialogue"]["is_clarifying_input"]:
            self.clarify(command, request, context)
        else:
            self.classify(command)

        return self.think_response(user_info)

    def clarify(self, command, request, context):

        # --> Determine role, type, and condition for command
        user_choice = request.data['command'].strip().lower()

        types = json.loads(context["dialogue"]["clarifying_commands"])
        if user_choice == "first":
            type = types[0]
        elif user_choice == "second":
            type = types[1]
        elif user_choice == "third":
            type = types[2]
        else:
            type = types[0]

        # --> Set selected command in command obj
        user_turn = DialogueHistory.objects.filter(dwriter__exact="user").order_by("-date")[1]
        command.set_command(user_turn.voice_message.strip().lower())

        role_index = context["dialogue"]["clarifying_role"]
        role = self.command_options[role_index]
        condition = self.condition_names[role_index]

        # --> Answer command
        command.answer(role, condition, type)

    def classify(self, command):
        client = CommandClassifier(command)
        client.classify()
        command.process_intents()

    def think_response(self, user_info):
        # TODO: Make this intelligent, e.g. hook this to a rule based engine
        db_answer = user_info.dialoguehistory_set.order_by("-date")[:1].get()
        frontend_answer = {
            "voice_message": db_answer.voice_message,
            "visual_message_type": json.loads(db_answer.visual_message_type),
            "visual_message": json.loads(db_answer.visual_message),
            "writer": "daphne",
        }
        return frontend_answer



    # --> Mandatory Sync Code

    def get_current_context(self, user_info):
        context = {}
        return context

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

    def create_dialogue_contexts(self):
        dialogue_context = DialogueContext(is_clarifying_input=False)
        contexts = OrderedDict()
        contexts["dialogue_context"] = dialogue_context
        return contexts

    def save_dialogue_contexts(self, dialogue_contexts, dialogue_turn):
        dialogue_contexts["dialogue_context"].dialogue_history = dialogue_turn
        dialogue_contexts["dialogue_context"].save()





class Command(APIView):
    """
    Process a command
    """
    daphne_version = ""
    command_options = []
    condition_names = []

    def post(self, request, format=None):
        # Define context and see if it was already defined for this session
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        # Obtain the merged context
        context = self.get_current_context(user_info)

        print("------------ TESTING")
        print(request.data['command'])
        print(request.data)
        print(request)

        # Save user input as part of the dialogue history
        DialogueHistory.objects.create(user_information=user_info,
                                       voice_message=request.data["command"],
                                       visual_message_type="[\"text\"]",
                                       visual_message="[\"" + request.data["command"] + "\"]",
                                       dwriter="user",
                                       date=datetime.datetime.utcnow())

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
            user_turn = DialogueHistory.objects.filter(dwriter__exact="user").order_by("-date")[1]

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

                command_predictions = command_processing.command_type_predictions(processed_command, self.daphne_version,
                                                                                  command_class)

                # If highest value prediction is over 95%, take that question. If over 90%, ask the user to make sure
                # that is correct by choosing over 3. If less, call BS
                max_value = np.amax(command_predictions)
                if max_value > 0.95:
                    command_type = command_processing.get_top_types(command_predictions, self.daphne_version,
                                                                    command_class, top_number=1)[0]
                    new_dialogue_contexts = self.create_dialogue_contexts()
                    dialogue_turn = command_processing.answer_command(processed_command, command_type, command_class,
                                                                      condition_name, user_info, context,
                                                                      new_dialogue_contexts, request.session)
                    self.save_dialogue_contexts(new_dialogue_contexts, dialogue_turn)
                elif max_value > 0.90:
                    command_types = command_processing.get_top_types(command_predictions, self.daphne_version,
                                                                     command_class, top_number=3)
                    command_processing.choose_command(command_types, self.daphne_version, command_role, command_class,
                                                      user_info)
                else:
                    command_processing.not_answerable(user_info)

        frontend_response = command_processing.think_response(user_info)

        return Response({'response': frontend_response})

    def get_current_context(self, user_info):
        context = {}
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
                "writer": piece.dwriter
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
