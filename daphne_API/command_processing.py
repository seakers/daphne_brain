import spacy

command_types = {
    "history": 1,
    "ifeed": 2,
    "vr": 3,
    "evaluate": 4,
    "criticize": 5
}


def get_command_type(processed_command):
    # Check if keywords are present for the switch modes commands, if not for now just return a random type as it will
    # be set already
    # TODO: Make a statistical model to check for type?
    has_let_keyword = False
    has_type_keyword = False
    type_keyword = ""
    for token in processed_command:
        if token.lemma_ == "let":
            has_let_keyword = True
        if token.lemma_ == "history" or token.lemma_ == "ifeed" or token.lemma_ == "vr" or token.lemma_ == "evaluate" \
            or token.lemma_ == "criticize":
            has_type_keyword = True
            type_keyword = token.lemma_

    if has_let_keyword and has_type_keyword:
        return 0, command_types[type_keyword]
    else:
        return -1, None
