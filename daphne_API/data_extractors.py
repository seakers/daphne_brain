import operator
import Levenshtein as lev
from sqlalchemy.orm import sessionmaker
import pandas

import daphne_API.historian.models as models
import daphne_API.historian.models as earth_models
import daphne_API.edl.model as edl_models
import os
import os, sys
import scipy.io
import fnmatch
import pandas as pd
import xlrd


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



def extract_edl_mat_file(processed_question, number_of_features,context):
    # TODO: Read folder and get list of possible mat files
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

file_paths = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', 'M2020', 'MC_test.mat')
mat_dict = scipy.io.loadmat(file_paths)
'''Get list of keys in mat dict'''
list_items = list(mat_dict.keys())
'''Get the NL description of the variable'''
file_path = pandas.read_excel('/Users/ssantini/Desktop/Code Daphne/command_classifier/edlsimqueries.xlsx')
list_descriptions = list(file_path[0])

def extract_edl_mat_parameter(processed_question, number_of_features, context):
    # TODO: extract a specific parameter from mat files
    mat_parameter = list_items  # mat_dict[random.choice(list_items)]
    mat_parameter = mat_parameter + list_descriptions
    print(mat_parameter)
    return sorted_list_of_features_by_index(processed_question, mat_parameter, number_of_features)


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


# edl_metric_summary = ["Number of Cases Run", "Any Failed Spec Criteria", "Flagged for Any Reason",
#                           "Time from cruise stage separation to flyway exceeded", "Fuel usage exceeds usable fuel",
#                           "Altitude AGL at TDS ground acquisition", "Time in Mode 21", "Time from EBM4 to PD",
#                           "Time from PD to HSS", "Guidance Prediction Error",
#                           "Guidance crossrange (based on lateral angle) at heading alignment",
#                           "Apollo Ranoff", "Trigger for Downrange for Parachute Deploy",
#                           "Range Error at Parachute Deploy", "Range to target", "Ellipse center distance from target",
#                           "Major axis ", "Minor axis", "Azimuth from North", "FSW fatals", "Late timepoint EVR",
#                           "GNC warning Hi/Lo EVRs", "Peak heat load exceeded (aerothermal)",
#                           "Peak heat rate exceeded (aerothermal)", "Peak shear exceeded (aerothermal)",
#                           "Peak pressure exceeded (aerothermal)", "Entry loads exceeded",
#                           "EBMD #1 recontact - minimum range at CPA exceeded",
#                           "EBMD #2 recontact - minimum range at CPA exceeded",
#                           "EBMD #3 recontact - minimum range at CPA exceeded",
#                           "EBMD #4 recontact - minimum range at CPA exceeded",
#                           "EBMD #5 recontact - minimum range at CPA exceeded",
#                           "EBMD #6 recontact - minimum range at CPA exceeded", "CBMD #1 recontact - within 10 m at CPA",
#                           "CBMD #2 recontact - within 10 m at CPA",
#                           "Cruise balance mass #1 separation conditions exceeded",
#                           "Cruise balance mass #2 separation conditions exceeded",
#                           "Angle of attack at parachute deploy exceeded (for parachute inflation qualification)",
#                           "Parachute deploy upper Mach exceeded", "Parachute deploy lower Mach exceeded",
#                           "Parachute inflation loads exceeded", "Mortar cover recontact (CPA to parachute apex <20 m)",
#                           "Angular acceleration or shear loads exceeded", "Heatshield separation above Mach threshold",
#                           "Heatshield separation at high angular rates", "Heatshield separation dynamic pressure exceeded",
#                           "Heatshield recontact", "Priming time less than 10 seconds (PV-5 to PV-6)",
#                           "BSS recontact (mid and long term)", "Backshell separation at high angular rates",
#                           "Backshell Separation at High Velocity (short term sep)",
#                           "Backshell Separation at Low Velocity (short term sep)", "BSS too low",
#                           "Throttledown Alt too High", "Throttledown Alt too Low", "Rover sep conditions exceeded",
#                           "Rover sep conditions exceeded", "Touchdown before diff release (TD too early)",
#                           "Touchdown rover vertical velocity exceeded", "Touchdown rover horizontal velocity exceeded",
#                           "Touchdown rover horizontal X velocity exceeded", "Touchdown rover horizontal Y velocity exceeded",
#                           "Descent stage impact", "Descent stage terrain impact prior to flyaway",
#                           "Heatshield Separation Mach Number", "Heatshield Separation Altitude AGL",
#                           "Peak Deceleration", "Peak Inflation Axial Load", "Parachute Deploy Upper Mach ",
#                           "Parachute Deploy Flight Path Angle", "Rover Max Vert Vel @ 1st Contact",
#                           "Rover Max Hor Vel @ 1st Contact", "Total Propellant Consumption",
#                           "Low Fuel Left (< 5 kg) in Tank # 1 at Descent Stage Impact",
#                           "Low Fuel Left (< 5 kg) in Tank # 2 at Descent Stage Impact",
#                           "Low Fuel Left (< 5 kg) in Tank # 3 at Descent Stage Impact"]