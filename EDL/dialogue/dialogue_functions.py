import json
import pickle

import matlab
import scipy

import numpy as np
import os
import yaml

from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import CalculateFuncs, ScorecardDataFrameFuncs, get_variable_info, correlation_multiprocessing
from EDL.models import EDLContextScorecards
from daphne_context.models import UserInformation
import pandas as pd
from multiprocessing import Pool




def load_mat_files(mission_name, mat_file, context: UserInformation):
    file_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files/', mission_name, mat_file)

    context.edlcontext.current_mat_file = file_path
    context.edlcontext.current_mat_file_for_print = mat_file
    context.edlcontext.current_mission = mission_name
    context.edlcontext.save()
    context.save()

    ''' ---------------For MATLAB Engine ------------------'''
    eng1.addpath(os.path.join('/Users/ssantini/Code/EDL_Simulation_Files/', mission_name), nargout = 0)

    mat_file_engine = eng1.load(mat_file)
    # TODO: ADD VARIABLE OF INTEREST TO ENGINE, NOT WHOLE MATFILE
    # eng1.workspace['dataset'] = mat_file_engine
    # eng1.disp('esto', nargout = 0)
    print('The current mat_file is:')
    print(mat_file)

    return 'file loaded'


def mat_file_list(mission_name, context: UserInformation):
    file_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files/', mission_name)
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
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    if mission_name == 'None': # if query uses context,  just use the file path in context
        file_path = mat_file
    else:
        file_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files/', mission_name, mat_file)
    ##################### CHECK IF IT IS A SCORECARD METRIC ###########################################
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=os.path.basename(file_path).replace(".mat", ".yml"),
                                                          edl_context_id__exact=context.edlcontext.id)
    if scorecard_query.desired_running_count() > 0:
        scorecard = scorecard_query.first()
        scorecard_labeled = pickle.loads(scorecard.current_scorecard_df)
        sub_df = scorecard_labeled.loc[scorecard_labeled['metric_name'].str.lower() == param_name]
        if sub_df.shape[0] > 0:
            units = sub_df['units'].ravel().tolist()[0]
            calculation_string = sub_df['calculation'].ravel().tolist()[0]
            list_for_load, warning = CalculateFuncs.equation_parser(calculation_string, mat_file)
            ''' Equations to calculate and remove the things left to the equal side '''
            eqs_to_calc = calculation_string.split(';')
            ''' Load  variables into workspace'''
            [eng1.load(mat_file, item, nargout=0) for item in list_for_load]  # load each
            [eng1.workspace[item] for item in list_for_load]  # add each to workspace
            for item in eqs_to_calc:
                eng1.eval(item, nargout=0)
            val2 = eng1.workspace['ans']
            param_array = np.array(val2)
            warning = 'Scorecard Metric'
        else:
            warning = 'Not Scorecard Metric'

    if warning == 'Not Scorecard Metric':
        edl_mat_load = eng1.load(file_path, param_name, nargout=0) # loads in engine
        dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

        for i in range(len(dict_NL)):
            key = param_name
            if key in dict_NL:
                param_name = dict_NL[param_name][0] # this returns the value of the key (i.e. variable from matfile from NL)
            else:
                param_name = param_name

        param_array = np.array(eng1.workspace[param_name])
        val2 = eng1.workspace[param_name]

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
                    "99.00%",
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

    my_list = []
    for _ in range(val2.size[1]):
        my_list.append(val2._data[_ * val2.size[0]:_ * val2.size[0] + val2.size[0]].tolist())
    return stat, my_list[0]


def load_scorecard(mission_name, mat_file, context: UserInformation):

    # ''' Get Scorecard path'''
    if mission_name == 'None':
        file_to_search = os.path.basename(mat_file.replace(".mat", ".yml"))
    else:
        file_to_search = mat_file.replace(".mat", ".yml")
    # ''' Check if scorecard exists in the Database'''
    all_scorecards = EDLContextScorecards.objects
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search,
                                                          edl_context_id__exact=context.edlcontext.id)
    if scorecard_query.desired_running_count() > 0:
        scorecard = scorecard_query.first()
        return 'Scorecard already exists, and loaded'

    # '''Check if scorecard exists already and just save scorecard path'''
    if os.path.exists(os.path.join("/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecards", file_to_search)) == True:
        i = 1
        scorecard_path = os.path.join('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecards', file_to_search)
    else:
        ''' Set Paths:
         1. mat file path; 2. the scorecard template path''
         '''
        if mission_name == 'None':
            mat_file_path = mat_file # this is actually a path
        else:
            mat_file_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files', mission_name, mat_file)
        ''' Connect to the local computer and generate scorecard'''
        os.system('setenv DYLD_FALLBACK_LIBRARY_PATH $LD_LIBRARY_PATH')
        os.system('~/scorecard.rb --help')
        os.environ['MATLAB_PATH'] = "/Volumes/Encrypted/Mars2020/mars2020/MATLAB/"
        os.system('pwd')
        #print(os.environ['MATLAB_PATH'])
        #os.system(('~/scorecard.rb --yaml --template="/Users/ssantini/Code/Code_Daphne/daphne_brain/daphne_API/edl/ScorecardMaterials/ScoreCardTemplate.xlsx"') + ' --path=' + mat_file_path)
        os.system('~/scorecard.rb -y --template=/Volumes/Encrypted/Mars2020/mars2020/EDLccss/ScoreCardTemplate.xlsx --path=/Volumes/Encrypted/Mars2020/mars2020/MATLAB/' + ' ' + mat_file_path)

        ''' Rename the Scorecard to the mat file'''
        scorecard_temp_path = mat_file.replace(".mat", "")
        scorecard_name = os.path.basename(scorecard_temp_path)+'.yml'
        scorecard_path = os.path.join('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecards', scorecard_name)
        if os.path.isfile('/Users/ssantini/Code/Code_Daphne/daphne_brain/scorecard.yml'):
            os.rename('/Users/ssantini/Code/Code_Daphne/daphne_brain/scorecard.yml', scorecard_path)

    with open(scorecard_path, encoding='utf-8') as scorecard_file:
        scorecard_dict = yaml.load(scorecard_file)
        scorecard_df_labeled = pd.DataFrame(scorecard_dict)
        scorecard_df_labeled = scorecard_df_labeled[~scorecard_df_labeled[':sheet'].str.contains("FLAG FAIL")]
        scorecard_df_labeled = scorecard_df_labeled[~scorecard_df_labeled[':calculation'].str.contains('haz_filename')]
        scorecard_df_labeled = scorecard_df_labeled[~scorecard_df_labeled[':calculation'].str.contains('lvs_error_x_fesn')]

    scorecard_df_labeled.columns = ['metric_name', 'type', 'units', 'calculation', 'direction', 'flag', 'out_of_spec', 'evalString', 'post_results', 'color','status', 'sheet_name']
    scorecard_df_labeled['status'] = scorecard_df_labeled['status'].replace([':grey', ':green'], 'ok')
    scorecard_df_labeled['status'] = scorecard_df_labeled['status'].replace([':yellow'], 'flagged')
    scorecard_df_labeled['status'] = scorecard_df_labeled['status'].replace([':red'], 'out_of_spec')

    flagged_df = scorecard_df_labeled[scorecard_df_labeled.status == 'flagged']
    out_of_spec_df = scorecard_df_labeled[scorecard_df_labeled.status == 'out_of_spec']

    out_of_spec_arrays = ScorecardDataFrameFuncs.get_scorecard_arrays(out_of_spec_df, mat_file, False)
    out_of_spec_df['arrays'] = out_of_spec_arrays

    # db_template = ScorecardDataFrameFuncs.scorecard_df_for_db(mat_file_path, context)
    scorecard_df_bytes = pickle.dumps(scorecard_df_labeled)
    out_of_spec_df_bytes = pickle.dumps(out_of_spec_df)
    flag_df_bytes = pickle.dumps(flagged_df)
    # db_template = pickle.dumps(db_template)

    metrics_of_interest = list(flagged_df['metric_name']) + list(out_of_spec_df['metric_name'])
    context.edlcontext.current_metrics_of_interest = json.dumps(metrics_of_interest)
    context.edlcontext.save()

    new_scorecard = EDLContextScorecards(scorecard_name= os.path.basename(scorecard_path),
                                         current_scorecard_path= scorecard_path,
                                         current_scorecard_df = scorecard_df_bytes,
                                         current_scorecard_df_flag = flag_df_bytes,
                                         current_scorecard_df_fail = out_of_spec_df_bytes,
                                         edl_context=context.edlcontext)
    new_scorecard.save()
    context.save()

    return 'Score Card Loaded and Populated'


def get_scorecard_post_results(edl_scorecard, scorecard_post_param, context: UserInformation):

    if edl_scorecard == 'None':
        scorecard_query = EDLContextScorecards.objects.filter(
            scorecard_name__exact=os.path.basename(context.edlcontext.current_mat_file).replace(".mat", ".yml"),
            edl_context_id__exact=context.edlcontext.id)
        if scorecard_query.desired_running_count() > 0:
            scorecard = scorecard_query.first()
            scorecard_df = pickle.loads(scorecard.current_scorecard_df)
            sub_df = scorecard_df.loc[scorecard_df['metric_name'].str.lower() == scorecard_post_param.lower()]
    else:
        current_scorecard = edl_scorecard.replace('.mat', 'yml')
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


def get_flag_summary(edl_scorecard, mat_file, context: UserInformation, *flag_type):
    if edl_scorecard == 'None':
        file_to_search = os.path.basename(mat_file.replace(".mat", ".yml"))
        scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
        if scorecard_query.desired_running_count() > 0:
            scorecard = scorecard_query.first()
            scorecard_df = scorecard.current_scorecard_df
            flagged_df = pickle.loads(scorecard.current_scorecard_df_flag)
            out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_fail)
            scorecard_df = pickle.loads(scorecard_df)
    else:
        scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=edl_scorecard)
        if scorecard_query.desired_running_count() > 0:
            scorecard = scorecard_query.first()
            scorecard_df = scorecard.current_scorecard_df
            flagged_df = pickle.loads(scorecard.current_scorecard_df_flag)
            out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_fail)
            scorecard_df = pickle.loads(scorecard_df)
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
                                                str(row.direction), str(row.out_of_spec), str(row.units),'is not satisfied'])
                }
            )
            how_many_cases = 'test cases'
            percent_cases = 'test percent'
            context.edlcontext.current_scorecard_path
            i = 1
        return outofspec_list


# TODO: add function for calculating the metrics from a matfile (5007)
def calculate_scorecard_metric(mat_file, edl_scorecard_calculate, scorecard_post_param, context: UserInformation):

    if not os.path.exists(os.path.dirname(mat_file)):
        result = 'not a valid file path, probably just a name'
        file_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files/',context.edlcontext.current_mission, mat_file)
        mat_file = file_path
    else:
        mat_file = mat_file
    '''Get from the template the details of the metric being calculated'''
    with open('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecard_materials/scorecard.json') as file:
        scorecard_json = json.load(file)
        for item in scorecard_json:
            if item['metric'] == scorecard_post_param:
                units = item['units']
                type_result = item['type']
                eval_string = item['evalString']

    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    list_for_load, warning = CalculateFuncs.equation_parser(edl_scorecard_calculate, mat_file)
    ''' Equations to calculate and remove the things left to the equal side '''
    eqs_to_calc = edl_scorecard_calculate.split(';')

    ''' Load  variables into workspace'''
    [eng1.load(mat_file, item, nargout=0) for item in list_for_load]  # load each
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
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    # param_name1 = 'windvert'
    # param_name2 = 'peak inflation axial load'
    file_to_search = os.path.basename(mat_file.replace(".mat", ".yml"))
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
    if scorecard_query.desired_running_count() > 0:
        scorecard = scorecard_query.first()
        complete_scorecard = pickle.loads(scorecard.current_scorecard_df)
        out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_fail)

    ''' Check if it is a matin file'''
    scorecard_metrics = (complete_scorecard['metric_name']).tolist()
    scorecard_metrics = [x.lower() for x in scorecard_metrics if x is not None]
    list_metrics = [i[0] for i in scipy.io.whosmat(mat_file)]

    if param_name1 not in list_metrics and param_name1 not in scorecard_metrics:
        mat_file1 = os.path.basename(mat_file.replace(".mat", "_matin.mat"))
        mat_file1 = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files_Inputs/m2020/', mat_file1)
    else:
        mat_file1 = mat_file

    if param_name2 not in list_metrics and param_name2 not in scorecard_metrics:
        mat_file2 = os.path.basename(mat_file.replace(".mat", "_matin.mat"))
        mat_file2 = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files_Inputs/m2020/', mat_file2)
    else:
        mat_file2 = mat_file

    variable_loc1, arr1, outofspec_indices1, fail_case_no1, flag_indices1, flag_case_no1 = get_variable_info.locate_variable(param_name1, complete_scorecard,
                                                                                          out_of_spec_df, mat_file1, 'all cases')
    variable_loc2, arr2, outofspec_indices2, fail_case_no2, flag_indices2, flag_case_no2 = get_variable_info.locate_variable(param_name2,
                                                                                          complete_scorecard,
                                                                                          out_of_spec_df, mat_file2, 'all cases')
    eng1.load(mat_file, 'output_case', nargout=0)
    output_case = eng1.workspace['output_case']

    output_case_list = (np.asarray(output_case)).tolist()
    output_case_list = [item for sublist in output_case_list for item in sublist]
    output_case_list =  [str(i) for i in output_case_list]# flatten

    val1 = [item for
            sublist in arr1.tolist() for item in sublist]
    val1 = matlab.double(val1)

    val2 = [item for sublist in arr2.tolist() for item in sublist]
    val2 = matlab.double(val2)

    fail_cases_total = fail_case_no1.tolist() + fail_case_no2.tolist()
    fail_cases_list = [str(i) for i in fail_cases_total]
    fail_case_labels = [True if i in fail_cases_list else False for i in output_case_list]

    flag_cases_total = flag_case_no1.tolist() + flag_case_no2.tolist()
    flag_cases_list = [str(i) for i in flag_cases_total]
    flag_case_labels = [True if i in flag_cases_list else False for i in output_case_list]

    my_list = []
    for _ in range(val2.size[1]):
        if output_case is not None:
            my_list.append((val1._data[_], val2._data[_], output_case._data[_], fail_case_labels[_], flag_case_labels[_]))
        else:
            my_list.append((val1._data[_], val2._data[_], None))

    return my_list


def create_cormat(matout_path, context: UserInformation):
    ''' Start Engine
    1. Get list of variables in da
    taset
    2. Set desired events for search
    3. Remove irrelevant events
    4. Create dataframe of remaining variables and compute the correlation matrix


    '''


    prueba = matout_path
    eng1.load(matout_path, nargout = 0)
    eng1.load(matout_path, 'output_case', nargout=0)
    output_cases = [item for sublist in np.array(eng1.workspace['output_case']).tolist() for item in sublist] # will be used as dataframe indices

    list_metrics_matout = scipy.io.whosmat(matout_path)
    list_metrics_matout_clean = [i[0] for i in list_metrics_matout]

    list_events = [words for segments in list_metrics_matout_clean for words in segments.split('_')[-1:]]
    list_events = (list(set(list_events)))
    # We had roughly 806 events. For an initial approach, we selected the events below. Which result in ~2,500 variables
    sub_events = ['_dsi', 'fesn', 'AGLsample', '_ei', '_rc', '_rev1', '_end1', '_hda', '_sufr', '_pd', '_hs', '_bs', '_sky', '_td']

    list_metrics_arm = []
    for substring in sub_events:
        list_variables = [s for s in list_metrics_matout_clean if substring in s]
        list_metrics_arm.append(list_variables)

    list_metrics_arm = [item for sublist in list_metrics_arm for item in sublist]
    ''' Get data from matout.mat and save as dataframe'''
    my_list = []
    for i in range(len(list_metrics_arm)):
        arr = eng1.eval(list_metrics_arm[i])
        my_list.append(np.asarray(arr._data))

    matout_df = pd.DataFrame(my_list, index=list_metrics_arm, columns=output_cases).transpose()
    matout_df.astype('float32')
    matin_df_sorted = matout_df.reset_index()
    num_partitions = 16  # no. partitions to split dataframe
    num_cores = 8
    corr_matrix = correlation_multiprocessing.parallelize_dataframe(matin_df_sorted, correlation_multiprocessing.vcorrcoef, list_metrics_arm)
    cormat_df = pd.DataFrame(corr_matrix, index=list_metrics_arm, columns=list_metrics_arm)
    i = 1
    cormat_df_bytes = pickle.dumps(cormat_df)
    context.edlcontext.current_cormat_status = "true"
    context.edlcontext.current_cormat_df = cormat_df_bytes
    context.edlcontext.save()

    file_to_search = os.path.basename(context.edlcontext.current_mat_file.replace(".mat", ".yml"))
    new_cormat_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search).first()
    new_cormat_query.current_corr_mat_df = pickle.dumps(cormat_df)
    new_cormat_query.current_corr_mat_status = "true"

    new_cormat_query.save()


    context.save()

    return 'Correlation matrix generated successfully'