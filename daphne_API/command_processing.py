import spacy

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

def get_command_type(processed_command):
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
