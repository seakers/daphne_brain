import tensorflow as tf
import numpy as np
import json
import os
import dateparser
import datetime
from tensorflow.contrib import learn
import histdb_API.models as models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from string import Template

def clean_str(spacy_doc):
    # Pre-process the strings
    tokens = []
    for token in spacy_doc:

        # If stopword or punctuation, ignore token and continue
        if (token.is_stop and not (token.lemma_ == "which" or token.lemma_ == "how" or token.lemma_ == "what"
                                   or token.lemma_ == "when" or token.lemma_ == "why")) \
                or token.is_punct:
            continue

        # Lemmatize the token and yield
        tokens.append(token.lemma_)
    return " ".join(tokens)


def classify(question):
    cleaned_question = clean_str(question)

    # Map data into vocabulary
    vocab_path = os.path.join("./histdb_API/model/vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform([cleaned_question])))

    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint("./histdb_API/model/checkpoints")
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
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            # get the prediction
            prediction = sess.run(predictions, {input_x: x_test, dropout_keep_prob: 1.0})

    return prediction[0]

def load_type_info(question_type):
    with open('./histdb_API/question_types/' + str(question_type) + '.json', 'r') as file:
        type_info = json.load(file)
    return [type_info["params"], type_info["query"], type_info["response"]]


def extract_measurement(processed_question, already_extracted):
    # Get a list of measurements
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = session.query(models.Measurement).all()
    # For every measurement, check if it has already been read and try to find the first occurrence
    for measurement in measurements:
        proc_measurement = measurement.name.strip().lower()
        start = 0
        for other_measurement in already_extracted:
            if other_measurement[0] == proc_measurement:
                start = other_measurement[1] + len(other_measurement[0])
        index = processed_question.text.find(proc_measurement, start)
        if index != -1:
            return proc_measurement, index
    return None


def extract_date(processed_question, already_extracted):
    # For now just pick the years
    for word in processed_question:
        if len(word) == 4 and word.like_num:
            already_written = False
            for other_year in already_extracted:
                if word.idx == other_year[1]:
                    already_written = True
            if already_written:
                continue
            return word.text, word.idx


extract_function = {}
extract_function["measurement"] = extract_measurement
extract_function["year"] = extract_date


def process_measurement(extracted_data, options):
    return extracted_data


def process_date(extracted_data, options):
    date_parsing_settings = {}
    if options == "begin":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 1, 1)}
    elif options == "end":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 12, 31)}
    return dateparser.parse(extracted_data, settings=date_parsing_settings)


process_function = {}
process_function["measurement"] = process_measurement
process_function["year"] = process_date


def extract_data(processed_question, params):
    extracted_data = {}
    already_extracted = {}
    for param in params:
        already_extracted[param["type"]] = []
    for param in params:
        extracted_param = extract_function[param["type"]](processed_question, already_extracted[param["type"]])
        if extracted_param != None:
            extracted_data[param["name"]] = process_function[param["type"]](extracted_param[0], param["options"])
            already_extracted[param["type"]].append(extracted_param)
    return extracted_data


def augment_data(data):
    data['now'] = datetime.datetime.now()
    return data

def query(query, data):
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()

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
    result = None
    response = "No response"
    if query["result_type"] == "list":
        result = []
        for row in query_db.all():
            result.append(eval("row." + query["result_field"]))
        if len(result) > 0:
            response = result[0]
            for text in result[1:]:
                response += ", " + text
        else:
            response = "none"
    return response

def build_answer(response_template, response, data):
    complete_data = data
    complete_data["response"] = response
    answer_template = Template(response_template)
    answer = answer_template.substitute(complete_data)
    return answer