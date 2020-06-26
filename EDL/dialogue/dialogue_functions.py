import json
import re
import numpy as np
import os
import yaml

from EDL.dialogue import ScorecardDataFrameFuncs
from EDL.dialogue.MatEngine_object import eng1
from daphne_context.models import UserInformation


def load_mat_files(mission_name, mat_file, context: UserInformation):
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)

    context.edlcontext.current_mat_file = file_path
    context.edlcontext.current_mat_file_for_print = mat_file
    context.edlcontext.save()
    context.save()

    ''' ---------------For MATLAB Engine ------------------'''
    eng1.addpath(os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name), nargout = 0)

    mat_file_engine = eng1.load(mat_file)
    # TODO: ADD VARIABLE OF INTEREST TO ENGINE, NOT WHOLE MATFILE
    # eng1.workspace['dataset'] = mat_file_engine

    # eng1.disp('esto', nargout = 0)
    print('The current mat_file is:')
    print(mat_file)
    return 'file loaded'


def mat_file_list(mission_name, context: UserInformation):
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


def compute_stat(mission_name,mat_file, param_name, context: UserInformation):
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

    for i in range(len(dict_NL)):
        key = param_name
        if key in dict_NL:
            param_name = dict_NL[param_name][0] # this returns the value of the key

        else:
            param_name = param_name
    if mission_name == 'None':
        file_path = mat_file
    else:
        file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)

    edl_mat_load = eng1.load(file_path, param_name, nargout=0) # loads in engine
    param_array = np.array(eng1.workspace[param_name])

    # mat_dict = scipy.io.loadmat(file_path)
    # '''Get list of keys in mat dict'''
    # list_keys = list(mat_dict.keys())
    # param_array = mat_dict[param_name]
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


    stat = []
    for name, value in zip(name_of_stat, value_of_stat):
        stat.append(
            {
                'command_result': " = ".join([name, value.astype(str)])
            }
        )


    val2 = eng1.workspace[param_name] # returns to python
    my_list = []
    for _ in range(val2.size[1]):
        my_list.append(val2._data[_ * val2.size[0]:_ * val2.size[0] + val2.size[0]].tolist())
    return stat, my_list[0]


def load_scorecard(mission_name, mat_file, context: UserInformation):
    if mission_name == 'None':
        file_to_search = os.path.basename(mat_file.replace(".mat", ".yml"))
    else:
        file_to_search = mat_file.replace(".mat", ".yml")
    '''Check if scorecard exists already'''
    if os.path.exists(os.path.join("/Users/ssantini/Desktop/Code_Daphne/daphne_brain/", file_to_search)) == True:
        i = 1
        scorecard_path = os.path.join('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/', file_to_search)

    else:
        ''' Set Paths:
         1. mat file path;
         2. the scorecard template path''
         '''
        if mission_name == 'None':
            mat_file_path = mat_file # this is actually a path
        else:
            mat_file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', mission_name, mat_file)
        scorecard_template_path = '"/Users/ssantini/Desktop/Code_Daphne/daphne_brain/ScoreCardTemplate.xlsx"'

        ''' Connect to the local computer and generate scorecard'''
        os.system('echo $SHELL')
        os.system('setenv DYLD_FALLBACK_LIBRARY_PATH $LD_LIBRARY_PATH')
        # The scorecard ruby location is: /Volumes/Encrypted/Mars2020/mars2020/bin/scorecard.rb'''
        # The Scorecard template is: /Users/ssantini/Code/ExtractDataMatlab/ScoreCardTemplate.xlsx '''
        os.system('~/scorecard.rb --help')
        os.system('pushd "~/Users/ssantini/Desktop/Code_Daphne/daphne_brain/"')
        os.system('pwd')
        os.environ['MATLAB_PATH']= "/Volumes/Encrypted/Mars2020/mars2020/MATLAB/"
        print(os.environ['MATLAB_PATH'])
        os.system(('~/scorecard.rb --yaml --template="/Users/ssantini/Desktop/Code_Daphne/daphne_brain/ScoreCardTemplate.xlsx"') + ' ' + mat_file_path)

        ''' Rename the Scorecard to the mat file'''
        scorecard_temp_path = mat_file.replace(".mat", "")
        scorecard_name = os.path.basename(scorecard_temp_path)+'.yml'
        scorecard_path = os.path.join('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/', scorecard_name)
        if os.path.isfile('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.yml'):
            os.rename('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.yml', scorecard_path)

    context.edlcontext.current_scorecard_file = os.path.basename(scorecard_path)
    context.edlcontext.current_scorecard = scorecard_path
    context.edlcontext.save()
    context.save()

    return 'Score Card Loaded and Populated'


def get_scorecard_post_results(edl_scorecard, scorecard_post_param, context: UserInformation):
    with open(os.path.basename(edl_scorecard), encoding='utf-8') as scorecard_file:
        scorecard_dict = yaml.load(scorecard_file)
    scorecard_df = ScorecardDataFrameFuncs.generate_scorecard_dataframe(scorecard_dict)

    '''Search in dictionary what is contained '''
    possible_metrics = scorecard_df.metric_name.str.contains(str(scorecard_post_param), case = False, na = False)
    indexes_in_df = possible_metrics[possible_metrics == True].index.tolist()
    post_results = scorecard_df.iloc[indexes_in_df]

    post_results_list = []
    for row in post_results.itertuples():
        post_results_list.append(
            {
                'command_result': " ".join([str(row.metric_name), str('='), str(row.post_results), str(row.units), "(",
                                            str(row.type), ")"])
            }
        )
    return post_results_list


def get_flag_summary(edl_scorecard, context: UserInformation, *flag_type):

    ''' 1. Convert to dataframe
    2. Add column with labels : flagged, out of spec, N/A or value is ok
    3. Get dataframe for flagged metrics and one data frame for out of spec'''

    scorecard_name = os.path.basename(edl_scorecard)
    with open(scorecard_name, encoding='utf-8') as scorecard_file:
        scorecard_dict = yaml.load(scorecard_file)

    scorecard_df = ScorecardDataFrameFuncs.generate_scorecard_dataframe(scorecard_dict)
    scorecard_df_labeled = ScorecardDataFrameFuncs.generate_scorecard_dataframe_labeled(scorecard_df)
    flagged_df = scorecard_df_labeled[scorecard_df_labeled.status == 'flagged']
    out_of_spec_df = scorecard_df_labeled[scorecard_df_labeled.status == 'out of spec']

    ''' Now we want to get what metrics are flagged and which are out of spec as a list'''
    if 'flagged_results' in flag_type:
        flagged_list = []
        for row in flagged_df.itertuples():
            flagged_list.append(
                {
                    'command_result':" ".join([str(row.metric_name), str(row.post_results), str(row.units), "(",
                                               str(row.type), ")",
                                               str(row.direction), str(row.flag), str(row.units), 'is not satisfied'])
                }
            )
        return flagged_list
    if 'outofspec_results' in flag_type:
        outofspec_list = []
        for row in out_of_spec_df.itertuples():
            outofspec_list.append(
                {
                    'command_result': " ".join([str(row.metric_name), str(row.post_results),  str(row.units), "(",
                                                str(row.type), ")",
                                                str(row.direction), str(row.flag), str(row.units),'is not satisfied'])
                }
            )
        return outofspec_list


# TODO: add function for calculating the metrics from a matfile (5007)
def calculate_scorecard_metric(mat_file, edl_scorecard_calculate, scorecard_post_param, context: UserInformation):

    '''Get from the template the details of the metric being calculated'''
    with open('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.json') as file:
        scorecard_json = json.load(file)
        for item in scorecard_json:
            if item['metric'] == scorecard_post_param:
                units = item['units']
                type_result = item['type']
                eval_string = item['evalString']
    ''' Check if the variables in the string to be calculate exist in the matfile, this uses a function called vars_for_calc(list, mat_file_path) and returns a list we can use to load them in the workspace'''
    # split the calculation string
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    ''' Equations to calculate and remove the things left to the equal side '''
    eqs_to_calc = edl_scorecard_calculate.split(';')
    eqs_to_calc_rhs = [item[item.find('='):][1:] for item in eqs_to_calc if
                       item.find('=') != 1]  # we care about the variables in the rhs of the equation
    eq_vars = re.split('[,()/*;~= ]', "".join(eqs_to_calc_rhs)) # variable list

    ''' Check if variables are in the mat file '''
    path_mat = '/Users/ssantini/Code/ExtractDataMatlab/matout.mat'
    list_for_load = eng1.vars_for_calc(eq_vars, path_mat) # matlab script that checks what file is in the matfile'

    ''' Load  variables into workspace'''
    [eng1.load('/Users/ssantini/Code/ExtractDataMatlab/matout.mat', item, nargout=0) for item in list_for_load]  # load each
    [eng1.workspace[item] for item in list_for_load]  # add each to workspace

    for item in eqs_to_calc:
        eng1.eval(item, nargout=0)
    calculation_result = eng1.workspace['ans']
    calculation_string = eng1.eval(eval_string)

    calculation_response = "".join([str('The'), str(' '), str(scorecard_post_param),  str(' = '), str(calculation_string),
                                                str(units), str(" ("), str(type_result),str(") ")])

    return calculation_response


# TODO: add function for plotting metrics  (5010)
def plot_from_matfile(mat_file, param_name1, param_name2, context: UserInformation):
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

    for i in range(len(dict_NL)):
        key1 = param_name1
        if key1 in dict_NL:
            param_name1 = dict_NL[param_name1][0]  # this returns the value of the key

        else:
            param_name1 = param_name1
        key2 = param_name2
        if key2 in dict_NL:
            param_name2 = dict_NL[param_name2][0]  # this returns the value of the key

        else:
            param_name2 = param_name2
    var1_mat = eng1.load(mat_file, param_name1, nargout=0)
    var2_mat = eng1.load(mat_file, param_name2, nargout=0)  # loads in engine
    output_case = eng1.load(mat_file, 'output_case', nargout=0)
    val1 = eng1.workspace[param_name1] # returns to python
    val2 = eng1.workspace[param_name2]
    output_case = eng1.workspace['output_case']
    my_list = []
    output_case_py = []
    for _ in range(val2.size[0]):
        if output_case is not None:
            my_list.append((val1._data[_], val2._data[_], output_case._data[_]))
        else:
            my_list.append((val1._data[_], val2._data[_], None))

    return my_list
