from dialogue.views import Command
from daphne_context.models import UserInformation, DialogueContext, DialogueContextSerializer
from AT.models import ATContextSerializer


class ATCommand(Command):
    daphne_version = "AT"
    command_options = ['Detection', 'Diagnosis', 'Recommendation']
    condition_names = ['detection', 'diagnosis', 'recommendation']

    def get_current_context(self, user_info: UserInformation):
        context = {}

        # First encode the constant context (visual)
        screen_context_serializer = ATContextSerializer(user_info.atcontext)
        screen_context = screen_context_serializer.data
        context["screen"] = screen_context

        # Then encode the temporal context
        # 1. Get the last 5 DialogueContext
        dialogue_contexts = DialogueContext.objects.order_by("-dialogue_history__date")[:5]
        # 2. Generate the JSON for each of them
        dialogue_contexts_dict = [
            self.generate_at_dialogue_context(dialogue_context) for dialogue_context in dialogue_contexts
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

    def generate_at_dialogue_context(self, dialogue_context: DialogueContext):
        dialogue_context_serializer = DialogueContextSerializer(dialogue_context)
        dialogue_context_dict = dialogue_context_serializer.data
        # if hasattr(dialogue_context, "eossdialoguecontext"):
        #     eossdialogue_context_serializer = EOSSDialogueContextSerializer(dialogue_context.eossdialoguecontext)
        #     engineer_context_serializer = EngineerContextSerializer(dialogue_context.eossdialoguecontext.engineercontext)
        #     dialogue_context_dict["eossdialoguecontext"] = eossdialogue_context_serializer.data
        #     dialogue_context_dict["eossdialoguecontext"]["engineercontext"] = engineer_context_serializer.data
        return dialogue_context_dict
