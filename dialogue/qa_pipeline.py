import datetime
import json
import os
import pickle
from string import Template

import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import or_

from dialogue import data_helpers
from dialogue.errors import ParameterMissingError
from daphne_context.models import UserInformation
from dialogue.nn_models import nn_models
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index
from . import ner

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

def extract_data(processed_question, params, user_information: UserInformation, context):
    print("Processed Question: {}".format(processed_question))
    """ Extract the features from the processed question, with a correcting factor """
    number_of_features = {}
    extracted_raw_data = {}
    extracted_data = {}

    # Get the right extractors and processors
    extract_function = get_extract_functions(user_information.daphne_version)
    process_function = get_process_functions(user_information.daphne_version)

    # Count how many non-context params of each type are needed
    for param in params:
        print("Param: {}".format(param))
        if not param["from_context"]:
            print(processed_question)
            if param["type"] in number_of_features:
                number_of_features[param["type"]] += 1
            else:
                number_of_features[param["type"]] = 1
    # Try to extract the required number of parameters
    #for type, num in number_of_features.items():
    #    extracted_raw_data[type] = extract_function[type](processed_question, num, user_information)
        #print("ERD Type {}: {}".format(type, extracted_raw_data[type]))
    print("Calling ner")
    _, extracted_raw_data = ner.ner(processed_question)
    print(extracted_raw_data)
    
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
            try: 
                extracted_entity = str(extracted_raw_data[param["type"]].pop(0))
                extracted_param = sorted_list_of_features_by_index(extracted_entity, extract_function[param["type"]](extracted_entity, user_information))[0]
                print("Extracted_param: {}".format(extracted_param))
            except KeyError:
                if param["mandatory"]:
                    # If param is needed but not detected return error with type of parameter
                    raise ParameterMissingError(param["type"])
        if extracted_param is not None:
            extracted_data[param["name"]] = process_function[param["type"]](extracted_param, param["options"],
                                                                            user_information)
            print("ED Name: {}".format(extracted_data[param["name"]]))                                                                        
    print("EData: {}".format(extract_data))
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
