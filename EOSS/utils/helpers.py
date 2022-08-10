import json

def bool_list_to_string(bool_list_str):
    bool_list = json.loads(bool_list_str)
    print("--> bool_list_to_string", bool_list)
    return_str = ''
    for bool_pos in bool_list:
        if bool_pos:
            return_str = return_str + '1'
        else:
            return_str = return_str + '0'
    return return_str

def boolean_string_to_boolean_array(boolean_string):
    return [b == "1" for b in boolean_string]









