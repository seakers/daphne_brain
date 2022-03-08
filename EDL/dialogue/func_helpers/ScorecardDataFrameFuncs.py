import yaml
import pandas as pd
import numpy as np
from numpy import nan
import os, sys
import re
import json

from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import CalculateFuncs

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
    sheet_name = []
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
        sheet_name.append(item[':sheet'])

        scorecard_dataframe= pd.DataFrame({'metric_name': metric_list,
        'type': type_list,
        'units': units_list,
        'post_results': POST_result_list,
        'direction': direction_list,
        'flag': flag_list,
        'out_of_spec':outofspec_list,
        'calculation':calculation_list,
        'evalString': eval_list,
        'sheet_name': sheet_name

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

def get_scorecard_arrays(scorecard_df, matfile_path, for_db):
    array_list = []
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)
    if for_db == True:
        eng1.load(matfile_path, 'output_case', nargout=0)
        output_case = eng1.workspace['output_case']
        output_case_array = np.asarray(output_case)
    for index, row in scorecard_df.iterrows():
        metric = row.metric_name
        print(metric)
        equation = row.calculation
        list_for_load, warning = CalculateFuncs.equation_parser(row.calculation, matfile_path)
        if not row.calculation.startswith("if") or row.calculation.startswith("i ="):
            eqs_to_calc = row.calculation.split(';')
            eqs_to_calc = [x for x in eqs_to_calc if x]
        else:
            eqs_to_calc = [row.calculation]
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

        if type(answer) != float: # if array
            if metric == 'Major axis ':
                ejemplo = np.asarray(answer)*2
            else:
                ejemplo = np.asarray(answer)
            array_list.append(ejemplo)
            test = 'its an array'
        elif type(answer) == float and for_db == True:
            array_list.append(np.asarray(answer))
        else:
            array_list.append(np.array(0))
    if for_db == True:
        array_list.append(output_case)
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
    if criteria == 'out_of_spec':
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

def scorecard_df_for_db(matout_path, context):
    if context.edlcontext.current_mission == 'm2020':
        mission_name = 'Mars2020'
        db_template = pd.read_excel('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/dialogue/func_helpers/db_m2020_template.xlsx')

    file_to_search = os.path.basename(matout_path.replace(".mat", ".yml"))
    scorecard_path = '/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/scorecards/' + file_to_search

    with open(scorecard_path, encoding='utf-8') as file_to_search:
        scorecard_dict = yaml.load(file_to_search)
        scorecard_df = pd.DataFrame(scorecard_dict)

    scorecard_metrics = scorecard_df[':metric'].ravel().tolist()
    db_template = db_template[db_template['metric_name'].isin(scorecard_metrics)]
    metric_list = db_template['metric_name'].ravel().tolist()


    # ''' Get Status of metrics flag/fail/pass'''
    scorecard_subdf = scorecard_df[scorecard_df[':metric'].isin(metric_list)]
    scorecard_subdf = scorecard_subdf[scorecard_subdf[':sheet'].isin(['Entry', 'Parachute Descent', 'Powered Flight'])]

    # ''' Add to template'''
    status_list = scorecard_subdf[':code'].ravel().tolist()
    calc_list = scorecard_subdf[':calculation'].ravel().tolist()
    units_list = scorecard_subdf[':units'].ravel().tolist()

    db_template['calculation'] = calc_list
    db_template = db_template
    # ''' Compute arrays '''
    arrays = get_scorecard_arrays(db_template, matout_path, True)
    output_case = np.asarray(arrays[len(arrays)-1]).ravel()
    # ''' Drop output_case from arrays list'''
    arrays = arrays[:-1]

    # Compute properties for each metric
    dict_list = []
    prctile_1_list = []
    prctile_99_list = []
    average_list = []
    var_list = []
    arr_list = []
    for item in arrays:
        if item.size == 1:
            item = np.full((1,8000), item)
        prctile_1 = np.percentile(np.asarray(item).ravel(), 1)
        prctile_99 = np.percentile(np.asarray(item).ravel(), 99)
        average = np.percentile(np.asarray(item).ravel(), 50)
        var = np.var(np.asarray(item).ravel())
        dictionary = str(json.dumps(dict(zip(output_case, np.asarray(item).ravel()))))
        dict_list.append(dictionary)
        prctile_1_list.append(prctile_1)
        prctile_99_list.append(prctile_99)
        average_list.append(average)
        var_list.append(var)
        arr_list.append(item.ravel().tolist())

    db_template['prctile_1'] = prctile_1_list
    db_template['prctile_99'] = prctile_99_list
    db_template['average'] = average_list
    db_template['variance'] = var_list
    db_template['variance'] = var_list
    db_template['status'] = status_list
    db_template['dict_data'] = dict_list
    db_template['units'] = units_list

    db_template['status'] = db_template['status'].replace([':grey', ':green'], 'ok')
    db_template['status'] = db_template['status'].replace([':yellow'], 'flagged')
    db_template['status'] = db_template['status'].replace([':red'], 'out_of_spec')
    # db_template['arrays'] = arrays

    #### GET DUPLICATES AND DROP NECESSARY ONES #####
    duplicates = db_template[db_template.duplicated(['metric_name'])]
    duplicates.drop(duplicates[duplicates['metric_name'] == 'Number of No Vel Solutions'].index, inplace=True)
    duplicates.drop(duplicates[duplicates['metric_name'] == 'Number of No Alt Solutions'].index, inplace=True)
    duplicates.drop(duplicates[duplicates['metric_name'] == 'Max Velocity Solution Change'].index, inplace=True)
    duplicates.drop(duplicates[duplicates['metric_name'] == 'Number of No Alt Soltuions'].index, inplace=True)
    duplicates.drop(duplicates[duplicates['metric_name'] == 'Number of No Vel Soltuions'].index, inplace=True)

    idx_to_remove = duplicates.index
    db_template.reset_index()
    nav_solutions = db_template[db_template['metric_name'].isin(['Max Velocity Solution Change',
                                                                 'Number of No Vel Solutions',
                                                                 'Number of No Alt Solutions',
                                                                 'Number of No Alt Soltuions',
                                                                 'Number of No Vel Soltuions'])]

    res = list(map(" at ".join, zip(nav_solutions.metric_name.tolist(), nav_solutions.segment_name.tolist())))
    nav_solutions['metric_name'] = res

    db_template.loc[nav_solutions.index] = nav_solutions
    # db_template['metric_id'] = db_template['metric_name'].astype(str) + ext_id
    # Drop the other duplicated measures that are not repeated in events
    db_template = db_template.drop_duplicates(subset='metric_name', keep='first')

    return db_template