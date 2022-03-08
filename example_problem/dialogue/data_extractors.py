from daphne_context.models import UserInformation
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index, crop_list


def extract_example(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of examples
    examples = ["example1", "example2", "example3", "example4"]
    return sorted_list_of_features_by_index(processed_question, examples, number_of_features)


extract_function = {}
extract_function["example"] = extract_example