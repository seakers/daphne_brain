import os
import spacy

from daphne_brain.nlp_object import nlp
from daphne_API.historian import qa_pipeline

from tensorflow.contrib import learn

command_types = {
    "history": 1,
    "ifeed": 2,
    "vr": 3,
    "evaluate": 4,
    "criticize": 5
}

## Command Types
# 0: Switch mode
# 1: History commands
# 2: iFEED commands
# 3: VR commands
# 4: Evaluate commands
# 5: Criticize commands
# 100: Stop command

def classify_command(command):
    cleaned_command = qa_pipeline.clean_str(command)

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
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            # get the prediction
            prediction = sess.run(predictions, {input_x: x_test, dropout_keep_prob: 1.0})

    return prediction[0]

def process_command(processed_command):
    # Check if keywords are present for the switch modes commands, if not for now just return a random type as it will
    # be set already
    # TODO: Make a statistical model to check for type?
    has_let_keyword = False
    has_type_keyword = False
    has_stop_keyword = False
    type_keyword = ""
    for token in processed_command:
        if token.lemma_ == "let":
            has_let_keyword = True
        if token.lemma_ == "history" or token.lemma_ == "ifeed" or token.lemma_ == "vr" or token.lemma_ == "evaluate" \
            or token.lemma_ == "criticize":
            has_type_keyword = True
            type_keyword = token.lemma_
        if token.lemma_ == "stop":
            has_stop_keyword = True

    if has_let_keyword and has_type_keyword:
        return 0, command_types[type_keyword]
    elif has_stop_keyword:
        return 100, None
    else:
        return -1, None

def histdb_qa_pipeline:
    processed_question = nlp(request.data['question'])
    # Classify the question, obtaining a question type
    question_type = qa_pipeline.classify(processed_question)
    # Load list of required and optional parameters from question, query and response format for question type
    [params, query, response_template] = qa_pipeline.load_type_info(question_type)
    # Extract required and optional parameters
    data = qa_pipeline.extract_data(processed_question, params)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data)
    # Query the database
    response = qa_pipeline.query(query, data)
    # Construct the response from the database query and the response format
    answer = qa_pipeline.build_answer(response_template, response, data)

    # Return the answer to the client
    return Response({'answer': answer})