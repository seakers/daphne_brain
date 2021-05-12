import datetime
import json
import os
import pickle
import glob

import numpy as np

from dialogue import qa_pipeline, data_helpers
from dialogue.errors import ParameterMissingError
from daphne_context.models import UserInformation, DialogueHistory, DialogueContext
from dialogue.nn_models import nn_models


def classify_command_role(command, daphne_version):
    cleaned_command = data_helpers.clean_str(command)

    # Get model
    loaded_model = nn_models[daphne_version]["general"]

    # Map data into vocabulary
    model_folder_path = os.path.join(os.getcwd(), "dialogue", "models", daphne_version, "general")
    vocab_path = os.path.join(model_folder_path, "tokenizer.pickle")
    with open(vocab_path, 'rb') as handle:
        tokenizer = pickle.load(handle)

    x = tokenizer.texts_to_sequences([cleaned_command])
    expected_input_length = loaded_model.layers[0].input_shape[0][1]
    x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])
    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    # evaluate loaded model on test data
    result_logits = loaded_model.predict(x)
    prediction = data_helpers.get_label_using_logits(result_logits, top_number=1)
    return prediction[0]


def command_type_predictions(processed_command, daphne_version, module_name):
    cleaned_question = data_helpers.clean_str(processed_command)

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

    return result_logits


def get_top_types(logits, daphne_version, module_name, top_number):
    numerical_labels = data_helpers.get_label_using_logits(logits, top_number=top_number)[0]

    named_labels = []
    type_info_folder = os.path.join(os.getcwd(), daphne_version, "dialogue", "command_types", module_name)
    for filename in sorted(glob.glob(os.path.join(type_info_folder, "*.json"))):
        specific_label = int(os.path.basename(filename).split('.', 1)[0])
        named_labels.append(specific_label)
    command_types = []
    for label in numerical_labels:
        command_types.append(named_labels[label])
    return command_types


def error_answers(objective, missing_param):
    return {
        'voice_answer': 'Sorry, but I can\'t answer your question. I interpreted that you are trying to ask me to ' +
                        objective +
                        '. I can\'t do this because a ' + missing_param + ' parameter doesn\'t have a valid value. If '
                        'you think I\'m not doing the correct thing, please report this to someone.',
        'visual_answer_type': ['text'],
        'visual_answer': ['Sorry, but I can\'t answer your question. I interpreted that you are trying to ask me to ' +
                          objective +
                          '. I can\'t do this because a ' + missing_param + ' parameter doesn\'t have a valid value. If '
                          'you think I\'m not doing the correct thing, please report this to someone.']
    }


def not_allowed_condition(user_information: UserInformation, command_class, command_type):
    if len(user_information.allowedcommand_set.all()) == 0:
        return False
    for allowed_command in user_information.allowedcommand_set.all():
        if command_class == allowed_command.command_type and command_type == str(allowed_command.command_descriptor):
            return False
    return True


def not_allowed_answers():
    return {
        'voice_answer': 'This command is restricted right now.',
        'visual_answer_type': ['text'],
        'visual_answer': ['This command is restricted right now.']
    }


def answer_command(processed_command, question_type, command_class, condition_name, user_info: UserInformation,
                   context, new_dialogue_contexts, session):
    # Create a DialogueContext for the user to fill
    answer = command(processed_command, question_type, command_class, condition_name, user_info, context,
                     new_dialogue_contexts, session)
    dialogue_history = DialogueHistory.objects.create(user_information=user_info,
                                                      voice_message=answer["voice_answer"],
                                                      visual_message_type=json.dumps(answer["visual_answer_type"]),
                                                      visual_message=json.dumps(answer["visual_answer"]),
                                                      writer="daphne",
                                                      date=datetime.datetime.utcnow())

    return dialogue_history


def choose_command(command_types, daphne_version, command_role, command_class, context: UserInformation):
    # Load information on the three commands
    answer = {
        'voice_answer': 'I\'m not confident enough in my interpretation of your question. Please help me by choosing'
                        ' what you are trying to accomplish from the following options.',
        'visual_answer_type': ['list'],
        'visual_answer': [{
            "begin": 'I\'m not confident enough in my interpretation of your question. Please help me by choosing'
                     ' what you are trying to accomplish from the following options. You can either click on the '
                     'objective or type first/second/third',
            "list": []
        }]
    }
    for command_type in command_types:
        information = qa_pipeline.load_type_info(command_type, daphne_version, command_class)
        answer["visual_answer"][0]["list"].append("You want me to " + information["objective"] + ".")

    dialogue_history = DialogueHistory.objects.create(user_information=context,
                                                      voice_message=answer["voice_answer"],
                                                      visual_message_type=json.dumps(answer["visual_answer_type"]),
                                                      visual_message=json.dumps(answer["visual_answer"]),
                                                      writer="daphne",
                                                      date=datetime.datetime.utcnow())
    DialogueContext.objects.create(dialogue_history=dialogue_history,
                                   is_clarifying_input=True,
                                   clarifying_role=command_role,
                                   clarifying_commands=json.dumps(command_types))


def not_answerable(context: UserInformation):
    # Load information on the three commands
    answer = {
        'voice_answer': 'I don\'t understand your command. Please rephrase it.',
        'visual_answer_type': ['text'],
        'visual_answer': ['I don\'t understand your command. Please rephrase it.']
    }

    dialogue_history = DialogueHistory.objects.create(user_information=context,
                                                      voice_message=answer["voice_answer"],
                                                      visual_message_type=json.dumps(answer["visual_answer_type"]),
                                                      visual_message=json.dumps(answer["visual_answer"]),
                                                      writer="daphne",
                                                      date=datetime.datetime.utcnow())

    DialogueContext.objects.create(dialogue_history=dialogue_history,
                                   is_clarifying_input=False)


def command(processed_command, question_type, command_class, condition_name, user_information: UserInformation, context,
            new_dialogue_contexts, session):
    if not_allowed_condition(user_information, condition_name, str(question_type)):
        return not_allowed_answers()
    daphne_version = user_information.daphne_version
    # Load list of required and optional parameters from question, query and response format for question type
    information = qa_pipeline.load_type_info(question_type, daphne_version, command_class)
    # Extract required and optional parameters
    try:
        data = qa_pipeline.extract_data(processed_command, information["params"], user_information, context)
    except ParameterMissingError as error:
        print(error)
        return error_answers(information["objective"], error.missing_param)
    # Add extra parameters to data
    data = qa_pipeline.augment_data(data, user_information, session)
    # Query the database
    if information["type"] == "db_query":
        results = qa_pipeline.query(information["query"], data, command_class)
    elif information["type"] == "run_function":
        results = qa_pipeline.run_function(information["function"], data, daphne_version, context, new_dialogue_contexts)
    elif information["type"] == "neo4j_query":
        results = qa_pipeline.neo4j_query(information["neo4j_query"], data, command_class)
    else:
        raise ValueError("JSON format not supported!")
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
