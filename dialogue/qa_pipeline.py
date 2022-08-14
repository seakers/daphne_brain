import datetime
import json
import os
import pickle
import re
from string import Template

import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import or_
from neo4j import GraphDatabase, basic_auth

from dialogue import data_helpers
from dialogue.errors import ParameterMissingError
from daphne_context.models import UserInformation
from dialogue.nn_models import nn_models


def classify(question, daphne_version, module_name):
    cleaned_question = data_helpers.clean_str(question)

    # Get model
    loaded_model = nn_models[daphne_version][module_name]
    # Map data into vocabulary
    model_folder_path = os.path.join(os.getcwd(), "dialogue", "models", daphne_version, module_name)
    vocab_path = os.path.join(model_folder_path, "tokenizer.pickle")
    with open(vocab_path, 'rb') as handle:
        tokenizer = pickle.load(handle)

    x = tokenizer.texts_to_sequences([cleaned_question])
    expected_input_length = loaded_model.layers[0].input_shape[0][1]
    x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])
    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    # evaluate loaded model on test data
    result_logits = loaded_model.predict(x)
    prediction = data_helpers.get_label_using_logits(result_logits, top_number=1)

    named_labels = []
    type_info_folder = os.path.join(os.getcwd(), daphne_version, "dialogue", "command_types", module_name)
    for filename in sorted(os.listdir(type_info_folder)):
        specific_label = int(filename.split('.', 1)[0])
        named_labels.append(specific_label)
    return named_labels[prediction[0][0]]


def load_type_info(question_type, daphne_version, module_name):
    type_info_file = os.path.join(os.getcwd(), daphne_version, "dialogue", "command_types", module_name,
                                  str(question_type) + '.json')
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
    elif type_info["type"] == "neo4j_query":
        information["neo4j_query"] = type_info["neo4j_query"]
    information["voice_response"] = type_info["voice_response"]
    information["visual_response"] = type_info["visual_response"]
    return information


def get_extract_functions(daphne_version):
    if daphne_version == "EOSS":
        from EOSS.dialogue.data_extractors import extract_function
        return extract_function
    if daphne_version == "EDL":
        from EDL.dialogue.data_extractors import extract_function
        return extract_function
    if daphne_version == "AT":
        from AT.dialogue.data_extractors import extract_function
        return extract_function


def get_process_functions(daphne_version):
    if daphne_version == "EOSS":
        from EOSS.dialogue.data_processors import process_function
        return process_function
    if daphne_version == "EDL":
        from EDL.dialogue.data_processors import process_function
        return process_function
    if daphne_version == "AT":
        from AT.dialogue.data_processors import process_function
        return process_function


def get_entities(processed_question_str, daphne_version):
    # Get the model
    loaded_model = nn_models[daphne_version]['ner']

    doc = loaded_model(processed_question_str.text)
    param = {}
    # Find named entities, phrases and concepts
    for index, entity in enumerate(doc.ents):
        param[entity.label_] = entity.text

    return param


def is_number(x):
    if type(x) == str:
        x = x.replace(',', '')
    try:
        float(x)
        int(x)
    except:
        return False
    return True


def convert_string_to_number(textnum, numwords=None):

    if re.search('[a-zA-Z]', textnum):
        if numwords is None:
            numwords = {}

        units = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
            'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
            'sixteen', 'seventeen', 'eighteen', 'nineteen',
        ]
        tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        scales = ['hundred', 'thousand', 'million', 'billion', 'trillion']
        ordinal_words = {'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8, 'ninth': 9, 'twelfth': 12}
        ordinal_endings = [('ieth', 'y'), ('th', '')]

        if not numwords:
            numwords['and'] = (1, 0)
            for idx, word in enumerate(units): numwords[word] = (1, idx)
            for idx, word in enumerate(tens): numwords[word] = (1, idx * 10)
            for idx, word in enumerate(scales): numwords[word] = (10 ** (idx * 3 or 2), 0)

        textnum = textnum.replace('-', ' ')

        current = result = 0
        curstring = ''
        onnumber = False
        lastunit = False
        lastscale = False

        def is_numword(x):
            if is_number(x):
                return True
            if word in numwords:
                return True
            return False

        def from_numword(x):
            if is_number(x):
                scale = 0
                increment = int(x.replace(',', ''))
                return scale, increment
            return numwords[x]

        for word in textnum.split():
            if word in ordinal_words:
                scale, increment = (1, ordinal_words[word])
                current = current * scale + increment
                if scale > 100:
                    result += current
                    current = 0
                onnumber = True
                lastunit = False
                lastscale = False
            else:
                for ending, replacement in ordinal_endings:
                    if word.endswith(ending):
                        word = "%s%s" % (word[:-len(ending)], replacement)

                if (not is_numword(word)) or (word == 'and' and not lastscale):
                    if onnumber:
                        # Flush the current number we are building
                        curstring += repr(result + current) + " "
                    curstring += word + " "
                    result = current = 0
                    onnumber = False
                    lastunit = False
                    lastscale = False
                else:
                    scale, increment = from_numword(word)
                    onnumber = True

                    if lastunit and (word not in scales):
                        # Assume this is part of a string of individual numbers to
                        # be flushed, such as a zipcode "one two three four five"
                        curstring += repr(result + current)
                        result = current = 0

                    if scale > 1:
                        current = max(1, current)

                    current = current * scale + increment
                    if scale > 100:
                        result += current
                        current = 0

                    lastscale = False
                    lastunit = False
                    if word in scales:
                        lastscale = True
                    elif word in units:
                        lastunit = True

        if onnumber:
            curstring += repr(result + current)

        # remove all whitespaces
        curstring = curstring.replace(" ", "")

    else:
        # remove all whitespaces
        curstring = textnum.replace(" ", "")

    return curstring


def preprocess_entities(entities):
    processed_entities = entities
    # replace point with decimals
    if 'point' in entities:
        processed_entities = processed_entities.replace('point', '.')
    if 'number' in entities:
        processed_entities = processed_entities.replace('number ', '#')
    if '-' in entities:
        processed_entities = processed_entities.replace('-', '')
    if '(' in entities:
        processed_entities = processed_entities.replace('(', '')
    if ')' in entities:
        processed_entities = processed_entities.replace(')', '')

    ''''implement homophones for numbers in measurements and steps'''
    if 'to' in entities:
        processed_entities = processed_entities.replace('to', '2')
    if 'too' in entities:
        processed_entities = processed_entities.replace('too', '2')
    if 'tree' in entities:
        processed_entities = processed_entities.replace('tree', '3')
    if 'for' in entities:
        processed_entities = processed_entities.replace('for', '4')

    return processed_entities


def extract_data(processed_question, params, user_information: UserInformation, context):
    """ Extract the features from the processed question, with a correcting factor """
    number_of_features = {}
    extracted_raw_data = {}
    extracted_data = {}

    # Get the right extractors and processors
    extract_function = get_extract_functions(user_information.daphne_version)
    process_function = get_process_functions(user_information.daphne_version)

    # Count how many non-context params of each type are needed
    for param in params:
        if not param["from_context"]:
            if param["type"] in number_of_features:
                number_of_features[param["type"]] += 1
            else:
                number_of_features[param["type"]] = 1
    # Try to extract the required number of parameters
    entities = get_entities(processed_question, user_information.daphne_version)

    # iterate over entities objects to get the entity that matches the feature
    for type, num in number_of_features.items():
        if entities:
            for entity_name, entity_value in entities.items():
                if entity_name == type:
                    # process the entities
                    entity_value = preprocess_entities(entity_value)
                    if 'NUMBER' in entity_name:
                        entity_value = convert_string_to_number(entity_value)
                    extracted_raw_data[type] = extract_function[type](entity_value, num, user_information)
    # For each parameter check if it's needed and apply postprocessing;
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
            if param["type"] in extracted_raw_data and len(extracted_raw_data[param["type"]]) > 0:
                extracted_param = extracted_raw_data[param["type"]].pop(0)
            elif param["mandatory"]:
                # If param is needed but not detected return error with type of parameter
                raise ParameterMissingError(param["type"])
        if extracted_param is not None:
            extracted_data[param["name"]] = process_function[param["type"]](extracted_param, param["options"],
                                                                            user_information)
    return extracted_data


def augment_data(data, user_information: UserInformation, session):
    data['now'] = datetime.datetime.utcnow()
    data['session_key'] = session.session_key
    if user_information.daphne_version == "EOSS":
        data['designs'] = user_information.eosscontext.design_set.order_by('id').all()
        data['problem'] = user_information.eosscontext.problem
    if user_information.daphne_version == "EDL":
        pass
    if user_information.daphne_version == "AT":
        pass

    # TODO: Add useful information from context if needed
    return data


def get_query_model(command_class):
    if command_class == "Historian":
        import EOSS.historian.models as models
        engine = models.db_connect()
        session = sessionmaker(bind=engine)()
        return models, session
    if command_class == "EDL":
        import EDL.data.model as models
        engine = models.db_connect()
        session = sessionmaker(bind=engine)()
        return models, session
    if command_class == "Diagnosis":
        import AT.diagnosis.models as models
        engine = models.db_connect()
        session = sessionmaker(bind=engine)()
        return models, session
    return None, None


def get_response_helpers(command_class):
    if command_class == "Historian":
        import EOSS.historian.response_helpers as response_helpers
        return response_helpers
    return None


def query(query, data, command_class):
    models, session = get_query_model(command_class)
    response_helpers = get_response_helpers(command_class)

    # Build the final query to the database
    always_template = Template(query["always"])
    expression = always_template.substitute(data)
    for opt_cond in query["opt"]:
        if opt_cond["cond"] in data:
            opt_template = Template(opt_cond["query_part"])
            expression += opt_template.substitute(data)
    end_template = Template(query["end"])
    expression += end_template.substitute(data)
    query_db = eval(expression)

    results = []
    for result_info in query["results"]:
        if result_info["result_type"] == "list":
            result = []
            for row in query_db.all():
                result_row = {}
                for key, value in result_info["result_fields"].items():
                    result_row[key] = eval(Template(value).substitute(data))
                result.append(result_row)
        elif result_info["result_type"] == "single":
            row = query_db.first()
            result = {}
            for key, value in result_info["result_fields"].items():
                result[key] = eval(Template(value).substitute(data))
        else:
            raise ValueError("RIP result_type")
        results.append(result)

    return results


def neo4j_query(query, data, command_class):
    print(query)
    print(data)
    driver = GraphDatabase.driver("neo4j://3.15.160.239:7687", auth=basic_auth("neo4j", "goSEAKers!"))
    session = driver.session()

    results = "result"
    return results


def get_dialogue_functions(daphne_version):
    if daphne_version == "EOSS":
        import EOSS.dialogue.dialogue_functions as dialogue_functions
        return dialogue_functions
    if daphne_version == "EDL":
        import EDL.dialogue.dialogue_functions as dialogue_functions
        return dialogue_functions
    if daphne_version == "AT":
        import AT.dialogue.dialogue_functions as dialogue_functions
        return dialogue_functions


def run_function(function_info, data, daphne_version, context, new_dialogue_contexts):
    # Load the functions that must be run
    dialogue_functions = get_dialogue_functions(daphne_version)
    # Run the function and save the results
    run_template = Template(function_info["run_template"])
    run_command = run_template.substitute(data)
    command_results = eval(run_command)
    if len(function_info["results"]) == 1:
        command_results = (command_results,)

    results = []
    for index, result_info in enumerate(function_info["results"]):
        if result_info["result_type"] == "list":
            result = []
            for item in command_results[index]:
                result_row = {}
                for key, value in result_info["result_fields"].items():
                    result_row[key] = eval(Template(value).substitute(data))
                result.append(result_row)
        elif result_info["result_type"] == "single":
            result = {}
            for key, value in result_info["result_fields"].items():
                result[key] = eval(Template(value).substitute(data))
        else:
            raise ValueError("RIP result_type")
        results.append(result)

    return results


def build_answers(voice_response_templates, visual_response_templates, results, data):
    complete_data = data
    complete_data["results"] = results

    answers = {}

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
