from EOSS.models import EOSSContext, EOSSContextSerializer, ActiveContextSerializer, EOSSDialogueContextSerializer, \
    EngineerContextSerializer, EOSSDialogueContext, EngineerContext
from daphne_context.models import UserInformation, DialogueContext, DialogueContextSerializer
from collections import OrderedDict





class ContextClient:

    def __init__(self, user_info):
        self.user_info = user_info
        self.context = {
            'screen': self.build_screen_context(),
            'dialogue': self.build_dialogue_context()
        }

    def build_screen_context(self):
        screen_context = EOSSContextSerializer(self.user_info.eosscontext).data
        screen_context["activecontext"] = ActiveContextSerializer(self.user_info.eosscontext.activecontext).data
        return screen_context

    def build_dialogue_context(self):


        # --> 1. Get last 5 dialogue context entries
        historical_context = DialogueContext.objects.order_by("-dialogue_history__date")[:5]
        if len(historical_context) == 0:
            return {}

        # --> 2. Format historical context and place in dictionary object
        dialogue_contexts = []
        for context in historical_context:
            context_serializer = DialogueContextSerializer(context)
            context_data = context_serializer.data
            if hasattr(context, "eossdialoguecontext"):
                eossdialogue_context_serializer = EOSSDialogueContextSerializer(context.eossdialoguecontext)
                engineer_context_serializer = EngineerContextSerializer(
                    context.eossdialoguecontext.engineercontext)
                context_data["eossdialoguecontext"] = eossdialogue_context_serializer.data
                context_data["eossdialoguecontext"]["engineercontext"] = engineer_context_serializer.data
            dialogue_contexts.append(context_data)

        # --> 3. Return dialogue context (for some reason we are only returning the first context entry)
        return dialogue_contexts[0]







    def create_dialogue_contexts(self):

        # --> 1. Dialogue Context
        dialogue_context = DialogueContext(is_clarifying_input=False)

        # --> 2. EOSS Dialogue Context
        eossdialogue_context = EOSSDialogueContext()

        # --> 3. Engineer Context
        engineer_context = EngineerContext()

        # --> 4. Package into dict
        contexts = OrderedDict()
        contexts["dialogue_context"] = dialogue_context
        contexts["eossdialogue_context"] = eossdialogue_context
        contexts["engineer_context"] = engineer_context
        return contexts


    def save_dialogue_contexts(self, dialogue_contexts, dialogue_history):
        dialogue_contexts["dialogue_context"].dialogue_history = dialogue_history
        dialogue_contexts["dialogue_context"].save()

        dialogue_contexts["eossdialogue_context"].dialoguecontext = dialogue_contexts["dialogue_context"]
        dialogue_contexts["eossdialogue_context"].save()

        dialogue_contexts["engineer_context"].eossdialoguecontext = dialogue_contexts["eossdialogue_context"]
        dialogue_contexts["engineer_context"].save()