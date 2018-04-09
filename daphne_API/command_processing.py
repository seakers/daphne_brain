import os

import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn

from daphne_API import data_helpers, qa_pipeline
from daphne_API.errors import ParameterMissingError


def classify_command(command):
    cleaned_command = data_helpers.clean_str(command)

    # Map data into vocabulary
    vocab_path = os.path.join("./daphne_API/models/general/vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform([cleaned_command])))

    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint("./daphne_API/models/general/")
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

    return prediction[0]


def error_answers(missing_param):
    return {
        'voice_answer': 'I can\'t answer this question because I\'m missing a ' + missing_param + ' parameter.',
        'visual_answer_type': 'text',
        'visual_answer': 'I can\'t answer this question because I\'m missing a ' + missing_param + ' parameter.'
    }


def not_allowed_condition(context, command_class, command_type):
    if 'allowed_commands' not in context:
        return False
    if command_type not in context['allowed_commands'][command_class]:
        return True
    return False


def not_allowed_answers():
    return {
        'voice_answer': 'This command is restricted right now.',
        'visual_answer_type': 'text',
        'visual_answer': 'This command is restricted right now.'
    }

def ifeed_command(processed_command, context):
    print("Command classified as iFEED type")
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command, "iFEED")
    if not_allowed_condition(context, 'ifeed', str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    [params, function, voice_response_template, visual_response_template] = \
        qa_pipeline.load_type_info(question_type, "iFEED")
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, params, context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, context)
    # Query the database
    result = qa_pipeline.run_function(function, data, context)
    # Construct the response from the database query and the response format
    answers = qa_pipeline.build_answers(voice_response_template, visual_response_template, result, data)

    # Return the answer to the client
    return answers

def vassar_command(processed_command, context):
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command, "VASSAR")
    if not_allowed_condition(context, 'analyst', str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    [params, function, voice_response_template, visual_response_template] = \
        qa_pipeline.load_type_info(question_type, "VASSAR")
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, params, context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, context)
    # Query the database
    result = qa_pipeline.run_function(function, data, context)
    # Construct the response from the database query and the response format
    answers = qa_pipeline.build_answers(voice_response_template, visual_response_template, result, data)

    # Return the answer to the client
    return answers

def critic_command(processed_command, context):
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command, "Critic")
    if not_allowed_condition(context, 'critic', str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    [params, function, voice_response_template, visual_response_template] = \
        qa_pipeline.load_type_info(question_type, "Critic")
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, params, context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, context)
    # Query the database
    result = qa_pipeline.run_function(function, data, context)
    # Construct the response from the database query and the response format
    answers = qa_pipeline.build_answers(voice_response_template, visual_response_template, result, data)

    # Return the answer to the client
    return answers

def historian_command(processed_command, context):
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command, "Historian")
    if not_allowed_condition(context, 'historian', str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    [params, query, voice_response_template, visual_response_template] = \
        qa_pipeline.load_type_info(question_type, "Historian")
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, params, context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, context)
    # Query the database
    result = qa_pipeline.query(query, data)
    # Construct the response from the database query and the response format
    answers = qa_pipeline.build_answers(voice_response_template, visual_response_template, result, data)

    # Return the answer to the client
    return answers

def think_response(context):
    # TODO: Make this intelligent, e.g. hook this to a rule based engine
    return context["answers"][0]