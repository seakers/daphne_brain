from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import daphne_API.command_processing as command_processing
from daphne_brain.nlp_object import nlp
import daphne_API.command_lists as command_lists
import json
import datetime

class Command(APIView):
    """
    Process a command
    """

    def post(self, request, format=None):
        # Preprocess the command
        processed_command = nlp(request.data['command'].strip().lower())

        # Classify the command, obtaining a command type
        command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian']
        command_types = command_processing.classify_command(processed_command)

        # Define context and see if it was already defined for this session
        if 'context' not in request.session:
            request.session['context'] = {}
                
        request.session['context']['data'] = request.session['data']    
        request.session['context']['answers'] = []

        request.session['context']['experiment_stage'] = 0
        if 'experiment' in request.session:
            if 'start_date2' in request.session['experiment']:
                request.session['context']['experiment_stage'] = 2
            else:
                request.session['context']['experiment_stage'] = 1
        
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

        response = command_processing.think_response(request.session['context'])

        # save data for experiment
        if 'experiment' in request.session:
            if 'start_date2' not in request.session['experiment']:
                dialog = 'dialog1'
            else:
                dialog = 'dialog2'
            request.session['experiment'][dialog].append({
                'question': processed_command.text,
                'answer': response,
                'time': datetime.datetime.utcnow().isoformat()
            })

        request.session.modified = True

        # If command is to switch modes, send new mode back, if not
        return Response({'response': response})


class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        # List of commands for a single subsystem
        command_list = []
        command_list_request = request.data['command_list']
        if command_list_request == 'general':
            command_list = command_lists.general_commands
        elif command_list_request == 'datamining':
            command_list = command_lists.datamining_commands
        elif command_list_request == 'analyst':
            command_list = command_lists.analyst_commands
        elif command_list_request == 'critic':
            command_list = command_lists.critic_commands
        elif command_list_request == 'historian':
            command_list = command_lists.historian_commands
        elif command_list_request == 'measurements':
            command_list = command_lists.measurements_list()
        elif command_list_request == 'missions':
            command_list = command_lists.missions_list()
        elif command_list_request == 'technologies':
            command_list = command_lists.technologies_list()
        elif command_list_request == 'objectives':
            command_list = command_lists.objectives_list()
        elif command_list_request == 'orb_alias':
            command_list = command_lists.orbits_alias
        elif command_list_request == 'instr_alias':
            command_list = command_lists.instruments_alias
        return Response({'list': command_list})
