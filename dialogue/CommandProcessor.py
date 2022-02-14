import json
import os
from dialogue.errors import ParameterMissingError


class CommandProcessor:

    def __init__(self, user_info, command, role, condition, type, daphne_version):
        self.user_info = user_info
        self.command = command
        self.role = role
        self.condition = condition
        self.type = type
        self.daphne_version = daphne_version


        self.command_info = self.load_command_info()


    @property
    def not_allowed_cmd(self):
        return {
            'voice_answer': 'This command is restricted right now.',
            'visual_answer_type': ['text'],
            'visual_answer': ['This command is restricted right now.']
        }

    @property
    def extract_function(self):
        if self.daphne_version == "EOSS":
            from EOSS.dialogue.data_extractors import extract_function
            return extract_function
        if self.daphne_version == "EDL":
            from EDL.dialogue.data_extractors import extract_function
            return extract_function
        if self.daphne_version == "AT":
            from AT.dialogue.data_extractors import extract_function
            return extract_function

    @property
    def process_function(self):
        if self.daphne_version == "EOSS":
            from EOSS.dialogue.data_processors import process_function
            return process_function
        if self.daphne_version == "EDL":
            from EDL.dialogue.data_processors import process_function
            return process_function
        if self.daphne_version == "AT":
            from AT.dialogue.data_processors import process_function
            return process_function





    def validate(self):
        if len(self.user_info.allowedcommand_set.all()) == 0:
            return False
        for allowed_command in self.user_info.allowedcommand_set.all():
            if self.condition == allowed_command.command_type and str(self.type) == str(
                    allowed_command.command_descriptor):
                return False


    def load_command_info(self):
        type_info_file = os.path.join(os.getcwd(), self.daphne_version, "dialogue", "command_types", self.role,
                                      str(self.type) + '.json')
        with open(type_info_file, 'r') as file:
            type_info = json.load(file)
        information = {}
        information["type"] = type_info["type"]
        information["params"] = type_info["params"]
        information["objective"] = type_info["objective"]
        if type_info["type"] == "db_query":
            information["query"] = type_info["query"]
        elif type_info["type"] == "run_function":
            information["function"] = type_info["function"]
        information["voice_response"] = type_info["voice_response"]
        information["visual_response"] = type_info["visual_response"]
        return information

    def extract_data(self):
        params = self.command_info['params']
        number_of_features = {}
        extracted_raw_data = {}
        extracted_data = {}

        for param in params:
            if not param["from_context"]:
                if param["type"] in number_of_features:
                    number_of_features[param["type"]] += 1
                else:
                    number_of_features[param["type"]] = 1

        for type, num in number_of_features.items():
            extracted_raw_data[type] = self.extract_function[type](self.command, num, self.user_info)

        for param in params:
            extracted_param = None
            if param["from_context"]:
                subcontext = context
                if len(param["context_path"]) > 0:
                    for step in param["context_path"]:
                        subcontext = subcontext[step]
                if param["name"] in subcontext:
                    extracted_param = subcontext[param["name"]]
                else:
                    if param["mandatory"]:
                        raise ParameterMissingError(param["type"])
            else:
                if len(extracted_raw_data[param["type"]]) > 0:
                    extracted_param = extracted_raw_data[param["type"]].pop(0)
                elif param["mandatory"]:
                    # If param is needed but not detected return error with type of parameter
                    raise ParameterMissingError(param["type"])
            if extracted_param is not None:
                extracted_data[param["name"]] = self.process_function[param["type"]](extracted_param, param["options"],
                                                                                self.user_info)
        return extracted_data

    def run(self):

        # --> 1. Validate Command
        if self.validate() is False:
            return self.not_allowed_cmd

        # --> 2. Load Command Info
        command_info = self.load_command_info()





