import json
import os

import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn

from daphne_API import data_helpers, qa_pipeline
from daphne_API.errors import ParameterMissingError
from daphne_API.models import EOSSContext, UserInformation


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


def not_allowed_condition(context: UserInformation, command_class, command_type):
    if len(context.eosscontext.allowedcommand_set.all()) == 0:
        return False
    for allowed_command in context.eosscontext.allowedcommand_set.all():
        if command_class == allowed_command.command_type and command_type == allowed_command.command_descriptor:
            return False
    return True


def not_allowed_answers():
    return {
        'voice_answer': 'This command is restricted right now.',
        'visual_answer_type': 'text',
        'visual_answer': 'This command is restricted right now.'
    }


def command(processed_command, command_class, condition_name, context: UserInformation):
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command, command_class)
    print(question_type)
    if not_allowed_condition(context, condition_name, str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    information = qa_pipeline.load_type_info(question_type, command_class)
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, information["params"], context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, context)
    # Query the database
    if information["type"] == "db_query":
        results = qa_pipeline.query(information["query"], data)
    elif information["type"] == "run_function":
        results = qa_pipeline.run_function(information["function"], data, context)
    else:
        results = None
    # Construct the response from the database query and the response format
    answers = qa_pipeline.build_answers(information["voice_response"], information["visual_response"], results, data)

    # Return the answer to the client
    return answers


def think_response(context: UserInformation):
    # TODO: Make this intelligent, e.g. hook this to a rule based engine
    db_answer = context.eosscontext.answer_set.all()[:1].get()
    frontend_answer = {
        "voice_answer": db_answer.voice_answer,
        "visual_answer_type": db_answer.visual_answer_type,
        "visual_answer": json.loads(db_answer.visual_answer)
    }
    return frontend_answer
