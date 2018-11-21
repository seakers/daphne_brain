import json
import numpy as np
import os

import pandas as pd
import scipy.io

from daphne_API import GetScorecardObjects


def EDL_load_mat_files(mission_name, mat_file, context):
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)
    context["current_mat_file"] = file_path
    context["current_mat_file_for_print"] = mat_file
    ''' ---------------For MATLAB Engine ------------------'''
    eng1.addpath(os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name), nargout = 0)

    mat_file_engine = eng1.load(mat_file)
    # TODO: ADD VARIABLE OF INTEREST TO ENGINE, NOT WHOLE MATFILE
    # eng1.workspace['dataset'] = mat_file_engine

    # eng1.disp('esto', nargout = 0)
    print('The current mat_file is:')
    print(mat_file)
    return 'file loaded'

def EDL_mat_file_list(mission_name,context):
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name)
    mat_files = os.listdir(file_path)
    result = []
    for mat_file in mat_files:
        result.append(
            {
                'command_result':mat_file
            }
        )
    return result


def EDL_compute_stat(mission_name,mat_file, param_name, context):
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

    for i in range(len(dict_NL)):
        key = param_name
        if key in dict_NL:
            param_name = dict_NL[param_name][0] # this returns the value of the key

        else:
            param_name = param_name
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)
    mat_dict = scipy.io.loadmat(file_path)
    '''Get list of keys in mat dict'''
    list_keys = list(mat_dict.keys())
    param_array = mat_dict[param_name]
    max = np.amax(param_array)
    min = np.amin(param_array)
    mean = np.mean(param_array)
    variance = np.var(param_array)
    std_dev = np.std(param_array)
    plus_three_sig = np.mean(param_array) + 3 * np.std(param_array)
    minus_three_sig = np.mean(param_array) - 3 * np.std(param_array)
    percentile013 = np.percentile(param_array, 0.13)
    percentile1 = np.percentile(param_array, 1)
    percentile10 = np.percentile(param_array, 10)
    percentile50 = np.percentile(param_array, 50)
    percentile99 = np.percentile(param_array, 99)
    percentile99_87 = np.percentile(param_array, 99.87)
    high99_87_minus_median = np.percentile(param_array, 99.87) - np.median(param_array)
    high99_87_minus_mean = np.percentile(param_array, 99.87) - np.median(param_array)
    median_minus_low_99_87 = np.median(param_array) - np.percentile(param_array, 0.13)
    mean_minus_low_99_87 = np.mean(param_array) - np.percentile(param_array, 0.13)

    name_of_stat = ["max", "min", "mean", "variance", "std", "3s", "mean", "-3s", "0.13%", "1.00%", "10.00%", "50.00%",
                    "90.00%",
                    "99.87", "high 99.89 - median", "high 99.87 - mean", "median - low 99.87",
                    "mean - low 99.87"]

    value_of_stat = [max, min, mean, variance, std_dev, plus_three_sig, mean, minus_three_sig, percentile013,
                     percentile1,
                     percentile10, percentile50, percentile99, percentile99_87, high99_87_minus_median,
                     high99_87_minus_mean,
                     median_minus_low_99_87, mean_minus_low_99_87]
    '''Now we want to create a  list as the one in the list sim data query'''
    # from daphne_API.MatEngine_object import eng1
    # eng1.eval('2+2')
    # eng1.load(eval(file_path))
    # eng1.eval('disp(esto)')

    stat = []
    for name, value in zip(name_of_stat, value_of_stat):
        stat.append(
            {
                'command_result': " = ".join([name, value.astype(str)])
            }
        )

    ''' Save parameter into csv file for plotting'''
    filename = str(param_name)+'.csv'
    np.savetxt(filename, param_array, delimiter=',', header=param_name, comments="")
    return stat

def load_scorecard(mission_name, mat_file, context):

    ''' Set Paths:
     1. mat file path;
     2. the scorecard template path''
     '''
    mat_file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', mission_name, mat_file)
    scorecard_template_path = '"/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardTemplate.xlsx"'


    ''' Connect to the local computer and generate scorecard'''
    os.system('echo $SHELL')
    os.system('setenv DYLD_FALLBACK_LIBRARY_PATH $LD_LIBRARY_PATH')
    # The scorecard ruby location is: /Volumes/Encrypted/Mars2020/mars2020/bin/scorecard.rb'''
    # The Scorecard template is: /Users/ssantini/Code/ExtractDataMatlab/ScoreCardTemplate.xlsx '''
    os.system('~/scorecard.rb --help')
    os.system('pushd "~/Users/ssantini/Desktop/Code Daphne/daphne_brain/"')
    os.system('pwd')
    os.environ['MATLAB_PATH']= "/Volumes/Encrypted/Mars2020/mars2020/MATLAB/"
    print(os.environ['MATLAB_PATH'])
    os.system(('~/scorecard.rb --yaml --template="/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardTemplate.xlsx"') + ' ' + mat_file_path)

    ''' Rename the Scorecard to the mat file'''
    scorecard_temp_path = mat_file.replace(".mat", "")
    scorecard_name = os.path.basename(scorecard_temp_path)+'.yml'
    scorecard_path = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', scorecard_name)
    if os.path.isfile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/scorecard.yml'):
        os.rename('/Users/ssantini/Desktop/Code Daphne/daphne_brain/scorecard.yml', scorecard_path)

    context["current_scorecard"] = scorecard_path
    return 'Score Card Loaded and Populated'


def get_scorecard_post_results(edl_scorecard,scorecard_post_param, context):
    path_scorecard = '/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx'
    scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

    [summary_outofspec, decision_meeting, edl_metric, trn, bud_metrics, entry, parachute_descent, powered_flight,
     edltimeline, comms, telecom, efc, summary, failure, detailed,
     list_of_metrics] = GetScorecardObjects.get_scorecard_objects_and_metrics(scorecard, path_scorecard)

    df = pd.read_excel(
        '/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get data from sheet
    list_of_metrics = list(df[0])

    '''Here we want to get the call values to convert to a dictionary using the NL language descriptions'''
    '''This dictionary is to get the POST results with the units'''
    keys_dict_summoutofspec = []
    keys_dict_summoutofspec_post = []
    keys_dict_summoutofspec_units = []
    keys_dict_summoutofspec_gless = []
    keys_dict_summoutofspec_flag = []
    keys_dict_summoutofspec_outofspec = []
    keys_dict_summoutofspec_description = []

    keys_dict_decision_meeting = []
    keys_dict_decision_meeting_post = []
    keys_dict_decision_meeting_units = []
    keys_dict_decision_meeting_gless = []
    keys_dict_decision_meeting_flag = []
    keys_dict_decision_meeting_outofspec = []
    keys_dict_decision_meeting_description = []

    keys_dict_edlmetrics = []
    keys_dict_edlmetrics_post = []
    keys_dict_edlmetrics_units = []
    keys_dict_edlmetrics_gless = []
    keys_dict_edlmetrics_flag = []
    keys_dict_edlmetrics_outofspec = []
    keys_dict_edlmetrics_description = []

    keys_dict_trn = []
    keys_dict_trn_post = []
    keys_dict_trn_units = []
    keys_dict_trn_gless = []
    keys_dict_trn_flag = []
    keys_dict_trn_outofspec = []
    keys_dict_trn_description = []

    keys_dict_bud = []
    keys_dict_bud_post = []
    keys_dict_bud_units = []
    keys_dict_bud_gless = []
    keys_dict_bud_flag = []
    keys_dict_bud_outofspec = []
    keys_dict_bud_description = []

    keys_dict_entry = []
    keys_dict_entry_post = []
    keys_dict_entry_units = []
    keys_dict_entry_gless = []
    keys_dict_entry_flag = []
    keys_dict_entry_outofspec = []
    keys_dict_entry_description = []

    keys_dict_parachute = []
    keys_dict_parachute_post = []
    keys_dict_parachute_units = []
    keys_dict_parachute_gless = []
    keys_dict_parachute_flag = []
    keys_dict_parachute_outofspec = []
    keys_dict_parachute_description = []

    keys_dict_poweredflight = []
    keys_dict_poweredflight_post = []
    keys_dict_poweredflight_units = []
    keys_dict_poweredflight_gless = []
    keys_dict_poweredflight_flag = []
    keys_dict_poweredflight_outofpec = []
    keys_dict_poweredflight_description = []

    keys_dict_timeline = []
    keys_dict_timeline_post = []
    keys_dict_timeline_units = []
    keys_dict_timeline_gless = []
    keys_dict_timeline_flag = []
    keys_dict_timeline_outofspec = []
    keys_dict_timeline_description = []

    keys_dict_edlcom = []
    keys_dict_edlcom_post = []
    keys_dict_edlcom_units = []
    keys_dict_edlcom_gless = []
    keys_dict_edlcom_flag = []
    keys_dict_edlcom_outofspec = []
    keys_dict_edlcom_description = []

    keys_dict_telecom = []
    keys_dict_telecom_post = []
    keys_dict_telecom_units = []
    keys_dict_telecom_gless = []
    keys_dict_telecom_flag = []
    keys_dict_telecom_outofspec = []
    keys_dict_telecom_description = []

    keys_dict_efc = []
    keys_dict_efc_post = []
    keys_dict_efc_units = []
    keys_dict_efc_gless = []
    keys_dict_efc_flag = []
    keys_dict_efc_outofspec = []
    keys_dict_efc_description = []

    keys_dict_summary = []
    keys_dict_summary_post = []
    keys_dict_summary_units = []
    keys_dict_summary_gless = []
    keys_dict_summary_flag = []
    keys_dict_summary_outofspec = []
    keys_dict_summary_description = []

    keys_dict_failures = []
    keys_dict_failures_post = []
    keys_dict_failures_units = []
    keys_dict_failures_gless = []
    keys_dict_failures_flag = []
    keys_dict_failures_outofspec = []
    keys_dict_failures_description = []

    keys_dict_detailed = []
    keys_dict_detailed_post = []
    keys_dict_detailed_units = []
    keys_dict_detailed_gless = []
    keys_dict_detailed_flag = []
    keys_dict_detailed_outofspec = []
    keys_dict_detailed_description = []

    for i in range(len(summary_outofspec.entries)):
        keys_dict_summoutofspec.append('summary_outofspec.entries[' + str(i) + '].name')
        keys_dict_summoutofspec_post.append('summary_outofspec.entries[' + str(i) + '].POST_results')
        keys_dict_summoutofspec_units.append('summary_outofspec.entries[' + str(i) + '].units')
        keys_dict_summoutofspec_flag.append('summary_outofspec.entries[' + str(i) + '].Flag')
        keys_dict_summoutofspec_gless.append('summary_outofspec.entries[' + str(i) + '].GreatOrLess')
        keys_dict_summoutofspec_outofspec.append('summary_outofspec.entries[' + str(i) + '].OutOfSpec')
        keys_dict_summoutofspec_description.append('summary_outofspec.entries[' + str(i) + '].Description')
    for i in range(len(decision_meeting.entries)):
        keys_dict_decision_meeting.append('decision_meeting.entries[' + str(i) + '].name')
        keys_dict_decision_meeting_post.append('decision_meeting.entries[' + str(i) + '].POST_results')
        keys_dict_decision_meeting_units.append('decision_meeting.entries[' + str(i) + '].units')
        keys_dict_decision_meeting_flag.append('decision_meeting.entries[' + str(i) + '].Flag')
        keys_dict_decision_meeting_gless.append('decision_meeting.entries[' + str(i) + '].GreatOrLess')
        keys_dict_decision_meeting_outofspec.append('decision_meeting.entries[' + str(i) + '].OutOfSpec')
        keys_dict_decision_meeting_description.append('decision_meeting.entries[' + str(i) + '].Description')
    for i in range(len(edl_metric.entries)):
        keys_dict_edlmetrics.append('edl_metric.entries[' + str(i) + '].name')
        keys_dict_edlmetrics_post.append('edl_metric.entries[' + str(i) + '].POST_results')
        keys_dict_edlmetrics_units.append('edl_metric.entries[' + str(i) + '].units')
        keys_dict_edlmetrics_flag.append('edl_metric.entries[' + str(i) + '].Flag')
        keys_dict_edlmetrics_gless.append('edl_metric.entries[' + str(i) + '].GreatOrLess')
        keys_dict_edlmetrics_outofspec.append('edl_metric.entries[' + str(i) + '].OutOfSpec')
        keys_dict_edlmetrics_description.append('edl_metric.entries[' + str(i) + '].Description')
    for i in range(len(trn.entries)):
        keys_dict_trn.append('trn.entries[' + str(i) + '].name')
        keys_dict_trn_post.append('trn.entries[' + str(i) + '].POST_results')
        keys_dict_trn_units.append('trn.entries[' + str(i) + '].units')
        keys_dict_trn_flag.append('trn.entries[' + str(i) + '].Flag')
        keys_dict_trn_gless.append('trn.entries[' + str(i) + '].GreatOrLess')
        keys_dict_trn_outofspec.append('trn.entries[' + str(i) + '].OutOfSpec')
        keys_dict_trn_description.append('trn.entries[' + str(i) + '].Description')
    for i in range(len(bud_metrics.entries)):
        keys_dict_bud.append('bud_metrics.entries[' + str(i) + '].name')
        keys_dict_bud_post.append('bud_metrics.entries[' + str(i) + '].POST_results')
        keys_dict_bud_units.append('bud_metrics.entries[' + str(i) + '].units')
        keys_dict_bud_flag.append('bud_metrics.entries[' + str(i) + '].Flag')
        keys_dict_bud_gless.append('bud_metrics.entries[' + str(i) + '].GreatOrLess')
        keys_dict_bud_outofspec.append('bud_metrics.entries[' + str(i) + '].OutOfSpec')
        keys_dict_bud_description.append('bud_metrics.entries[' + str(i) + '].Description')
    for i in range(len(entry.entries)):
        keys_dict_entry.append('entry.entries[' + str(i) + '].name')
        keys_dict_entry_post.append('entry.entries[' + str(i) + '].POST_results')
        keys_dict_entry_units.append('entry.entries[' + str(i) + '].units')
        keys_dict_entry_flag.append('entry.entries[' + str(i) + '].Flag')
        keys_dict_entry_gless.append('entry.entries[' + str(i) + '].GreatOrLess')
        keys_dict_entry_outofspec.append('entry.entries[' + str(i) + '].OutOfSpec')
        keys_dict_entry_description.append('entry.entries[' + str(i) + '].Description')
    for i in range(len(parachute_descent.entries)):
        keys_dict_parachute.append('parachute_descent.entries[' + str(i) + '].name')
        keys_dict_parachute_post.append('parachute_descent.entries[' + str(i) + '].POST_results')
        keys_dict_parachute_units.append('parachute_descent.entries[' + str(i) + '].units')
        keys_dict_parachute_flag.append('parachute_descent.entries[' + str(i) + '].Flag')
        keys_dict_parachute_gless.append('parachute_descent.entries[' + str(i) + '].GreatOrLess')
        keys_dict_parachute_outofspec.append('parachute_descent.entries[' + str(i) + '].OutOfSpec')
        keys_dict_parachute_description.append('parachute_descent.entries[' + str(i) + '].Description')
    for i in range(len(powered_flight.entries)):
        keys_dict_poweredflight.append('powered_flight.entries[' + str(i) + '].name')
        keys_dict_poweredflight_post.append('powered_flight.entries[' + str(i) + '].POST_results')
        keys_dict_poweredflight_units.append('powered_flight.entries[' + str(i) + '].units')
        keys_dict_poweredflight_flag.append('powered_flight.entries[' + str(i) + '].Flag')
        keys_dict_poweredflight_gless.append('powered_flight.entries[' + str(i) + '].GreatOrLess')
        keys_dict_poweredflight_outofpec.append('powered_flight.entries[' + str(i) + '].OutOfSpec')
        keys_dict_poweredflight_description.append('powered_flight.entries[' + str(i) + '].Description')
    for i in range(len(edltimeline.entries)):
        keys_dict_timeline.append('edltimeline.entries[' + str(i) + '].name')
        keys_dict_timeline_post.append('edltimeline.entries[' + str(i) + '].POST_results')
        keys_dict_timeline_units.append('edltimeline.entries[' + str(i) + '].units')
        keys_dict_timeline_flag.append('edltimeline.entries[' + str(i) + '].Flag')
        keys_dict_timeline_gless.append('edltimeline.entries[' + str(i) + '].GreatOrLess')
        keys_dict_timeline_outofspec.append('edltimeline.entries[' + str(i) + '].OutOfSpec')
        keys_dict_timeline_description.append('edltimeline.entries[' + str(i) + '].Description')
    for i in range(len(comms.entries)):
        keys_dict_edlcom.append('comms.entries[' + str(i) + '].name')
        keys_dict_edlcom_post.append('comms.entries[' + str(i) + '].POST_results')
        keys_dict_edlcom_units.append('comms.entries[' + str(i) + '].units')
        keys_dict_edlcom_flag.append('comms.entries[' + str(i) + '].Flag')
        keys_dict_edlcom_gless.append('comms.entries[' + str(i) + '].GreatOrLess')
        keys_dict_edlcom_outofspec.append('comms.entries[' + str(i) + '].OutOfSpec')
        keys_dict_edlcom_description.append('comms.entries[' + str(i) + '].Description')
    for i in range(len(telecom.entries)):
        keys_dict_telecom.append('telecom.entries[' + str(i) + '].name')
        keys_dict_telecom_post.append('telecom.entries[' + str(i) + '].POST_results')
        keys_dict_telecom_units.append('telecom.entries[' + str(i) + '].units')
        keys_dict_telecom_flag.append('telecom.entries[' + str(i) + '].Flag')
        keys_dict_telecom_gless.append('telecom.entries[' + str(i) + '].GreatOrLess')
        keys_dict_telecom_outofspec.append('telecom.entries[' + str(i) + '].OutOfSpec')
        keys_dict_telecom_description.append('telecom.entries[' + str(i) + '].Description')
    for i in range(len(efc.entries)):
        keys_dict_efc.append('efc.entries[' + str(i) + '].name')
        keys_dict_efc_post.append('efc.entries[' + str(i) + '].POST_results')
        keys_dict_efc_units.append('efc.entries[' + str(i) + '].units')
        keys_dict_efc_flag.append('efc.entries[' + str(i) + '].Flag')
        keys_dict_efc_gless.append('efc.entries[' + str(i) + '].GreatOrLess')
        keys_dict_efc_outofspec.append('efc.entries[' + str(i) + '].OutOfSpec')
        keys_dict_efc_description.append('efc.entries[' + str(i) + '].Description')
    for i in range(len(summary.entries)):
        keys_dict_summary.append('summary.entries[' + str(i) + '].name')
        keys_dict_summary_post.append('summary.entries[' + str(i) + '].POST_results')
        keys_dict_summary_units.append('summary.entries[' + str(i) + '].units')
        keys_dict_summary_flag.append('summary.entries[' + str(i) + '].Flag')
        keys_dict_summary_gless.append('summary.entries[' + str(i) + '].GreatOrLess')
        keys_dict_summary_outofspec.append('summary.entries[' + str(i) + '].OutOfSpec')
        keys_dict_summary_description.append('summary.entries[' + str(i) + '].Description')
    for i in range(len(failure.entries)):
        keys_dict_failures.append('failure.entries[' + str(i) + '].name')
        keys_dict_failures_post.append('failure.entries[' + str(i) + '].POST_results')
        keys_dict_failures_units.append('failure.entries[' + str(i) + '].units')
        keys_dict_failures_flag.append('failure.entries[' + str(i) + '].Flag')
        keys_dict_failures_gless.append('failure.entries[' + str(i) + '].GreatOrLess')
        keys_dict_failures_outofspec.append('failure.entries[' + str(i) + '].OutOfSpec')
        keys_dict_failures_description.append('failure.entries[' + str(i) + '].Description')
    for i in range(len(detailed.entries)):
        keys_dict_detailed.append('detailed.entries[' + str(i) + '].name')
        keys_dict_detailed_post.append('detailed.entries[' + str(i) + '].POST_results')
        keys_dict_detailed_units.append('detailed.entries[' + str(i) + '].units')
        keys_dict_detailed_flag.append('detailed.entries[' + str(i) + '].Flag')
        keys_dict_detailed_gless.append('detailed.entries[' + str(i) + '].GreatOrLess')
        keys_dict_detailed_outofspec.append('detailed.entries[' + str(i) + '].OutOfSpec')
        keys_dict_detailed_description.append('detailed.entries[' + str(i) + '].Description')

    # esoes = eval(keys_dict_entry[:])
    '''Create single list of post results and units'''

    post_dict_value = [keys_dict_summoutofspec_post + keys_dict_decision_meeting_post + keys_dict_edlmetrics_post +
                       keys_dict_trn_post + keys_dict_bud_post + keys_dict_entry_post + keys_dict_parachute_post +
                       keys_dict_poweredflight_post + keys_dict_timeline_post + keys_dict_edlcom_post +
                       keys_dict_telecom_post + keys_dict_efc_post + keys_dict_summary_post + keys_dict_failures_post +
                       keys_dict_detailed_post]
    post_dict_value = [item for items in post_dict_value for item in items]

    units_dict_value = [keys_dict_summoutofspec_units + keys_dict_decision_meeting_units + keys_dict_edlmetrics_units +
                        keys_dict_trn_units + keys_dict_bud_units + keys_dict_entry_units + keys_dict_parachute_units +
                        keys_dict_poweredflight_units + keys_dict_timeline_units + keys_dict_edlcom_units +
                        keys_dict_telecom_units + keys_dict_efc_units + keys_dict_summary_units + keys_dict_failures_units +
                        keys_dict_detailed_units]
    units_dict_value = [item for items in units_dict_value for item in items]

    flag_dict_value = [keys_dict_summoutofspec_flag + keys_dict_decision_meeting_flag + keys_dict_edlmetrics_flag +
                       keys_dict_trn_flag + keys_dict_bud_flag + keys_dict_entry_flag + keys_dict_parachute_flag +
                       keys_dict_poweredflight_flag + keys_dict_timeline_flag + keys_dict_edlcom_flag +
                       keys_dict_telecom_flag + keys_dict_efc_flag + keys_dict_summary_flag + keys_dict_failures_flag +
                       keys_dict_detailed_flag]
    flag_dict_value = [(item) for (items) in flag_dict_value for (item) in (items)]

    gless_dict_value = [keys_dict_summoutofspec_gless + keys_dict_decision_meeting_gless + keys_dict_edlmetrics_gless +
                        keys_dict_trn_gless + keys_dict_bud_gless + keys_dict_entry_gless + keys_dict_parachute_gless +
                        keys_dict_poweredflight_gless + keys_dict_timeline_gless + keys_dict_edlcom_gless +
                        keys_dict_telecom_gless + keys_dict_efc_gless + keys_dict_summary_gless + keys_dict_failures_gless +
                        keys_dict_detailed_gless]
    gless_dict_value = [item for items in gless_dict_value for item in items]

    outofspec_dict_value = [
        keys_dict_summoutofspec_outofspec + keys_dict_decision_meeting_outofspec + keys_dict_edlmetrics_outofspec +
        keys_dict_trn_outofspec + keys_dict_bud_outofspec + keys_dict_entry_outofspec
        + keys_dict_parachute_outofspec +
        keys_dict_poweredflight_outofpec + keys_dict_timeline_outofspec + keys_dict_edlcom_outofspec +
        keys_dict_telecom_outofspec + keys_dict_efc_outofspec + keys_dict_summary_outofspec + keys_dict_failures_outofspec +
        keys_dict_detailed_outofspec]
    outofspec_dict_value = [item for items in outofspec_dict_value for item in items]


    description_dict_value = [keys_dict_summoutofspec_description + keys_dict_decision_meeting_description +
                              keys_dict_edlmetrics_description + keys_dict_trn_description + keys_dict_bud_description +
                              keys_dict_entry_description + keys_dict_parachute_description +
                              keys_dict_poweredflight_description + keys_dict_timeline_gless + keys_dict_edlcom_description +
                              keys_dict_telecom_description + keys_dict_efc_description + keys_dict_summary_description +
                              keys_dict_failures_description + keys_dict_detailed_description]
    description_dict_value = [item for items in description_dict_value for item in items]

    '''================================================== Dictionary =================================================='''
    list_of_lists_all = [list_of_metrics, post_dict_value, units_dict_value, gless_dict_value, flag_dict_value,
                         outofspec_dict_value]

    for i in range(len(post_dict_value)):
        post_dict_value[i] = eval(post_dict_value[i])
        units_dict_value[i] = eval(units_dict_value[i])
        flag_dict_value[i] = eval(flag_dict_value[i])
        gless_dict_value[i] = eval(gless_dict_value[i])
        outofspec_dict_value[i] = eval(outofspec_dict_value[i])
        description_dict_value[i] = eval(description_dict_value[i])

    all_metrics_dict = {z[0]: (list((z[1:]))) for (z) in zip(*list_of_lists_all)}

    value =(str(all_metrics_dict[scorecard_post_param][0]))
    units = str(all_metrics_dict[scorecard_post_param][1])
    scorecard_post_result_returned = str(value) + " " + str(units)

    '''Save the dictionary'''
    json.dump(all_metrics_dict, open("/Users/ssantini/Desktop/Code Daphne/daphne_brain/dict_for_flags_outofspec.txt",
              'w'))

    return scorecard_post_result_returned

def get_flag_summary(edl_scorecard, context, *flag_type):

    '''================================================== Get flagged values ===================================='''
    dict_NL = json.load(open("/Users/ssantini/Desktop/Code Daphne/daphne_brain/dict_for_flags_outofspec.txt"))
    all_metrics_dict = dict_NL

    df = pd.read_excel(
        '/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get renamed metrics
    list_of_metrics = list(df[0]) # made some modifications

    flagged_metrics = []
    flagged_value = []
    flagged_unit = []
    flagged_operator = []
    flagged_flagval = []
    flagged_note = []

    outofspec_metrics = []
    outofspec_value = []
    outofspec_unit = []
    outofspec_operator = []
    outofspec_outofspec = []
    outofspec_note = []

    for item in list_of_metrics:
        value = (str((all_metrics_dict[item][0])))
        unit = (str((all_metrics_dict[item][1])))
        operator = (str((all_metrics_dict[item][2])))
        flag_val = (str((all_metrics_dict[item][3])))
        outofspec_val = (str((all_metrics_dict[item][4])))
        if value != 'nan' and operator != 'nan' and flag_val != 'nan' and outofspec_val != 'nan':
            if eval(str(value) + str(operator) + str(flag_val)) == False \
                    and eval(str(value) + str(operator) + str(outofspec_val)) == True:
                flagged_metrics.append(item)
                flagged_value.append(value)
                flagged_unit.append(unit)
                flagged_operator.append(str(operator))
                flagged_flagval.append(str(flag_val))
                flagged_note.append(str('is not satisfied'))
            if eval(str(value) + str(operator) + str(flag_val)) == False \
                    and eval(str(value) + str(operator) + str(outofspec_val)) == False:
                outofspec_metrics.append(item)
                outofspec_value.append((value))
                outofspec_unit.append((unit))
                outofspec_operator.append(str(operator))
                outofspec_outofspec.append(str(flag_val))
                outofspec_note.append(str('is not satisfied'))
    if ('flagged_results' in flag_type):
        flagged_values = []
        for name, value, unit, operator, flagval, note in zip(flagged_metrics, flagged_value, flagged_unit, flagged_operator,
                                                        flagged_flagval, flagged_note):
            flagged_values.append(
                {
                    'command_result': "  ".join([name, value, operator, flagval, unit, note])
                }
            )
        return flagged_values
    if ('outofspec_results' in flag_type):
        out_of_spec_values = []
        for name, value, unit, operator, flagval, note in zip(outofspec_metrics, outofspec_value, outofspec_unit,
                                                              outofspec_operator, outofspec_outofspec, outofspec_note):
            out_of_spec_values.append(
                {
                    'command_result': "  ".join([name, value, operator, flagval, unit, note])
                }
            )
        return out_of_spec_values

def get_scorecard_post_results_edlmetrics(edl_scorecard,scorecard_post_param, context):
    path_scorecard = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', edl_scorecard)
    scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

    '''Here we get all lists from all metrics and fields'''
    NAMES_EDLSHEET = []
    TYPES_EDLSHEET = []
    UNITS_EDLSHEET = []
    GREATORLESSS_EDL_SHEET = []
    POST_RESULTS_EDLSHEET = []
    FLAG_EDLSHEET = []
    OUTOFSPEC_EDLSHEET = []
    DESCRIPT_EDLSHEET = []
    CALC_EDLSHEET = []

    '''Remove all of the fields we dont want'''
    sheets = scorecard.sheet_names
    for sheet in sheets:
        df = pd.read_excel('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx', sheet_name=sheet)  # get data from sheet
        column_names = list(df.columns)
        metric_col = column_names[1]  # metric sheet will be the reference for deleting empty rows or label rows
        length_col = len(df[metric_col])  # original number of rows in the excel sheet
        if sheet == sheets[0]:
            for i in range(length_col):
                algo = df[metric_col][i]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric':
                    df.drop([i], inplace=True)
                    DF_EDLMETRICS = df

            NAMES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[1]]))
            TYPES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[2]]))
            UNITS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[3]]))
            POST_RESULTS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[4]]))
            GREATORLESSS_EDL_SHEET.append(list(DF_EDLMETRICS[column_names[5]]))
            FLAG_EDLSHEET.append(list(DF_EDLMETRICS[column_names[6]]))
            OUTOFSPEC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[7]]))
            CALC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[10]]))
            DESCRIPT_EDLSHEET.append(list(DF_EDLMETRICS[column_names[9]]))

    '''Create objects and classes'''

    class ScoreCardCategory(object):
        def __init__(self, name=0, entries=0):
            self.name = name  # these are the tab names (categories)
            self.entries = entries  # These are all the metrics in each

        def __call__(self, name, entries):
            print(name)
            print(entries)

    class ScoreCardMetrics(object):
        def __init__(self, name=0, type=0, units=0, POST_results=0, GreatOrLess=0, Flag=0, OutOfSpec=0, Enum=0,
                     Description=0, Calculation=0, CalculationCheckedBy=0, MetricCheckedBy=0, FlagOutOfSpecOwner=0):
            self.name = name
            self.type = type
            self.units = units
            self.POST_results = POST_results
            self.GreatOrLess = GreatOrLess
            self.Flag = Flag
            self.OutOfSpec = OutOfSpec
            self.Enum = Enum
            self.Description = Description
            self.Calculation = Calculation
            self.CalculationCheckedBy = CalculationCheckedBy
            self.MetricCheckedBy = MetricCheckedBy
            self.FlagOutOfSpecOwner = FlagOutOfSpecOwner

        def __call__(self, name, type, units, POST_results, GreatOrLess, Flag, OutOfSpec, Enum,
                     Description, Calculation, CalculationCheckedBy, MetricCheckedBy, FlagOutOfSpecOwner):
            print(name)
            print(type)
            print(units)
            print(POST_results)
            print(GreatOrLess)
            print(Flag)
            print(OutOfSpec)
            print(Enum)
            print(Description)
            print(Calculation)
            print(CalculationCheckedBy)
            print(MetricCheckedBy)
            print(FlagOutOfSpecOwner)

    METRIC_OBJECTS_GROUPED_EDLMETRIC = []
    METRIC_OBJECTS_EDLMETRIC = []
    for i in range(len(NAMES_EDLSHEET[0])):  # number of metrics in each sheet
        METRIC_OBJECTS_EDLMETRIC.append(ScoreCardMetrics(name=NAMES_EDLSHEET[0][i], type=TYPES_EDLSHEET[0][i],
                                                         units=UNITS_EDLSHEET[0][i],
                                                         POST_results=POST_RESULTS_EDLSHEET[0][i],
                                                         GreatOrLess=GREATORLESSS_EDL_SHEET[0][i],
                                                         Flag=FLAG_EDLSHEET[0][i],
                                                         OutOfSpec=OUTOFSPEC_EDLSHEET[0][i], Enum=0,
                                                         Description=DESCRIPT_EDLSHEET[0][i],
                                                         Calculation=CALC_EDLSHEET[0][i], CalculationCheckedBy=0,
                                                         MetricCheckedBy=0, FlagOutOfSpecOwner=0))
        METRIC_OBJECTS = list(METRIC_OBJECTS_EDLMETRIC)
    METRIC_OBJECTS_GROUPED_EDLMETRIC.append(METRIC_OBJECTS)

    edl_metric_objects = METRIC_OBJECTS_GROUPED_EDLMETRIC[0]
    edl_metric = ScoreCardCategory(scorecard.sheet_names[0], edl_metric_objects)

    '''Here we want to get the call values to convert to a dictionary using the NL language descriptions'''
    '''This dictionary is to get the POST results with the units'''
    value_edlmetric_name = []
    value_edlmetric_units = []
    value_edlmetric_post = []
    value_edlmetric_type = []
    value_edlmetric_greatorless = []
    value_edlmetric_flag = []
    value_edlmetric_description = []
    value_edlmetric_outofspec = []

    for i in range(len(edl_metric_objects)):
        value_edlmetric_type.append('edl_metric.entries[' + str(i) + '].type')
        value_edlmetric_units.append('edl_metric.entries[' + str(i) + '].units')
        value_edlmetric_post.append('edl_metric.entries[' + str(i) + '].POST_results')
        value_edlmetric_greatorless.append('edl_metric.entries[' + str(i) + '].GreatOrLess')
        value_edlmetric_flag.append('edl_metric.entries[' + str(i) + '].Flag')
        value_edlmetric_outofspec.append('edl_metric.entries[' + str(i) + '].OutofSpec')
        value_edlmetric_description.append('edl_metric.entries[' + str(i) + '].Description')

    '''=========================================Dictionary========================================================='''
    list_of_metrics_edlmetric = [item for items in NAMES_EDLSHEET for item in items]
    list_of_lists = [list_of_metrics_edlmetric, value_edlmetric_type, value_edlmetric_units, value_edlmetric_post,
                     value_edlmetric_greatorless, value_edlmetric_flag, value_edlmetric_outofspec,
                     value_edlmetric_description]
    dictionary_edlmetrics = {z[0]: list(z[1:]) for z in zip(*list_of_lists)}

    value = eval(dictionary_edlmetrics[scorecard_post_param][2])
    units = eval(dictionary_edlmetrics[scorecard_post_param][1])
    scorecard_post_result_returned_edlmetrics = str(value) + " " + units
    return scorecard_post_result_returned_edlmetrics

# def get_scorecard_sumamry_edlmetrics(edl_scorecard, context):
#     path_scorecard = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', edl_scorecard)
#     scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

#     '''Here we get all lists from all metrics and fields'''
#     NAMES_EDLSHEET = []
#     TYPES_EDLSHEET = []
#     UNITS_EDLSHEET = []
#     GREATORLESSS_EDL_SHEET = []
#     POST_RESULTS_EDLSHEET = []
#     FLAG_EDLSHEET = []
#     OUTOFSPEC_EDLSHEET = []
#     DESCRIPT_EDLSHEET = []
#     CALC_EDLSHEET = []


#     '''Remove all of the fields we dont want'''
#     sheets = scorecard.sheet_names
#     for sheet in sheets:
#         df = pd.read_excel('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx', sheet_name=sheet)  # get data from sheet
#         column_names = list(df.columns)
#         metric_col = column_names[1]  # metric sheet will be the reference for deleting empty rows or label rows
#         length_col = len(df[metric_col])  # original number of rows in the excel sheet
#         if sheet == sheets[0]:
#             for i in range(length_col):

#                 if type(df[metric_col][i]) == float:
#                     df.drop([i], inplace=True)
#                 elif (df[metric_col][i]) == 'Metric':
#                     df.drop([i], inplace=True)
#                     DF_EDLMETRICS = df

#             NAMES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[1]]))
#             TYPES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[2]]))
#             UNITS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[3]]))
#             POST_RESULTS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[4]]))
#             GREATORLESSS_EDL_SHEET.append(list(DF_EDLMETRICS[column_names[5]]))
#             FLAG_EDLSHEET.append(list(DF_EDLMETRICS[column_names[6]]))
#             OUTOFSPEC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[7]]))
#             CALC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[10]]))
#             DESCRIPT_EDLSHEET.append(list(DF_EDLMETRICS[column_names[9]]))

#     '''Create objects and classes'''

#     class ScoreCardCategory(object):
#         def __init__(self, name=0, entries=0):
#             self.name = name  # these are the tab names (categories)
#             self.entries = entries  # These are all the metrics in each

#         def __call__(self, name, entries):
#             print(name)
#             print(entries)

#     class ScoreCardMetrics(object):
#         def __init__(self, name=0, type=0, units=0, POST_results=0, GreatOrLess=0, Flag=0, OutOfSpec=0, Enum=0,
#                      Description=0, Calculation=0, CalculationCheckedBy=0, MetricCheckedBy=0, FlagOutOfSpecOwner=0):
#             self.name = name
#             self.type = type
#             self.units = units
#             self.POST_results = POST_results
#             self.GreatOrLess = GreatOrLess
#             self.Flag = Flag
#             self.OutOfSpec = OutOfSpec
#             self.Enum = Enum
#             self.Description = Description
#             self.Calculation = Calculation
#             self.CalculationCheckedBy = CalculationCheckedBy
#             self.MetricCheckedBy = MetricCheckedBy
#             self.FlagOutOfSpecOwner = FlagOutOfSpecOwner

#         def __call__(self, name, type, units, POST_results, GreatOrLess, Flag, OutOfSpec, Enum,
#                      Description, Calculation, CalculationCheckedBy, MetricCheckedBy, FlagOutOfSpecOwner):
#             print(name)
#             print(type)
#             print(units)
#             print(POST_results)
#             print(GreatOrLess)
#             print(Flag)
#             print(OutOfSpec)
#             print(Enum)
#             print(Description)
#             print(Calculation)
#             print(CalculationCheckedBy)
#             print(MetricCheckedBy)
#             print(FlagOutOfSpecOwner)

#     METRIC_OBJECTS_GROUPED_EDLMETRIC = []
#     METRIC_OBJECTS_EDLMETRIC = []
#     for i in range(len(NAMES_EDLSHEET[0])):  # number of metrics in each sheet
#         METRIC_OBJECTS_EDLMETRIC.append(ScoreCardMetrics(name=NAMES_EDLSHEET[0][i], type=TYPES_EDLSHEET[0][i],
#                                                          units=UNITS_EDLSHEET[0][i],
#                                                          POST_results=POST_RESULTS_EDLSHEET[0][i],
#                                                          GreatOrLess=GREATORLESSS_EDL_SHEET[0][i],
#                                                          Flag=FLAG_EDLSHEET[0][i],
#                                                          OutOfSpec=OUTOFSPEC_EDLSHEET[0][i], Enum=0,
#                                                          Description=DESCRIPT_EDLSHEET[0][i],
#                                                          Calculation=CALC_EDLSHEET[0][i], CalculationCheckedBy=0,
#                                                          MetricCheckedBy=0, FlagOutOfSpecOwner=0))
#         METRIC_OBJECTS = list(METRIC_OBJECTS_EDLMETRIC)
#     METRIC_OBJECTS_GROUPED_EDLMETRIC.append(METRIC_OBJECTS)

#     edl_metric_objects = METRIC_OBJECTS_GROUPED_EDLMETRIC[0]
#     edl_metric = ScoreCardCategory(scorecard.sheet_names[0], edl_metric_objects)
#     '''===================================Create Summary ==========================================================='''
#     name = []
#     types = []
#     units = []
#     post = []
#     GorLess = []
#     flag = []
#     outofspec = []
#     description = []
#     calculation = []

#     for i in range(len(edl_metric_objects)):
#         name.append(str((edl_metric.entries[i].name)))
#         types.append(str((edl_metric.entries[i].type)))
#         units.append(str((edl_metric.entries[i].units)))
#         post.append(str((edl_metric.entries[i].POST_results)))
#         flag.append(str((edl_metric.entries[i].Flag)))
#         outofspec.append(str((edl_metric.entries[i].OutOfSpec)))
#         GorLess.append(str((edl_metric.entries[i].GreatOrLess)))
#         description.append(str((edl_metric.entries[i].Description)))
#         calculation.append(str((edl_metric.entries[i].Calculation)))

#     table = BeautifulTable()
#     table.column_headers = ['metric', 'type', 'POST2 Result', 'units', 'direction', 'flag value', 'out of spec value',
#                             'calculation','description']

#     for row in zip((name), (types), (post), (units), (GorLess), (flag), (outofspec),
#                    (calculation), (description)):
#         table.append_row(row)

#     table.column_widths = [30, 10, 15, 10, 8, 10, 15, 20, 10]
#     print(table.get_string(recalculate_width=False))

#     table_summary_edlmetrics = table
#     return table_summary_edlmetrics
