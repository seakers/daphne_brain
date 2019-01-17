import datetime
import json
import os
from string import Template

import numpy as np
import tensorflow as tf
from django.conf import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
from sqlalchemy import func
from tensorflow.contrib import learn
from daphne_API import data_helpers

import daphne_API.historian.models as models
import daphne_API.data_extractors as extractors
import daphne_API.data_processors as processors
import daphne_API.runnable_functions as run_func
from daphne_API.errors import ParameterMissingError
from daphne_API.models import UserInformation

if 'EDL' in settings.ACTIVE_MODULES:
    import daphne_API.edl.model as edl_models


def classify(question, module_name):
    cleaned_question = data_helpers.clean_str(question)

    # Map data into vocabulary
    vocab_path = os.path.join("./daphne_API/models/" + module_name + "/vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform([cleaned_question])))

    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint("./daphne_API/models/" + module_name + "/")
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
            saver.restore(sess, checkpoint_file)

            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]

            # Tensors we want to evaluate
            logits = graph.get_operation_by_name("output/logits").outputs[0]

            # get the prediction
            result_logits = sess.run(logits, {input_x: x_test, dropout_keep_prob: 1.0})
            prediction = data_helpers.get_label_using_logits(result_logits, top_number=1)

    named_labels = []
    for filename in sorted(os.listdir("./daphne_API/command_types/" + module_name)):
        specific_label = int(filename.split('.', 1)[0])
        named_labels.append(specific_label)
    return named_labels[prediction[0][0]]


def load_type_info(question_type, module_name):
    with open('./daphne_API/command_types/' + module_name + '/' + str(question_type) + '.json', 'r') as file:
        type_info = json.load(file)
    information = {}
    information["type"] = type_info["type"]
    information["params"] = type_info["params"]
    if type_info["type"] == "db_query":
        information["query"] = type_info["query"]
    elif type_info["type"] == "run_function":
        information["function"] = type_info["function"]
    information["voice_response"] = type_info["voice_response"]
    information["visual_response"] = type_info["visual_response"]
    return information

extract_function = {}
extract_function["mission"] = extractors.extract_mission
extract_function["measurement"] = extractors.extract_measurement
extract_function["technology"] = extractors.extract_technology
extract_function["space_agency"] = extractors.extract_space_agency
extract_function["year"] = extractors.extract_date
extract_function["design_id"] = extractors.extract_design_id
extract_function["agent"] = extractors.extract_agent
extract_function["instrument_parameter"] = extractors.extract_instrument_parameter
extract_function["vassar_instrument"] = extractors.extract_vassar_instrument
extract_function["vassar_measurement"] = extractors.extract_vassar_measurement
extract_function["vassar_stakeholder"] = extractors.extract_vassar_stakeholder
extract_function["objective"] = extractors.extract_vassar_objective

extract_function["name"] = extractors.extract_edl_mission
extract_function["edl_mission"] = extractors.extract_edl_mission
extract_function["parameter"] = extractors.extract_edl_parameter
extract_function["edl_mat_file"] = extractors.extract_edl_mat_file
extract_function["edl_mat_param"] = extractors.extract_edl_mat_parameter
extract_function["extract_scorecard_filename"] = extractors.extract_scorecard_filename
extract_function["scorecard_edlmetricsheet_results"] = extractors.extract_edl_scorecard_edlmetricsheet
extract_function["edl_metric_calculate"] = extractors.edl_metric_calculate
extract_function["edl_metric_names"] = extractors.get_edl_metric_names

process_function = {}
process_function["mission"] = processors.process_mission
process_function["measurement"] = processors.not_processed
process_function["technology"] = processors.not_processed
process_function["space_agency"] = processors.process_mission
process_function["year"] = processors.process_date
process_function["design_id"] = processors.not_processed
process_function["agent"] = processors.not_processed
process_function["instrument_parameter"] = processors.not_processed
process_function["vassar_instrument"] = processors.not_processed
process_function["vassar_measurement"] = processors.not_processed
process_function["vassar_stakeholder"] = processors.not_processed
process_function["objective"] = processors.not_processed

process_function["parameter"] = processors.process_parameter
process_function["edl_mission"] = processors.not_processed
process_function["name"] = processors.not_processed
process_function["edl_mat_file"] = processors.not_processed
process_function["edl_mat_param"] = processors.not_processed
process_function["extract_scorecard_filename"] = processors.not_processed
process_function["scorecard_edlmetricsheet_results"] = processors.not_processed
process_function["edl_metric_calculate"] = processors.process_edl_scorecard_calculate
process_function["edl_metric_names"]=processors.not_processed

def extract_data(processed_question, params, context: UserInformation):
    """ Extract the features from the processed question, with a correcting factor """
    number_of_features = {}
    extracted_raw_data = {}
    extracted_data = {}
    # Count how many non-context params of each type are needed
    for param in params:
        if not param["from_context"]:
            print(processed_question)
            if param["type"] in number_of_features:
                number_of_features[param["type"]] += 1
            else:
                number_of_features[param["type"]] = 1
    # Try to extract the required number of parameters
    for type, num in number_of_features.items():
        extracted_raw_data[type] = extract_function[type](processed_question, num, context)
    # For each parameter check if it's needed and apply postprocessing;
    for param in params:
        extracted_param = None
        if param["from_context"]:
            try:
                subcontext = context
                if param["context"] is not "":
                    subcontext = getattr(subcontext, param["context"])
                if param["subcontext"] is not "":
                    subcontext = getattr(subcontext, param["subcontext"])
                extracted_param = getattr(subcontext, param["name"])
            except AttributeError:
                if param["mandatory"]:
                    raise ParameterMissingError(param["type"])
        else:
            if len(extracted_raw_data[param["type"]]) > 0:
                extracted_param = extracted_raw_data[param["type"]].pop(0)
            elif param["mandatory"]:
                # If param is needed but not detected return error with type of parameter
                raise ParameterMissingError(param["type"])
        if extracted_param is not None:
            extracted_data[param["name"]] = process_function[param["type"]](extracted_param, param["options"], context)
    return extracted_data


def augment_data(data, context: UserInformation):
    data['now'] = datetime.datetime.utcnow()

    data['designs'] = context.eosscontext.design_set.all()

    #if 'behavioral' in context:
    #    data['behavioral'] = context['behavioral']
    #if 'non_behavioral' in context:
    #    data['non_behavioral'] = context['non_behavioral']
    # TODO: Add useful information from context if needed
    return data


def query(query, data):
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    if 'EDL' in settings.ACTIVE_MODULES:
        edl_engine = edl_models.db_connect()
        edl_session = sessionmaker(bind=edl_engine)()

    def print_orbit(orbit):
        text_orbit = ""
        orbit_codes = {
            "GEO": "geostationary",
            "LEO": "low earth",
            "HEO": "highly elliptical",
            "SSO": "sun-synchronous",
            "Eq": "equatorial",
            "NearEq": "near equatorial",
            "MidLat": "mid latitude",
            "NearPo": "near polar",
            "Po": "polar",
            "DD": "dawn-dusk local solar time",
            "AM": "morning local solar time",
            "Noon": "noon local solar time",
            "PM": "afternoon local solar time",
            "VL": "very low altitude",
            "L": "low altitude",
            "M": "medium altitude",
            "H": "high altitude",
            "VH": "very high altitude",
            "NRC": "no repeat cycle",
            "SRC": "short repeat cycle",
            "LRC": "long repeat cycle"
        }
        if orbit is not None:
            orbit_parts = orbit.split('-')
            text_orbit = "a "
            first = True
            for orbit_part in orbit_parts:
                if first:
                    first = False
                else:
                    text_orbit += ', '
                text_orbit += orbit_codes[orbit_part]
            text_orbit += " orbit"
        else:
            text_orbit = "none"
        return text_orbit

    def print_date(date):
        return date.strftime('%d %B %Y')

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


def run_function(function_info, data, context: UserInformation):
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