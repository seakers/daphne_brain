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
        # Classify the question, obtaining a question type
        command_type, other_info = command_processing.get_command_type(processed_command)
        # If command is to switch modes, send new mode back, if not
        return Response({'response': processed_command.text, 'command_type': command_type, 'other_info': other_info})

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