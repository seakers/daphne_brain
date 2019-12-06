import json
from collections import OrderedDict

from django.core import serializers
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.models import EOSSContext, EOSSContextSerializer, ActiveContextSerializer, EOSSDialogueContextSerializer, \
    EngineerContextSerializer, EOSSDialogueContext, EngineerContext
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
import EOSS.dialogue.command_lists as command_lists
from daphne_context.models import UserInformation, DialogueContext, DialogueContextSerializer
from dialogue.views import Command, Dialogue, ClearHistory


class EOSSCommand(Command):
    daphne_version = "EOSS"
    command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian']
    condition_names = ['analyst', 'engineer', 'critic', 'historian']

    def get_current_context(self, user_info: UserInformation):
        context = {}

        # First encode the constant context (visual)
        screen_context_serializer = EOSSContextSerializer(user_info.eosscontext)
        active_context_serializer = ActiveContextSerializer(user_info.eosscontext.activecontext)
        screen_context = screen_context_serializer.data
        screen_context["activecontext"] = active_context_serializer.data
        context["screen"] = screen_context

        # Then encode the temporal context
        # 1. Get the last 5 DialogueContext
        dialogue_contexts = DialogueContext.objects.order_by("-dialogue_history__date")[:5]
        # 2. Generate the JSON for each of them
        dialogue_contexts_dict = [
            self.generate_eoss_dialogue_context(dialogue_context) for dialogue_context in dialogue_contexts
        ]
        # 3. Merge the JSONs starting by the newest
        if len(dialogue_contexts_dict) > 0:
            merged_dialogue_contexts = dialogue_contexts_dict[0]
            for idx in range(len(dialogue_contexts_dict)-1):
                pass
        else:
            merged_dialogue_contexts = {}
        # 4. Add the merged JSON to the context object
        context["dialogue"] = merged_dialogue_contexts
        return context

    def generate_eoss_dialogue_context(self, dialogue_context: DialogueContext):
        dialogue_context_serializer = DialogueContextSerializer(dialogue_context)
        dialogue_context_dict = dialogue_context_serializer.data
        if hasattr(dialogue_context, "eossdialoguecontext"):
            eossdialogue_context_serializer = EOSSDialogueContextSerializer(dialogue_context.eossdialoguecontext)
            engineer_context_serializer = EngineerContextSerializer(dialogue_context.eossdialoguecontext.engineercontext)
            dialogue_context_dict["eossdialoguecontext"] = eossdialogue_context_serializer.data
            dialogue_context_dict["eossdialoguecontext"]["engineercontext"] = engineer_context_serializer.data
        return dialogue_context_dict

    def create_dialogue_contexts(self):
        dialogue_context = DialogueContext(is_clarifying_input=False)
        eossdialogue_context = EOSSDialogueContext()
        engineer_context = EngineerContext()
        contexts = OrderedDict()
        contexts["dialogue_context"] = dialogue_context
        contexts["eossdialogue_context"] = eossdialogue_context
        contexts["engineer_context"] = engineer_context
        return contexts

    def save_dialogue_contexts(self, dialogue_contexts, dialogue_turn):
        dialogue_contexts["dialogue_context"].dialogue_history = dialogue_turn
        dialogue_contexts["dialogue_context"].save()
        dialogue_contexts["eossdialogue_context"].dialoguecontext = dialogue_contexts["dialogue_context"]
        dialogue_contexts["eossdialogue_context"].save()
        dialogue_contexts["engineer_context"].eossdialoguecontext = dialogue_contexts["eossdialogue_context"]
        dialogue_contexts["engineer_context"].save()


class EOSSHistory(Dialogue):
    daphne_version = "EOSS"


class EOSSClearHistory(ClearHistory):
    daphne_version = "EOSS"


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
        elif command_list_request == 'engineer':
            command_list = command_lists.engineer_commands_list(restricted_list)
        elif command_list_request == 'analyst':
            command_list = command_lists.analyst_commands_list(restricted_list)
        elif command_list_request == 'explorer':
            command_list = command_lists.explorer_commands_list(restricted_list)
        elif command_list_request == 'historian':
            command_list = command_lists.historian_commands_list(restricted_list)
        elif command_list_request == 'critic':
            command_list = command_lists.critic_commands_list(restricted_list)

        elif command_list_request == 'orb_info':
            command_list = command_lists.orbits_info(problem)
        elif command_list_request == 'instr_info':
            command_list = command_lists.instruments_info(problem)

        elif command_list_request == 'engineer_instruments':
            command_list = command_lists.engineer_instrument_list(problem)
        elif command_list_request == 'engineer_instrument_parameters':
            command_list = command_lists.engineer_instrument_parameter_list(problem)
        elif command_list_request == 'engineer_measurements':
            command_list = command_lists.engineer_measurement_list(problem)
        elif command_list_request == 'engineer_stakeholders':
            command_list = command_lists.engineer_stakeholder_list(problem)
        elif command_list_request == 'engineer_objectives':
            command_list = command_lists.engineer_objectives_list(vassar_client, problem)
        elif command_list_request == 'engineer_subobjectives':
            command_list = command_lists.engineer_subobjectives_list(vassar_client, problem)

        elif command_list_request == 'historian_measurements':
            command_list = command_lists.historian_measurements_list()
        elif command_list_request == 'historian_missions':
            command_list = command_lists.historian_missions_list()
        elif command_list_request == 'historian_technologies':
            command_list = command_lists.historian_technologies_list()
        elif command_list_request == 'historian_space_agencies':
            command_list = command_lists.historian_agencies_list()

        return Response({'list': command_list})
