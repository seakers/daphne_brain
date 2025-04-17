import os

import pandas
import scipy.io
import json
from sqlalchemy.orm import sessionmaker
from django.conf import settings

import EDL.data.model as edl_models
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index


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


extract_function = {}
extract_function["name"] = extract_edl_mission
extract_function["edl_mission"] = extract_edl_mission
extract_function["parameter"] = extract_edl_parameter
extract_function["edl_mat_file"] = extract_edl_mat_file
extract_function["edl_mat_param"] = extract_edl_mat_parameter
extract_function["extract_scorecard_filename"] = extract_scorecard_filename
extract_function["scorecard_edlmetricsheet_results"] = extract_edl_scorecard_edlmetricsheet
extract_function["edl_metric_calculate"] = edl_metric_calculate
extract_function["edl_metric_names"] = get_edl_metric_names
