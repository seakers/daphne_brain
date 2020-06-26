import operator
import Levenshtein as lev


def feature_list_by_ratio(processed_question, feature_list, case_sensitive=False):
    """ Obtain a list of all the features in the list sorted by partial similarity to the question"""
    ratio_ordered = []
    length_question = len(processed_question.text)
    for feature in feature_list:
        length_feature = len(feature)
        if length_feature > length_question:
            ratio_ordered.append((feature, 0, -1))
        else:
            substrings = [processed_question.text[i:i+length_feature] for i in range(length_question-length_feature+1)]
            if case_sensitive:
                ratios = [lev.ratio(substrings[i], feature) for i in range(length_question-length_feature+1)]
            else:
                ratios = [lev.ratio(substrings[i].lower(), feature.lower()) for i in range(length_question - length_feature + 1)]
            max_index, max_ratio = max(enumerate(ratios), key=operator.itemgetter(1))
            ratio_ordered.append((feature, max_ratio, max_index))

    # Keep the longest string by default
    ratio_ordered = sorted(ratio_ordered, key=lambda ratio_info: -len(ratio_info[0]))
    ratio_ordered = sorted(ratio_ordered, key=lambda ratio_info: -ratio_info[1])
    ratio_ordered = [ratio_info for ratio_info in ratio_ordered if ratio_info[1] > 0.75]
    return ratio_ordered


def crop_list(full_list, max_size):
    if len(full_list) > max_size:
        return full_list[:max_size]
    else:
        return full_list


def sorted_list_of_features_by_index(processed_question, feature_list, number_of_features, case_sensitive=False):
    obt_feature_list = feature_list_by_ratio(processed_question, feature_list, case_sensitive)
    obt_feature_list = crop_list(obt_feature_list, number_of_features)
    obt_feature_list = sorted(obt_feature_list, key=lambda ratio_info: ratio_info[2])
    obt_feature_list = [feature[0] for feature in obt_feature_list]
    return obt_feature_list
