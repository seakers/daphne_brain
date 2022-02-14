from daphne_brain.nlp_object import nlp

from EOSS.dialogue.data_extractors import extract_function as eoss_extract_function
from EOSS.dialogue.data_processors import process_function as eoss_process_function

# from EDL.dialogue.data_extractors import extract_function as edl_extract_function
# from EDL.dialogue.data_processors import process_function as edl_process_function
#
# from AT.dialogue.data_extractors import extract_function as at_extract_function
# from AT.dialogue.data_processors import process_function as at_process_function



extract_functions = {
    'EOSS': eoss_extract_function,
    # 'EDL': edl_extract_function,
    # 'AT': at_extract_function
}

process_functions = {
    'EOSS': eoss_process_function,
    # 'EDL': edl_process_function,
    # 'AT': at_process_function
}


class Command:


    def __init__(self, command, daphne_version='EOSS'):
        self.cmd = command
        self.cmd_nlp = self._nlp(command)
        self.cmd_clean = self._clean(self.cmd_nlp)

        # --> Default Variable Values
        self.daphne_version = daphne_version
        self.extract_function = extract_functions[daphne_version]
        self.process_function = process_functions[daphne_version]
        self.daphne_roles = ['iFEED', 'VASSAR', 'Critic', 'Historian', 'Teacher']
        self.daphne_conditions = ['analyst', 'engineer', 'critic', 'historian', 'teacher']
        self.create_dialogue_contexts = None
        self.save_dialogue_contexts = None


        # --> Nested dictionary where: self.intent_dict[role][type] = confidence
        self.intent_dict = {}

    def set_create_context_func(self, func):
        self.create_dialogue_contexts = func
        return self

    def set_save_context_func(self, func):
        self.save_dialogue_contexts = func
        return self

    def set_roles(self, daphne_roles):
        self.daphne_roles = daphne_roles
        return self

    def set_version(self, daphne_version):
        self.daphne_version = daphne_version
        return self

    def set_conditions(self, daphne_conditions):
        self.daphne_conditions = daphne_conditions
        return self


    def _nlp(self, command):
        return nlp(command.strip())

    def _clean(self, command):
        tokens = []
        for token in command:
            # If stopword or punctuation, ignore token and continue
            cond1 = token.is_stop
            cond2 = not (
                    token.lemma_ == "which" or token.lemma_ == "how" or token.lemma_ == "what" or token.lemma_ == "when" or token.lemma_ == "why")
            cond3 = token.is_punct
            if cond1 and cond2 or cond3:
                continue

            tokens.append(token.lemma_)
        return " ".join(tokens)


    def add_intent(self, role, types, confidence):
        self.intent_dict[role] = {
            'types': types,
            'confidence': confidence
        }


    def process_intents(self):

        # --> Iterate over intents
        for role, type_dict in self.intent_dict:
            types = type_dict['types']

            # --> Check if type classification meets confidence thresholds
            confidence = type_dict['confidence']
            print('-->', role, 'CONFIDENCE:', confidence)
            if confidence > 0.95:
                self.command_answer(role, types[0])
                # answer command
            elif confidence > 0.90:
                self.command_choice(role, types)
                # give user choice to validate selection
            else:
                self.command_not_answerable(role, types)
                # question is not answerable


    def command_answer(self, role, type):

        # --> 1. Get new dialogue context
        new_context = self.create_dialogue_contexts()


        return 0

    def command_choice(self, role, types):
        return 0

    def command_not_answerable(self, role, types):
        return 0




