import yaml
import pandas as pd
import numpy as np
from numpy import nan
import os, sys

from daphne_API.edl import CalculateFuncs
from daphne_API.MatEngine_object import eng1
eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

def generate_scorecard_dataframe(scorecard_dict):

    dict_test = pd.DataFrame.from_dict(scorecard_dict)
    metric_list = []
    type_list = []
    units_list = []
    POST_result_list = []
    direction_list = []
    flag_list = []
    outofspec_list = []
    calculation_list = []
    eval_list = []
    for item in scorecard_dict:
        metric_list.append(item[':metric'])
        type_list.append(item[':type'])
        units_list.append(item[':units'])
        POST_result_list.append(item[':value'])
        direction_list.append(item[':direction'])
        flag_list.append(item[':yellow'])
        outofspec_list.append(item[':red'])
        calculation_list.append(item[':calculation'])
        eval_list.append(item[':evalString'])

        scorecard_dataframe= pd.DataFrame({'metric_name': metric_list,
        'type': type_list,
        'units': units_list,
        'post_results': POST_result_list,
        'direction': direction_list,
        'flag': flag_list,
        'out_of_spec':outofspec_list,
        'calculation':calculation_list,
        'evalString': eval_list
         })
    seen = set()
    unique_metrics = []
    for item in metric_list:
        if item not in seen:
            seen.add(item)
            unique_metrics.append(item)

    return scorecard_dataframe

status_list = []
def generate_scorecard_dataframe_labeled(scorecard_dataframe_labeled):
    for i in list(range(len(scorecard_dataframe_labeled.index.values))):  # list(range(len(scorecard_df.index.values)))
        if pd.isna(scorecard_dataframe_labeled['post_results'][i]) != True and pd.isna(scorecard_dataframe_labeled['flag'][i]) != True \
                and pd.isna(scorecard_dataframe_labeled['direction'][i]) != True and scorecard_dataframe_labeled['direction'][i] != None\
                and scorecard_dataframe_labeled['direction'][i] != 'N/A' and pd.isna(scorecard_dataframe_labeled['out_of_spec'][i]) != True:
                #and scorecard_dataframe_labeled['out_of_spec'][i] != 0 and scorecard_dataframe_labeled['flag'][i] != 0:
                metric_name = scorecard_dataframe_labeled['metric_name'][i]
                result = scorecard_dataframe_labeled['post_results'][i]
                sign = scorecard_dataframe_labeled['direction'][i]
                flag_val = scorecard_dataframe_labeled['flag'][i]
                fail_val = scorecard_dataframe_labeled['out_of_spec'][i]
                if eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(scorecard_dataframe_labeled['flag'][i])) == False \
                                and eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(scorecard_dataframe_labeled['out_of_spec'][i])) == True:
                            status_list.append(str('flagged'))
                elif eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(scorecard_dataframe_labeled['flag'][i])) == False\
                                and eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(scorecard_dataframe_labeled['out_of_spec'][i])) == False:
                            status_list.append(str('out of spec'))
                elif eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(
                            scorecard_dataframe_labeled['flag'][i])) == True \
                             and eval(str(scorecard_dataframe_labeled['post_results'][i]) + str(scorecard_dataframe_labeled['direction'][i]) + str(
                            scorecard_dataframe_labeled['out_of_spec'][i])) == True:
                            status_list.append(str('value is ok'))
                else:
                            status_list.append('N/A')
        else:
            status_list.append('N/A')

    status_df = pd.DataFrame({'status': status_list})
    scorecard_dataframe_labeled['status'] = status_df
    return scorecard_dataframe_labeled

def get_scorecard_arrays(scorecard_df, matfile_path):
    array_list = []
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)
    for index, row in scorecard_df.iterrows():
        metric = row.metric_name
        outofspec = row.out_of_spec
        equation = row.calculation
        list_for_load, warning = CalculateFuncs.equation_parser(row.calculation, matfile_path)
        eqs_to_calc = row.calculation.split(';')
        eqs_to_calc = [x for x in eqs_to_calc if x]
        ''' Load  variables into workspace'''
        [eng1.load(matfile_path, item, nargout=0) for item in list_for_load]  # load each
        [eng1.workspace[item] for item in list_for_load]
        #eqs_to_calc = [w.replace('[a,b,azl]=size_ellipse(x,y,mean(gcrad_tds/1e3))', '[a,b,azl]=size_ellipse(x,y,(gcrad_tds/1e3))') for w in eqs_to_calc]
        for item in eqs_to_calc:
            # add each to workspace
            variables = eng1.eval('who')
            eng1.eval(item, nargout=0)
            variables = eng1.eval('who')
            if 'ans' in variables:
                this = 'answer is calculated already'
                answer = eng1.workspace['ans']
            # if 'a' in variables:
            #     answer = eng1.workspace['a']

            #answer = eng1.workspace['ans']
        if type(answer) != float: # if array
            if metric == 'Major axis ':
                ejemplo = np.asarray(answer)*2
            else:
                ejemplo = np.asarray(answer)
            array_list.append(ejemplo)
            test = 'its an array'
        else:
            array_list.append(np.array(0))
    return array_list


def get_case_numbers(metric_name, scorecard_dataframe, matfile_path, criteria):

    metric_array = scorecard_dataframe.arrays.array[0]
    #metric_array = \
    #scorecard_dataframe[scorecard_dataframe["metric_name"].str.lower().str.contains(metric_name)].arrays.array[0]
    n = len(metric_array)
    metric_status = []
    if len(metric_array) > 0:
        'this means we have an array, we can now calculate the labels'
        flag_value = (scorecard_dataframe.flag.array[0]).astype(str)
        direction = str(scorecard_dataframe.direction.array[0])
        out_of_spec_value = (scorecard_dataframe.out_of_spec.array[0]).astype(str)

        for i in range(len(metric_array)):
            if eval(str(metric_array[i][0]) + (direction) + flag_value) == False \
                    and eval(str(metric_array[i][0]) + (direction) + (out_of_spec_value)) == True:
                metric_status.append('flagged_case')
            elif eval(str(metric_array[i][0]) + (direction) + (flag_value)) == False \
                    and eval(str(metric_array[i][0]) + (direction) + (out_of_spec_value)) == False:
                metric_status.append('out_of_spec_case')
            elif eval(str(metric_array[i][0]) + (direction) + (flag_value)) == True \
                    and eval(str(metric_array[i][0]) + (direction) + (out_of_spec_value)) == True:
                metric_status.append('value ok')
            else:
                metric_status.append('missing information')

    else:
        return 'There is not enough information to calculate this'

    eng1.load(matfile_path, 'output_case', nargout=0)
    output_case = eng1.workspace['output_case']
    output_case_array = np.asarray(output_case)

    indices_fail = []
    indices_flag = []
    cases_fail = []
    cases_flag = []
    if criteria == 'out of spec':
        indices_fail = [j for j, x in enumerate(metric_status) if x == 'out_of_spec_case']
        cases_fail = np.take(output_case, indices_fail)
        indices_flag = []
        cases_flag = []
    if criteria == 'flagged':
        indices_flag = [j for j, x in enumerate(metric_status) if x == 'flagged_case']
        cases_flag = np.take(output_case, indices_flag)
        cases_fail = []
        indices_fail = []
    if criteria == 'all cases':
        indices_fail = [j for j, x in enumerate(metric_status) if x == 'out_of_spec_case']
        cases_fail = np.take(output_case, indices_fail)
        indices_flag = [j for j, x in enumerate(metric_status) if x == 'flagged_case']
        cases_flag = np.take(output_case, indices_flag)

    return indices_fail, cases_fail, indices_flag, cases_flag