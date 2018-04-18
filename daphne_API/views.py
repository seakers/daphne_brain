from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import daphne_API.command_processing as command_processing
from daphne_brain.nlp_object import nlp
import daphne_API.command_lists as command_lists
import json
import datetime
from importlib import import_module
from django.conf import settings
from daphne_brain.session_lock import session_lock
from VASSAR_API.api import VASSARClient

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

class Command(APIView):
    """
    Process a command
    """

    def post(self, request, format=None):
        # Preprocess the command
        processed_command = nlp(request.data['command'].strip().lower())

        # Classify the command, obtaining a command type
        command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian', 'EDL']
        command_types = command_processing.classify_command(processed_command)

        # Define context and see if it was already defined for this session
        if 'context' not in request.session:
            request.session['context'] = {}

        if 'data' in request.session:
            request.session['context']['data'] = request.session['data']

        if 'vassar_port' in request.session:
            request.session['context']['vassar_port'] = request.session['vassar_port']

        request.session['context']['answers'] = []

        if 'allowed_commands' in request.data:
            request.session['context']['allowed_commands'] = json.loads(request.data['allowed_commands'])

        # Act based on the types
        for command_type in command_types:
            if command_options[command_type] == 'iFEED':
                request.session['context']['answers'].append(
                    command_processing.ifeed_command(processed_command, request.session['context']))
            if command_options[command_type] == 'VASSAR':
                request.session['context']['answers'].append(
                    command_processing.vassar_command(processed_command, request.session['context']))
            if command_options[command_type] == 'Critic':
                request.session['context']['answers'].append(
                    command_processing.critic_command(processed_command, request.session['context']))
            if command_options[command_type] == 'Historian':
                request.session['context']['answers'].append(
                    command_processing.historian_command(processed_command, request.session['context']))
            if command_options[command_type] == 'EDL':
                request.session['context']['answers'].append(
                    command_processing.EDL_command(processed_command, request.session['context']))

        response = command_processing.think_response(request.session['context'])

        request.session.modified = True

        # If command is to switch modes, send new mode back, if not
        return Response({'response': response})

class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        store = SessionStore(request.session.session_key)
        port = store['vassar_port'] if 'vassar_port' in store else 9090
        vassar_client = VASSARClient(port)
        # List of commands for a single subsystem
        command_list = []
        command_list_request = request.data['command_list']
        restricted_list = None
        if 'restricted_list' in request.data:
            restricted_list = request.data['restricted_list']
        if command_list_request == 'general':
            command_list = command_lists.general_commands_list(restricted_list)
        elif command_list_request == 'datamining':
            command_list = command_lists.datamining_commands_list(restricted_list)
        elif command_list_request == 'analyst':
            command_list = command_lists.analyst_commands_list(restricted_list)
        elif command_list_request == 'critic':
            command_list = command_lists.critic_commands_list(restricted_list)
        elif command_list_request == 'historian':
            command_list = command_lists.historian_commands_list(restricted_list)
        elif command_list_request == 'measurements':
            command_list = command_lists.measurements_list()
        elif command_list_request == 'missions':
            command_list = command_lists.missions_list()
        elif command_list_request == 'technologies':
            command_list = command_lists.technologies_list()
        elif command_list_request == 'space_agencies':
            command_list = command_lists.agencies_list()
        elif command_list_request == 'objectives':
            command_list = command_lists.objectives_list(vassar_client)
        elif command_list_request == 'orb_info':
            command_list = command_lists.orbits_info
        elif command_list_request == 'instr_info':
            command_list = command_lists.instruments_info
        elif command_list_request == 'analyst_instrument_parameters':
            command_list = command_lists.analyst_instrument_parameter_list()
        elif command_list_request == 'analyst_instruments':
            command_list = command_lists.analyst_instrument_list()
        elif command_list_request == 'analyst_measurements':
            command_list = command_lists.analyst_measurement_list()
        elif command_list_request == 'analyst_stakeholders':
            command_list = command_lists.analyst_stakeholder_list()
        return Response({'list': command_list})