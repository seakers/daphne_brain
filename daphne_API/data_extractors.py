import operator
import Levenshtein as lev
from sqlalchemy.orm import sessionmaker
import pandas

import daphne_API.historian.models as models
import daphne_API.historian.models as earth_models
import daphne_API.edl.model as edl_models


instruments_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric/Climate-centric AttributeSet.xls', sheet_name='Instrument')
measurements_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric/Climate-centric AttributeSet.xls', sheet_name='Measurement')
param_names = []
for row in measurements_sheet.itertuples(index=True, name='Measurement'):
    if row[2] == 'Parameter':
        for i in range(6, len(row)):
            param_names.append(row[i])


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

    # Keep the longest string by default
    ratio_ordered = sorted(ratio_ordered, key=lambda ratio_info: -len(ratio_info[0]))
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

def extract_space_agency(processed_question, number_of_features, context):
    # Get a list of technologies and types
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [' ' + agency.name.strip().lower() for agency in session.query(models.Agency).all()]
    return sorted_list_of_features_by_index(processed_question, agencies, number_of_features)


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
        if word.lower_ in agents:
            extracted_list.append(word.lower_)
    return crop_list(extracted_list, number_of_features)


def extract_instrument_parameter(processed_question, number_of_features, context):
    return sorted_list_of_features_by_index(processed_question, instruments_sheet['Attributes-for-object-Instrument'], number_of_features)


def extract_vassar_instrument(processed_question, number_of_features, context):
    options = ["ACE_ORCA","ACE_POL","ACE_LID","CLAR_ERB","ACE_CPR","DESD_SAR","DESD_LID","GACM_VIS","GACM_SWIR","HYSP_TIR","POSTEPS_IRS","CNES_KaRIN"]
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_measurement(processed_question, number_of_features, context):
    return sorted_list_of_features_by_index(processed_question, param_names, number_of_features)


def extract_vassar_stakeholder(processed_question, number_of_features, context):
    options = ["atmospheric","oceanic","terrestrial"]
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)

def extract_vassar_objective(processed_question, number_of_features, context):
    options = ["ATM" + str(i) for i in range(1,10)]
    options.extend(["OCE" + str(i) for i in range(1,10)])
    options.extend(["TER" + str(i) for i in range(1, 10)])
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)

def extract_edl_mission(processed_question, number_of_features, context):
    # Get a list of missions
    engine = edl_models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [missions.name.strip().lower() for missions in session.query(edl_models.Mission).all()]
    return sorted_list_of_features_by_index(processed_question, missions, number_of_features)

def extract_edl_parameter(processed_question, number_of_features, context):
    # Get a list of parameters
    parameters = ["entry mass", "name", "full name", "status", "launch date", "launch vehicle", "applications",
                  "touchdown mass", "useful landed mass", "landing site elevation", "landing site", "entry strategy",
                  "entry vehicle","entry interface X","entry interface Y", "entry interface Z", "orbital direction",
                  "entry velocity", "entry lift control","entry attitude control", "entry guidance",
                  "entry angle of attack", "ballistic coefficient", "lift to drag ratio", "peak deceleration",
                  "descent attitude control", "drag coefficient", "deploy mach number", "deploy dynamic pressure",
                  "wind relative velocity", "altitude parachute deploy", "backshell separation altitude",
                  "backshell separation velocity", "backshell separation mechanism", "heat shield geometry",
                  "heat shield diameter", "heat shield TPS", "heat shield thickness",
                  "heat shield peak heat rate", "heat shield peak stagnation pressure", "horizontal velocity sensing",
                  "altitude sensing", "horizontal velocity control", "terminal descent decelerator",
                  "terminal descent velocity control", "vertical descent rate", "fuel burn",
                  "touchdown vertical velocity", "touchdown horizontal velocity", "touchdown attenuation",
                  "touchdown rock height capability", "touchdown slope capability", "touchdown sensor",
                  "touchdown sensing", "simulation"]
    return sorted_list_of_features_by_index(processed_question, parameters, number_of_features)



def extract_mat_file(processed_question, number_of_features,context):
    # TODO: Read folder and get list of possible mat files
    path = "/Users/ssantini/Code/EDL_Assistant_Brain/daphne_API/mat_files"
    mat_files = os.listdir(path)

    return sorted_list_of_features_by_index(processed_question, mat_files, number_of_features)

def extract_mat_parameter(processed_question, number_of_features, context):

    return(processed_question, parameter, context)
