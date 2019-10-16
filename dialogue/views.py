import datetime
import json
from collections import OrderedDict

import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response

from daphne_brain.nlp_object import nlp
import dialogue.command_processing as command_processing
from auth_API.helpers import get_or_create_user_information
from daphne_context.models import DialogueHistory, AllowedCommand, DialogueContext


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

        # Save user input as part of the dialogue history
        DialogueHistory.objects.create(user_information=user_info,
                                       voice_message=request.data["command"],
                                       visual_message_type="[\"text\"]",
                                       visual_message="[\"" + request.data["command"] + "\"]",
                                       writer="user",
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
            processed_command = nlp(request.data['command'].strip().lower())

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
                    command_processing.choose_command(command_types, self.daphne_version, command_class, user_info)
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
                "writer": piece.writer
            } for piece in last_dialogue
        ]
        dialogue_list.reverse()

        response_json = {
            "dialogue_pieces": dialogue_list
        }

        return Response(response_json)
