import os

from daphne_API.historian import qa_pipeline

import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn

from daphne_API import data_helpers

def classify_command(command):
    cleaned_command = data_helpers.clean_str(command)

    # Map data into vocabulary
    vocab_path = os.path.join("./daphne_API/models/general/vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform([cleaned_command])))

    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint("./daphne_API/models/general/checkpoints")
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

def ifeed_command(processed_command):
    pass

def vassar_command(processed_command):
    pass

def critic_command(processed_command):
    pass

def historian_command(processed_command):
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_command)
    # Load list of required and optional parameters from question, query and response format for question type
    [params, query, response_template] = qa_pipeline.load_type_info(question_type)
    # Extract required and optional parameters
    data = qa_pipeline.extract_data(processed_command, params)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data)
    # Query the database
    response = qa_pipeline.query(query, data)
    # Construct the response from the database query and the response format
    answer = qa_pipeline.build_answer(response_template, response, data)

    # Return the answer to the client
    return answer

def think_response(context):
    # TODO: Make this intelligent, e.g. hook this to a rule based engine
    return context["answers"][0]