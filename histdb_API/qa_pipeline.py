import tensorflow as tf
import numpy as np
import json
import os
from tensorflow.contrib import learn


def clean_str(spacy_doc):
    # Pre-process the strings
    tokens = []
    for token in spacy_doc:

        # If stopword or punctuation, ignore token and continue
        if token.is_stop or token.is_punct:
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

def extract_data(processed_question, params):
    pass

def query(query, data):
    pass

def build_answer(response_template, response):
    pass