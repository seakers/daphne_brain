import json
import os

import numpy as np
import keras
from keras.engine.saving import model_from_json
from keras.preprocessing.text import tokenizer_from_json

from dialogue import qa_pipeline, data_helpers
from dialogue.errors import ParameterMissingError
from daphne_context.models import UserInformation


def classify_command(command, daphne_version):
    cleaned_command = data_helpers.clean_str(command)

    with keras.backend.get_session().graph.as_default():
        # Map data into vocabulary
        model_folder_path = os.path.join(os.getcwd(), "dialogue", "models", daphne_version, "general")
        vocab_path = os.path.join(model_folder_path, "tokenizer.json")
        with open(vocab_path, mode="r") as tokenizer_json:
            tokenizer = tokenizer_from_json(tokenizer_json.read())
        # load json and create model
        model_path = os.path.join(model_folder_path, "model.json")
        with open(model_path, mode="r") as model_json:
            loaded_model = model_from_json(model_json.read())
        # load weights into new model
        weights_path = os.path.join(model_folder_path, "model.h5")
        loaded_model.load_weights(weights_path)
        print("Loaded model from disk")

        x = tokenizer.texts_to_sequences([cleaned_command])
        expected_input_length = loaded_model.layers[0].input_shape[1]
        x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])
        print("\nEvaluating...\n")

        # Evaluation
        # ==================================================
        # evaluate loaded model on test data
        loaded_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['binary_accuracy'])
        result_logits = loaded_model.predict(x)
        prediction = data_helpers.get_label_using_logits(result_logits, top_number=1)
        return prediction[0]


def error_answers(missing_param):
    return {
        'voice_answer': 'I can\'t answer this question because I\'m missing a ' + missing_param + ' parameter.',
        'visual_answer_type': ['text'],
        'visual_answer': ['I can\'t answer this question because I\'m missing a ' + missing_param + ' parameter.']
    }


def not_allowed_condition(context: UserInformation, command_class, command_type):
    if len(context.allowedcommand_set.all()) == 0:
        return False
    for allowed_command in context.allowedcommand_set.all():
        if command_class == allowed_command.command_type and command_type == str(allowed_command.command_descriptor):
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
    question_type = qa_pipeline.classify(processed_command, context.daphne_version, command_class)
    print(question_type)
    if not_allowed_condition(context, condition_name, str(question_type)):
        return not_allowed_answers()
    # Load list of required and optional parameters from question, query and response format for question type
    information = qa_pipeline.load_type_info(question_type, context.daphne_version, command_class)
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
        results = qa_pipeline.query(information["query"], data, command_class)
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
    db_answer = context.dialoguehistory_set.order_by("-date")[:1].get()
    frontend_answer = {
        "voice_message": db_answer.voice_message,
        "visual_message_type": json.loads(db_answer.visual_message_type),
        "visual_message": json.loads(db_answer.visual_message),
        "writer": "daphne",
    }
    return frontend_answer
