import operator
import Levenshtein as lev
from sqlalchemy.orm import sessionmaker
import pandas
import daphne_API.historian.models as earth_models
from django.conf import settings
if 'EDL' in settings.ACTIVE_MODULES:
    import daphne_API.edl.model as edl_models
if 'EOSS' in settings.ACTIVE_MODULES:
    from daphne_API import problem_specific
from dialogue.models import EOSSContext, UserInformation
from django.conf import settings

import os
import scipy.io
import pandas as pd
import json


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


def extract_mission(processed_question, number_of_features, context: UserInformation):
    # Get a list of missions
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [' ' + mission.name.strip().lower() for mission in session.query(earth_models.Mission).all()]
    return sorted_list_of_features_by_index(processed_question, missions, number_of_features)


def extract_measurement(processed_question, number_of_features, context: UserInformation):
    # Get a list of measurements
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip().lower() for measurement in session.query(earth_models.Measurement).all()]
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_technology(processed_question, number_of_features, context: UserInformation):
    # Get a list of technologies and types
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in earth_models.technologies]
    technologies = technologies + [type.name.strip().lower() for type in session.query(earth_models.InstrumentType).all()]
    return sorted_list_of_features_by_index(processed_question, technologies, number_of_features)

def extract_space_agency(processed_question, number_of_features, context: UserInformation):
    # Get a list of technologies and types
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [' ' + agency.name.strip().lower() for agency in session.query(earth_models.Agency).all()]
    return sorted_list_of_features_by_index(processed_question, agencies, number_of_features)


def extract_date(processed_question, number_of_features, context: UserInformation):
    # For now just pick the years
    extracted_list = []
    for word in processed_question:
        if len(word) == 4 and word.like_num:
            extracted_list.append(word.text)

    return crop_list(extracted_list, number_of_features)


def extract_design_id(processed_question, number_of_features, context: UserInformation):
    # Get a list of design ids
    design_ids = ['d' + str(design.id) for design in context.eosscontext.design_set.all()]
    extracted_list = []
    for word in processed_question:
        if word.text in design_ids:
            extracted_list.append(word.text)
    return crop_list(extracted_list, number_of_features)


def extract_agent(processed_question, number_of_features, context: UserInformation):
    agents = ["expert", "historian", "analyst", "explorer"]
    extracted_list = []
    for word in processed_question:
        if word.lower_ in agents:
            extracted_list.append(word.lower_)
    return crop_list(extracted_list, number_of_features)


def extract_instrument_parameter(processed_question, number_of_features, context: UserInformation):
    instrument_parameters = \
        problem_specific.get_instruments_sheet(context.eosscontext.problem)['Attributes-for-object-Instrument']
    return sorted_list_of_features_by_index(processed_question, instrument_parameters, number_of_features)


def extract_vassar_instrument(processed_question, number_of_features, context: UserInformation):
    options = [instr["name"] for instr in problem_specific.get_instrument_dataset(context.eosscontext.problem)]
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_measurement(processed_question, number_of_features, context: UserInformation):
    param_names = problem_specific.get_param_names(context.eosscontext.problem)
    return sorted_list_of_features_by_index(processed_question, param_names, number_of_features)


def extract_vassar_stakeholder(processed_question, number_of_features, context: UserInformation):
    options = problem_specific.get_stakeholders_list(context.eosscontext.problem)
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)

def extract_vassar_objective(processed_question, number_of_features, context: EOSSContext):
    options = ["ATM" + str(i) for i in range(1,10)]
    options.extend(["OCE" + str(i) for i in range(1,10)])
    options.extend(["TER" + str(i) for i in range(1, 10)])
    options.extend(["WEA" + str(i) for i in range(1, 10)])
    options.extend(["CLI" + str(i) for i in range(1, 10)])
    options.extend(["ECO" + str(i) for i in range(1, 10)])
    options.extend(["WAT" + str(i) for i in range(1, 10)])
    options.extend(["HEA" + str(i) for i in range(1, 10)])
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



def extract_edl_mat_file(processed_question, number_of_features, context):
    '''Read folder and get list of possible mat files'''
    base_dir = '/Users/ssantini/Desktop/EDL_Simulation_Files/'
    all_subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(base_dir + d)]
    mat_files = []
    for name in all_subdirs:
        dir = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', name)
        mat_files.extend(os.listdir(dir))
    print(mat_files)
    print(all_subdirs)
    print(os.listdir(base_dir))
    return sorted_list_of_features_by_index(processed_question, mat_files, number_of_features)


def get_edl_metric_names(processed_question, number_of_features, context):
    with open('scorecard.json') as file:
        scorecard_json = json.load(file)
        scorecard_metrics = []
        for item in scorecard_json:
            if item['metric'] is not None:
                scorecard_metrics.append(item['metric'])
    return sorted_list_of_features_by_index(processed_question, scorecard_metrics, number_of_features)


def edl_metric_calculate(processed_question, number_of_features, context):
    with open('scorecard.json') as file:
        scorecard_json = json.load(file)
        scorecard_metrics = []
        for item in scorecard_json:
            if item['metric'] is not None:
                scorecard_metrics.append(item['metric'])
    return sorted_list_of_features_by_index(processed_question, scorecard_metrics, number_of_features)


if 'EDL' in settings.ACTIVE_MODULES:
    file_paths = os.path.join(settings.EDL_PATH, 'EDL_Simulation_Files', 'm2020', 'MC_test.mat')
    mat_dict = scipy.io.loadmat(file_paths)
    '''Get list of keys in mat dict'''
    list_items = list(mat_dict.keys())
    '''Get the NL description of the variable'''
    xls_path = os.path.join(settings.EDL_PATH, 'Code_Daphne/command_classifier/edlsimqueries.xlsx')
    file_path = pandas.read_excel(xls_path)
    list_descriptions = list(file_path[0])


def extract_edl_mat_parameter(processed_question, number_of_features, context):
    # TODO: extract a specific parameter from mat files
    mat_parameter = list_items  # mat_dict[random.choice(list_items)]
    mat_parameter = mat_parameter + list_descriptions
    #print(mat_parameter)
    return sorted_list_of_features_by_index(processed_question, mat_parameter, number_of_features)

def extract_scorecard_filename(processed_question, number_of_features,context):
    base_dir = '/Users/ssantini/Desktop/EDL_Simulation_Files/'
    all_subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(base_dir + d)]
    mat_file_name = []
    scorecard_name = []
    for name in all_subdirs:
        dir = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', name)
        mat_file_name.extend((os.listdir(dir)))
        for item in mat_file_name:
            scorecard_name.append(item.replace('.mat','.yml'))
    return sorted_list_of_features_by_index(processed_question, scorecard_name, number_of_features)


def extract_edl_POSTresult_scorecard(processed_question, number_of_features, context):
    # TODO: exrtact the POST results for a particular EDL metric
    df = pd.read_excel(
        '/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get data from sheet
    list_of_metrics = list(df[0])
    edl_metric_post_scorecard = list_of_metrics
    print(edl_metric_post_scorecard)
    return sorted_list_of_features_by_index(processed_question, edl_metric_post_scorecard, number_of_features)


def extract_edl_scorecard_edlmetricsheet(processed_question, number_of_features, context):
    # TODO: exrtact the POST results for a particular EDL metric
    edl_metric_edlsheet = ["Peak Decleration", "Parachute Deploy Mach Number", "Peak Parachute Inflation Load (MEV)",
                          "Parachute Deploy Range Error", "Timeline Margin", "Touchdown Vertical Velocity",
                          "Touchdown Horizontal Velocity", "Hazardous Landing Fraction", "Fuel Remaining", "Fuel Used",
                          "Range to Target", "TRN End-to-End Performance", "LVS Reduced Performance Timeline Margin",
                          "LVS Fine Mode Timeline Margin", "Probability of Success - Terrain Only",
                          "Parachute Deploy Flight Path Angle ", "TDS NAV INIT (Mode 20) Altitude ",
                          "Backshell Separation Altitude ", "Touchdown Ellipse Major Axis ",
                          "Touchdown Ellipse Minor Axis ", "MLE Priming Time ", "First Accordion Flown ",
                          "Mortar Fire Dynamic Pressure ", "Parachute Inflation Dynamic Pressure ",
                          "Peak Parachute Inflation Load (CBE) "]
    print(edl_metric_edlsheet)
    return sorted_list_of_features_by_index(processed_question, edl_metric_edlsheet, number_of_features)

