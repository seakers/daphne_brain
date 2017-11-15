import operator
import Levenshtein as lev
from sqlalchemy.orm import sessionmaker

import daphne_API.historian.models as models

def feature_list_by_ratio(processed_question, feature_list):
    """ Obtain a list of all the features in the list sorted by partial similarity to the question"""
    ratio_ordered = []
    length_question = len(processed_question.text)
    for feature in feature_list:
        length_feature = len(feature)
        if length_feature > length_question:
            ratio_ordered.append((feature, 0, -1))
        else:
            substrings = [processed_question.text[i:i+length_feature].lower() for i in range(length_question-length_feature+1)]
            ratios = [lev.ratio(substrings[i], feature.lower()) for i in range(length_question-length_feature+1)]
            max_index, max_ratio = max(enumerate(ratios), key=operator.itemgetter(1))
            ratio_ordered.append((feature, max_ratio, max_index))

    ratio_ordered = sorted(ratio_ordered, key=lambda ratio_info: -ratio_info[1])
    ratio_ordered = [ratio_info for ratio_info in ratio_ordered if ratio_info[1] > 0.75]
    return ratio_ordered


def crop_list(list, max_size):
    if len(list) > max_size:
        return list[:max_size]
    else:
        return list


def sorted_list_of_features_by_index(processed_question, feature_list, number_of_features):
    obt_feature_list = feature_list_by_ratio(processed_question, feature_list)
    obt_feature_list = crop_list(obt_feature_list, number_of_features)
    obt_feature_list = sorted(obt_feature_list, key=lambda ratio_info: ratio_info[2])
    obt_feature_list = [feature[0] for feature in obt_feature_list]
    return obt_feature_list


def extract_mission(processed_question, number_of_features, context):
    # Get a list of missions
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [' ' + mission.name.strip().lower() for mission in session.query(models.Mission).all()]
    return sorted_list_of_features_by_index(processed_question, missions, number_of_features)


def extract_measurement(processed_question, number_of_features, context):
    # Get a list of measurements
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip().lower() for measurement in session.query(models.Measurement).all()]
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_technology(processed_question, number_of_features, context):
    # Get a list of technologies and types
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in models.technologies]
    technologies = technologies + [type.name.strip().lower() for type in session.query(models.InstrumentType).all()]
    return sorted_list_of_features_by_index(processed_question, technologies, number_of_features)


def extract_date(processed_question, number_of_features, context):
    # For now just pick the years
    extracted_list = []
    for word in processed_question:
        if len(word) == 4 and word.like_num:
            extracted_list.append(word.text)

    return crop_list(extracted_list, number_of_features)


def extract_design_id(processed_question, number_of_features, context):
    # Get a list of design ids
    design_ids = ['d' + str(item['id']) for item in context['data']]
    extracted_list = []
    for word in processed_question:
        if word.text in design_ids:
            extracted_list.append(word.text)
    return crop_list(extracted_list, number_of_features)


def extract_agent(processed_question, number_of_features, context):
    agents = ["expert", "historian", "analyst", "explorer"]
    extracted_list = []
    for word in processed_question:
        if word.text in agents:
            extracted_list.append(word.text.lower)
    return crop_list(extracted_list, number_of_features)