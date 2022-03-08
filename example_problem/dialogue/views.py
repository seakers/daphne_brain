import json
from collections import OrderedDict

from rest_framework.views import APIView
from rest_framework.response import Response

from auth_API.helpers import get_or_create_user_information
from daphne_context.models import UserInformation, DialogueContext, DialogueContextSerializer
from dialogue.views import Command, Dialogue, ClearHistory
from example_problem.models import EngineerContext, EngineerContextSerializer, ExampleContextSerializer, ExampleDialogueContext, ExampleDialogueContextSerializer
import example_problem.dialogue.command_lists as command_lists

class ExampleCommand(Command):
    daphne_version = "example_problem"
    command_options = ['Analyst', 'Engineer', 'Explorer', 'Historian', 'Critic'], 
    condition_names = ['analyst', 'engineer', 'explorer', 'historian', 'critic'], 

    def get_current_context(self, user_info: UserInformation):
        context = {}

        # First encode the constant context (visual)
        screen_context_serializer = ExampleContextSerializer(user_info.examplecontext)
        screen_context = screen_context_serializer.data
        context["screen"] = screen_context

        # Then encode the temporal context
        # 1. Get the last 5 DialogueContext
        dialogue_contexts = DialogueContext.objects.order_by("-dialogue_history__date")[:5]
        # 2. Generate the JSON for each of them
        dialogue_contexts_dict = [
            self.generate_example_dialogue_context(dialogue_context) for dialogue_context in dialogue_contexts
        ]
        # 3. Merge the JSONs starting by the newest
        if len(dialogue_contexts_dict) > 0:
            merged_dialogue_contexts = dialogue_contexts_dict[0]
            for idx in range(len(dialogue_contexts_dict)-1):
                # TODO: Implement context merge
                pass
        else:
            merged_dialogue_contexts = {}
        # 4. Add the merged JSON to the context object
        context["dialogue"] = merged_dialogue_contexts
        return context

    def generate_example_dialogue_context(self, dialogue_context: DialogueContext):
        dialogue_context_serializer = DialogueContextSerializer(dialogue_context)
        dialogue_context_dict = dialogue_context_serializer.data
        if hasattr(dialogue_context, "exampledialogue_context"):
            eossdialogue_context_serializer = ExampleDialogueContextSerializer(dialogue_context.exampledialoguecontext)
            engineer_context_serializer = EngineerContextSerializer(dialogue_context.exampledialoguecontext.engineercontext)
            dialogue_context_dict["exampledialogue_context"] = eossdialogue_context_serializer.data
            dialogue_context_dict["exampledialogue_context"]["engineercontext"] = engineer_context_serializer.data
        return dialogue_context_dict

    def create_dialogue_contexts(self):
        dialogue_context = DialogueContext(is_clarifying_input=False)
        eossdialogue_context = ExampleDialogueContext()
        engineer_context = EngineerContext()
        contexts = OrderedDict()
        contexts["dialogue_context"] = dialogue_context
        contexts["exampledialogue_context"] = eossdialogue_context
        contexts["engineer_context"] = engineer_context
        return contexts

    def save_dialogue_contexts(self, dialogue_contexts, dialogue_turn):
        dialogue_contexts["dialogue_context"].dialogue_history = dialogue_turn
        dialogue_contexts["dialogue_context"].save()
        dialogue_contexts["exampledialogue_context"].dialoguecontext = dialogue_contexts["dialogue_context"]
        dialogue_contexts["exampledialogue_context"].save()
        dialogue_contexts["engineer_context"].exampledialoguecontext = dialogue_contexts["exampledialogue_context"]
        dialogue_contexts["engineer_context"].save()


class ExampleHistory(Dialogue):
    daphne_version = "example_problem"


class ExampleClearHistory(ClearHistory):
    daphne_version = "example_problem"


class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'example_problem')
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

        return Response({'list': command_list})
