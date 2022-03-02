import os
import json
import datetime
from string import Template


from daphne_brain.nlp_object import nlp
from dialogue.errors import ParameterMissingError
from daphne_context.models import UserInformation, DialogueHistory, DialogueContext
from sqlalchemy.orm import sessionmaker


from EOSS.vassar.api import VASSARClient
from EOSS.models import EOSSContext







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
        self.user_info = None
        self.session = None
        self.current_context = None


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

    def set_user_info(self, user_info):
        self.user_info = user_info
        return self

    def set_current_context(self, current_context):
        self.current_context = current_context
        return self

    def set_session(self, session):
        self.session = session
        return self

    def set_command(self, command):
        self.cmd = command
        self.cmd_nlp = self._nlp(command)
        self.cmd_clean = self._clean(self.cmd_nlp)

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


    """
     __  __                                          
    |  \/  |                                         
    | \  / |  ___  ___  ___   __ _   __ _   ___  ___ 
    | |\/| | / _ \/ __|/ __| / _` | / _` | / _ \/ __|
    | |  | ||  __/\__ \\__ \| (_| || (_| ||  __/\__ \
    |_|  |_| \___||___/|___/ \__,_| \__, | \___||___/
                                     __/ |           
                                    |___/         
    """

    @property
    def msg_restricted(self):
        return {
            'voice_answer': 'This command is restricted right now.',
            'visual_answer_type': ['text'],
            'visual_answer': ['This command is restricted right now.']
        }

    @property
    def msg_choice(self):
        return {
            'voice_answer': 'I\'m not confident enough in my interpretation of your question. Please help me by choosing'
                            ' what you are trying to accomplish from the following options.',
            'visual_answer_type': ['list'],
            'visual_answer': [{
                "begin": 'I\'m not confident enough in my interpretation of your question. Please help me by choosing'
                         ' what you are trying to accomplish from the following options. You can either click on the '
                         'objective or type first/second/third',
                "list": []
            }]
        }

    @property
    def msg_non_answerable(self):
        return {
            'voice_answer': 'I don\'t understand your command. Please rephrase it.',
            'visual_answer_type': ['text'],
            'visual_answer': ['I don\'t understand your command. Please rephrase it.']
        }

    def msg_error(self, objective, missing_param):
        return {
            'voice_answer': 'Sorry, but I can\'t answer your question. I interpreted that you are trying to ' + objective +
                            '. I can\'t do this because a ' + missing_param + ' parameter doesn\'t have a valid value. If '
                                                                              'you think I\'m not doing the correct thing, please report this to someone.',
            'visual_answer_type': ['text'],
            'visual_answer': [
                'Sorry, but I can\'t answer your question. I interpreted that you are trying to ' + objective +
                '. I can\'t do this because a ' + missing_param + ' parameter doesn\'t have a valid value. If '
                                                                  'you think I\'m not doing the correct thing, please report this to someone.']
        }




    """
     _____         _                _     _____                                   _               
    |_   _|       | |              | |   |  __ \                                 (_)              
      | |   _ __  | |_  ___  _ __  | |_  | |__) |_ __  ___    ___  ___  ___  ___  _  _ __    __ _ 
      | |  | '_ \ | __|/ _ \| '_ \ | __| |  ___/| '__|/ _ \  / __|/ _ \/ __|/ __|| || '_ \  / _` |
     _| |_ | | | || |_|  __/| | | || |_  | |    | |  | (_) || (__|  __/\__ \\__ \| || | | || (_| |
    |_____||_| |_| \__|\___||_| |_| \__| |_|    |_|   \___/  \___|\___||___/|___/|_||_| |_| \__, |
                                                                                             __/ |
                                                                                            |___/     
    """

    def add_intent(self, role, types, confidence):

        # --> 1. Get command condition
        condition = ''
        for idx, enum_role in enumerate(self.daphne_roles):
            if role == enum_role:
                condition = self.daphne_conditions[idx]

        # --> 2. Add to intent dictionary
        self.intent_dict[role] = {
            'types': types,
            'confidence': confidence,
            'condition': condition
        }

    def process_intents(self):

        # --> Iterate over intents
        for role, type_dict in self.intent_dict:
            types = type_dict['types']
            condition = type_dict['condition']

            # --> Check if type classification meets confidence thresholds
            confidence = type_dict['confidence']
            print('-->', role, 'CONFIDENCE:', confidence)
            if confidence > 0.95:
                self.answer(role, condition, types)
            elif confidence > 0.90:
                self.give_choice(role, condition, types)
            else:
                self.not_answerable()

    """                                        
         /\                                     
        /  \    _ __   ___ __      __ ___  _ __ 
       / /\ \  | '_ \ / __|\ \ /\ / // _ \| '__|
      / ____ \ | | | |\__ \ \ V  V /|  __/| |   
     /_/    \_\|_| |_||___/  \_/\_/  \___||_|   
                                            
    """


    def answer(self, role, condition, types):

        # --> 1. Get new dialogue context (type: dict)
        new_context = self.create_dialogue_contexts()

        # --> 2. Formulate response
        response = self.formulate_response(role, condition, types)

        # --> 3. Index response into dialogue database and return
        dialogue_turn = DialogueHistory.objects.create(user_information=self.user_info,
                                                          voice_message=response["voice_answer"],
                                                          visual_message_type=json.dumps(response["visual_answer_type"]),
                                                          visual_message=json.dumps(response["visual_answer"]),
                                                          dwriter="daphne",
                                                          date=datetime.datetime.utcnow())

        # --> 4. Save dialogue contexts
        self.save_dialogue_contexts(new_context, dialogue_turn)

    def formulate_response(self, role, condition, types):

        # --> 1. Validate command
        if not self._validate(condition, types[0]):
            return self.msg_restricted

        # --> 2. Get intent info dict
        intent_info = self.get_intent_info(role, types[0])

        # --> 3. Get dict containing extracted command parameters
        try:
            command_data = self.extract_intent_features(intent_info)
        except ParameterMissingError as error:
            print(error)
            return self.msg_error(intent_info["objective"], error.missing_param)

        # --> 4. Augment data
        command_data = self.augment_data(command_data)

        # --> 5. Execute intent queries / functions
        if intent_info['type'] == 'db_query':
            exec_result = self.intent_query(intent_info, command_data, role)
        elif intent_info["type"] == "run_function":
            exec_result = self.intent_func(intent_info, command_data)
        else:
            raise ValueError("JSON format not supported!")

        # --> 6. Build answers
        return self.build_answers(intent_info, command_data, exec_result)


    def _validate(self, condition, type):
        # Validates command on
        # 1. command condition
        # 2. command type
        if len(self.user_info.allowedcommand_set.all()) == 0:
            return False
        for allowed_command in self.user_info.allowedcommand_set.all():
            if condition == allowed_command.command_type and type == str(allowed_command.command_descriptor):
                return False
        return True


    def get_intent_info(self, role, type):
        intent_file = os.path.join(os.getcwd(), self.daphne_version, "dialogue", "command_types", role,
                                  str(type) + '.json')
        with open(intent_file, 'r') as file:
            type_info = json.load(file)
        intent_info = {}
        intent_info["type"] = type_info["type"]
        if type_info["type"] == "db_query":
            intent_info["query"] = type_info["query"]
        elif type_info["type"] == "run_function":
            intent_info["function"] = type_info["function"]
        intent_info["params"] = type_info["params"]
        intent_info["objective"] = type_info["objective"]
        intent_info["voice_response"] = type_info["voice_response"]
        intent_info["visual_response"] = type_info["visual_response"]
        return intent_info

    def extract_intent_features(self, intent_info):
        """ Extract the features from the processed question, with a correcting factor """

        # --> 1. Create dict mapping expected command parameters to the # times expected
        # - e.x. { 'mission': 2 } -> the command template expects two mission names to be in the user command
        number_of_features = {}
        for param in intent_info['params']:
            if not param["from_context"]:
                if param["type"] in number_of_features:
                    number_of_features[param["type"]] += 1
                else:
                    number_of_features[param["type"]] = 1

        # --> 2. Create dict mapping expected command parameters to matched command words
        # - e.x. { 'mission': ['SMAP', 'Landsat'] }
        extracted_raw_data = {}
        for type, num in number_of_features.items():
            extracted_raw_data[type] = self.extract_function[type](self.cmd_nlp, num, self.user_info)

        # --> For each parameter, check if it's needed and apply postprocessing;
        extracted_data = {}
        for param in intent_info['params']:
            extracted_param = None
            if param["from_context"]:
                subcontext = self.current_context
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

    def augment_data(self, command_data):
        command_data['now'] = datetime.datetime.utcnow()
        command_data['session_key'] = self.session.session_key
        if self.daphne_version == "EOSS":
            eoss_context: EOSSContext = self.user_info.eosscontext
            vassar_client = VASSARClient(user_information=self.user_info)
            command_data['designs'] = vassar_client.get_dataset_architectures(problem_id=eoss_context.problem_id,
                                                                              dataset_id=eoss_context.dataset_id)
            command_data['group_id'] = eoss_context.group_id
            command_data['problem_id'] = eoss_context.problem_id
            command_data['dataset_id'] = eoss_context.dataset_id

            if 'context' in self.session:
                if 'behavioral' in self.session['context']:
                    command_data['behavioral'] = self.session['context']['behavioral']
                if 'non_behavioral' in self.session['context']:
                    command_data['non_behavioral'] = self.session['context']['non_behavioral']
        if self.daphne_version == "EDL":
            pass
        if self.daphne_version == "AT":
            pass

        return command_data


    def intent_query(self, intent_info, command_data, role):
        query = intent_info['query']
        models, session, response_helpers = self.get_query_helpers(role)

        # --> Build final query and evaluate
        always_template = Template(query["always"])
        expression = always_template.substitute(command_data)
        for opt_cond in query["opt"]:
            if opt_cond["cond"] in command_data:
                opt_template = Template(opt_cond["query_part"])
                expression += opt_template.substitute(command_data)
        end_template = Template(query["end"])
        expression += end_template.substitute(command_data)
        query_db = eval(expression)

        # --> Parse query results
        results = []
        for result_info in query["results"]:
            if result_info["result_type"] == "list":
                result = []
                for row in query_db.all():
                    result_row = {}
                    for key, value in result_info["result_fields"].items():
                        result_row[key] = eval(Template(value).substitute(command_data))
                    result.append(result_row)
            elif result_info["result_type"] == "single":
                row = query_db.first()
                result = {}
                for key, value in result_info["result_fields"].items():
                    result[key] = eval(Template(value).substitute(command_data))
            else:
                raise ValueError("RIP result_type")
            results.append(result)

        return results

    def get_query_helpers(self, role):
        if role == "Historian":
            import EOSS.historian.models as models
            import EOSS.historian.response_helpers as response_helpers
            engine = models.db_connect()
            session = sessionmaker(bind=engine)()
            return models, session, response_helpers
        if role == "EDL":
            import EDL.data.model as models
            engine = models.db_connect()
            session = sessionmaker(bind=engine)()
            return models, session, None
        return None, None, None


    def intent_func(self, intent_info, command_data):

        # --> Get dialogue functions for daphne version
        dialogue_functions = self.get_func_helpers()

        # --> Evaluate function
        function_info = intent_info['function']
        run_template = Template(function_info["run_template"])
        run_command = run_template.substitute(command_data)
        command_results = eval(run_command)

        # --> Get function results
        if len(function_info["results"]) == 1:
            command_results = (command_results,)
        results = []
        for index, result_info in enumerate(function_info["results"]):
            if result_info["result_type"] == "list":
                result = []
                for item in command_results[index]:
                    result_row = {}
                    for key, value in result_info["result_fields"].items():
                        result_row[key] = eval(Template(value).substitute(command_data))
                    result.append(result_row)
            elif result_info["result_type"] == "single":
                result = {}
                for key, value in result_info["result_fields"].items():
                    result[key] = eval(Template(value).substitute(command_data))
            else:
                raise ValueError("RIP result_type")
            results.append(result)
        return results

    def get_func_helpers(self):
        if self.daphne_version == "EOSS":
            import EOSS.dialogue.dialogue_functions as dialogue_functions
            return dialogue_functions
        if self.daphne_version == "EDL":
            import EDL.dialogue.dialogue_functions as dialogue_functions
            return dialogue_functions
        if self.daphne_version == "AT":
            import AT.dialogue.dialogue_functions as dialogue_functions
            return dialogue_functions


    def build_answers(self, intent_info, data, results):
        voice_response_templates = intent_info['voice_response']
        visual_response_templates = intent_info['visual_response']

        answers = {}
        complete_data = data
        complete_data['results'] = results

        def build_text_from_list(templates, result):
            text = ""
            begin_template = Template(templates["begin"])
            text += begin_template.substitute(complete_data)
            repeat_template = Template(templates["repeat"])
            if len(result) > 0:
                first = True
                for item in result:
                    if first:
                        first = False
                    else:
                        text += ", "
                    text += repeat_template.substitute(item)
            else:
                text += "none"
            end_template = Template(templates["end"])
            text += end_template.substitute(complete_data)
            return text

        def build_text_from_single(template, result):
            text_template = Template(template["template"])
            result_data = complete_data
            for key, value in result.items():
                result_data[key] = value
            text = text_template.substitute(result_data)
            return text

        # Create voice response
        answers["voice_answer"] = ""
        for index, result in enumerate(results):
            if voice_response_templates[index]["type"] == "list":
                answers["voice_answer"] += build_text_from_list(voice_response_templates[index], result)
            elif voice_response_templates[index]["type"] == "single":
                answers["voice_answer"] += build_text_from_single(voice_response_templates[index], result)

        # Create visual response
        answers["visual_answer"] = []
        answers["visual_answer_type"] = []
        for index, result in enumerate(results):
            if visual_response_templates[index]["type"] == "text":
                answers["visual_answer_type"].append("text")
                if visual_response_templates[index]["from"] == "list":
                    answers["visual_answer"].append(build_text_from_list(visual_response_templates[index], result))
                elif visual_response_templates[index]["from"] == "single":
                    answers["visual_answer"].append(build_text_from_single(visual_response_templates[index], result))
            elif visual_response_templates[index]["type"] == "list":
                answers["visual_answer_type"].append("list")
                visual_answer = {}
                begin_template = Template(visual_response_templates[index]["begin"])
                visual_answer["begin"] = begin_template.substitute(complete_data)
                visual_answer["list"] = []
                item_template = Template(visual_response_templates[index]["item_template"])
                for item in result:
                    visual_answer["list"].append(item_template.substitute(item))
                answers["visual_answer"].append(visual_answer)
            elif visual_response_templates[index]["type"] == "multilist":
                answers["visual_answer_type"].append("multilist")
                visual_answer = {}
                begin_template = Template(visual_response_templates[index]["begin"])
                visual_answer["begin"] = begin_template.substitute(complete_data)
                visual_answer["list"] = []
                item_template = Template(visual_response_templates[index]["item_template"])
                for item in result:
                    visual_answer["list"].append({
                        "text": item_template.substitute(item),
                        "subitems": eval(Template(visual_response_templates[index]["subitems"]).substitute(item))
                    })
                answers["visual_answer"].append(visual_answer)
            elif visual_response_templates[index]["type"] == "timeline_plot":
                answers["visual_answer_type"].append("timeline_plot")
                visual_answer = {}
                title_template = Template(visual_response_templates[index]["title"])
                visual_answer["title"] = title_template.substitute(complete_data)
                visual_answer["plot_data"] = []
                for item in result:
                    category_template = Template(visual_response_templates[index]["item"]["category"])
                    id_template = Template(visual_response_templates[index]["item"]["id"])
                    start_template = Template(visual_response_templates[index]["item"]["start"])
                    end_template = Template(visual_response_templates[index]["item"]["end"])
                    visual_answer["plot_data"].append({
                        "category": category_template.substitute(item),
                        "id": id_template.substitute(item),
                        "start": start_template.substitute(item),
                        "end": end_template.substitute(item)
                    })
                answers["visual_answer"].append(visual_answer)
            elif visual_response_templates[index]["type"] == "hist_plot":
                answers["visual_answer_type"].append("hist_plot")
                visual_answer = {}
                title_template = Template(visual_response_templates[index]["title"])
                visual_answer["plot_info"] = {"plot_data": []}
                visual_answer["plot_info"]["title"] = title_template.substitute(complete_data)
                for item in result:
                    item_template = Template(visual_response_templates[index]["item_template"])
                    visual_answer["plot_info"]["plot_data"].append(float(item_template.substitute(item)))
                answers["visual_answer"].append(visual_answer)
            elif visual_response_templates[index]["type"] == "plot_vars":
                answers["visual_answer_type"].append("plot_vars")
                visual_answer = {}
                visual_answer["plot_info"] = {"plot_data": []}
                for item in result:
                    item_template = Template(visual_response_templates[index]["item_template"])
                    visual_answer["plot_info"]["plot_data"].append(eval(item_template.substitute(item)))
                title_template = Template(visual_response_templates[index]["title"])
                visual_answer["plot_info"]["title"] = title_template.substitute(complete_data)
                x_axis_template = Template(visual_response_templates[index]["x_axis_template"])
                y_axis_template = Template(visual_response_templates[index]["y_axis_template"])
                visual_answer["plot_info"]["x_axis"] = x_axis_template.substitute(complete_data)
                visual_answer["plot_info"]["y_axis"] = y_axis_template.substitute(complete_data)
                answers["visual_answer"].append(visual_answer)

        return answers


    """
      _____  _                _____  _             _            
     / ____|(_)              / ____|| |           (_)           
    | |  __  _ __   __ ___  | |     | |__    ___   _   ___  ___ 
    | | |_ || |\ \ / // _ \ | |     | '_ \  / _ \ | | / __|/ _ \
    | |__| || | \ V /|  __/ | |____ | | | || (_) || || (__|  __/
     \_____||_|  \_/  \___|  \_____||_| |_| \___/ |_| \___|\___|
                      
    """

    def give_choice(self, role, condition, types):

        answer = self.msg_choice

        # --> Append command choices to answer
        for type in types:
            intent_info = self.get_intent_info(role, type)
            answer["visual_answer"][0]["list"].append("You want me to " + intent_info["objective"] + ".")

        # --> Index dialogue history and context objects
        dialogue_history = DialogueHistory.objects.create(user_information=self.user_info,
                                                          voice_message=answer["voice_answer"],
                                                          visual_message_type=json.dumps(answer["visual_answer_type"]),
                                                          visual_message=json.dumps(answer["visual_answer"]),
                                                          dwriter="daphne",
                                                          date=datetime.datetime.utcnow())
        DialogueContext.objects.create(dialogue_history=dialogue_history,
                                       is_clarifying_input=True,
                                       clarifying_role=role,
                                       clarifying_commands=json.dumps(types))


    """
     _   _         _                                                      _      _       
    | \ | |       | |       /\                                           | |    | |      
    |  \| |  ___  | |_     /  \    _ __   ___ __      __ ___  _ __  __ _ | |__  | |  ___ 
    | . ` | / _ \ | __|   / /\ \  | '_ \ / __|\ \ /\ / // _ \| '__|/ _` || '_ \ | | / _ \
    | |\  || (_) || |_   / ____ \ | | | |\__ \ \ V  V /|  __/| |  | (_| || |_) || ||  __/
    |_| \_| \___/  \__| /_/    \_\|_| |_||___/  \_/\_/  \___||_|   \__,_||_.__/ |_| \___|
                                                                                          
    """

    def not_answerable(self):

        answer = self.msg_non_answerable

        dialogue_history = DialogueHistory.objects.create(user_information=self.user_info,
                                                          voice_message=answer["voice_answer"],
                                                          visual_message_type=json.dumps(answer["visual_answer_type"]),
                                                          visual_message=json.dumps(answer["visual_answer"]),
                                                          dwriter="daphne",
                                                          date=datetime.datetime.utcnow())

        DialogueContext.objects.create(dialogue_history=dialogue_history,
                                       is_clarifying_input=False)




