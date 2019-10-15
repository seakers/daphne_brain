from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
import EOSS.dialogue.command_lists as command_lists
from dialogue.views import Command


class EOSSCommand(Command):
    daphne_version = "EOSS"
    command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian']
    condition_names = ['ifeed', 'analyst', 'critic', 'historian']


class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        port = user_info.eosscontext.vassar_port
        vassar_client = VASSARClient(port)
        problem = user_info.eosscontext.problem
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
            command_list = command_lists.objectives_list(vassar_client, problem)
        elif command_list_request == 'orb_info':
            command_list = command_lists.orbits_info(problem)
        elif command_list_request == 'instr_info':
            command_list = command_lists.instruments_info(problem)
        elif command_list_request == 'analyst_instrument_parameters':
            command_list = command_lists.analyst_instrument_parameter_list(problem)
        elif command_list_request == 'analyst_instruments':
            command_list = command_lists.analyst_instrument_list(problem)
        elif command_list_request == 'analyst_measurements':
            command_list = command_lists.analyst_measurement_list(problem)
        elif command_list_request == 'analyst_stakeholders':
            command_list = command_lists.analyst_stakeholder_list(problem)
        return Response({'list': command_list})
