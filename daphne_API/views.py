from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import daphne_API.command_processing as command_processing
from daphne_brain.nlp_object import nlp


class Command(APIView):
    """
    Process a command
    """

    def post(self, request, format=None):
        # Preprocess the command
        processed_command = nlp(request.data['command'].strip().lower())

        # Classify the command, obtaining a command type
        command_options = ["iFEED", "VASSAR", "Critic", "Historian"]
        command_types = command_processing.classify_command(processed_command)

        # Define context and see if it was already defined for this session
        if "context" not in request.session:
            request.session["context"] = {}

        if "answers" in request.session["context"]:
            request.session["context"]["answers"] = []
        
        # Act based on the types
        for command_type in command_types:
            if command_options[command_type] == "iFEED":
                request.session["context"]["answers"].append(command_processing.ifeed_command(processed_command))
            if command_options[command_type] == "VASSAR":
                request.session["context"]["answers"].append(command_processing.vassar_command(processed_command))
            if command_options[command_type] == "Critic":
                request.session["context"]["answers"].append(command_processing.critic_command(processed_command))
            if command_options[command_type] == "Historian":
                request.session["context"]["answers"].append(command_processing.historian_command(processed_command))

        response = command_processing.think_response(request.session["context"])
        # If command is to switch modes, send new mode back, if not
        return Response({"response": response})

class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """

    def get(self, request, format=None):
        # List of commands for the general system
        pass

    def post(self, request, format=None):
        # List of commands for a single subsystem
        pass