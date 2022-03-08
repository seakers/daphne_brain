from __future__ import division, absolute_import, print_function
import os
import pandas as pd
import pickle
from scipy.io import loadmat
import scipy.io
from scipy import stats
from sklearn.utils import resample
from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import get_variable_info
from EDL.models import EDLContextScorecards
from auth_API.helpers import get_or_create_user_information, get_user_information
import numpy as np
from functools import partial


def run_SA(target_metric, metric_type, input_data_type, event_selection, boundary, cutoff_val, cutoff_val2, event_options,
           dataset_opts, dataset_min, dataset_max, event_start, user_info):

    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)
    matfile_path = user_info.edlcontext.current_mat_file
    matfile_name = os.path.basename(matfile_path.replace(".mat", "_matin.mat"))

    # get scorecard
    file_to_search = os.path.basename(matfile_path.replace(".mat", ".yml"))
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search)
    if scorecard_query.count() > 0:
        scorecard = scorecard_query.first()
        scorecard_labeled = pickle.loads(scorecard.current_scorecard_df)
        scorecard_labeled = scorecard_labeled.dropna()
        out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_fail)
        out_of_spec_df = out_of_spec_df.dropna()
        cormat = pickle.loads(scorecard.current_corr_mat_df)
        # cor_target = abs(cormat.loc[target_metric])
        # relevant_features = cor_target[cor_target > 0.5].sort_values(ascending=False)

    variable_loc, arr_target, outofspec_indices, fail_case_no, flag_indices, flag_case_no = get_variable_info.locate_variable(
        str.lower(target_metric), scorecard_labeled, out_of_spec_df, matfile_path, 'all cases')

    input_dispatcher = {"EDLSequence": get_df_EDL_seq, "MCInput": get_df_mc_input}

    if input_data_type ==  "MCInput":
        matin_df, input_dict_df, labels = input_dispatcher[input_data_type](matfile_path, fail_case_no, matfile_name, target_metric, arr_target, user_info)
    elif input_data_type == "EDLSequence":
        matin_df, input_dict_df, labels = input_dispatcher[input_data_type](user_info, event_selection, variable_loc, out_of_spec_df, target_metric, event_options, event_start,
                    fail_case_no, arr_target)

    # shrink dataset
    if dataset_opts == 'fraction-dataset':
        matin_df = matin_df[(matin_df[target_metric].astype(float) >= float(dataset_min)) & (matin_df[target_metric].astype(float) <= float(dataset_max))]
        print('selecting fraction of dataset chosen')

    divideDataBy = {"passfail": passfail_boundary, "cutoff": cutoff_boundary, "0.01": percentile_boundary, "0.99": percentile_boundary}

    matin_lower, matin_upper = divideDataBy[boundary](matin_df, labels, cutoff_val, cutoff_val2, target_metric, boundary, arr_target)
    matin_lower = matin_lower.drop([target_metric, 'fail_label'], axis=1)
    matin_upper = matin_upper.drop([target_metric, 'fail_label'], axis=1)

    ''' KS TEST '''
    p_vals = []
    description = []
    label = []
    counter = 0
    distance =[]
    for column in matin_lower:
        # print(column)
        counter += 1
        arr1 = (matin_upper[column]).values
        arr2 = (matin_lower[column]).values
        arr1.reshape(1, len(arr1))
        arr2.reshape(1, len(arr2))
        test_result = stats.ks_2samp(arr1, arr2)
        p_vals.append(test_result[1])
        distance.append(test_result[0])
        description.append((input_dict_df[input_dict_df['Variable'].str.contains(column)].Description.array[0]))
        label.append((input_dict_df[input_dict_df['Variable'].str.contains(column)].Label.array[0]))

    df_results = pd.DataFrame(
            {'metric_name': list(matin_upper.columns), 'distance': distance, 'p_vals': p_vals, 'description':description,
             'label':label}).sort_values(by='distance', ascending= False)

    sub_df = df_results.iloc[0:20, :]
    print('Sensitivity Analysis finished')

    return sub_df
################################################################################################################################################

def get_df_mc_input(matfile_path, fail_case_no, matfile_name, target_metric, arr_target, user_info):
    input_dict_df = pd.read_excel('/Users/ssantini/Dropbox/Code/SensitivityAnalysis/input_deck_dict.xlsx')
    matin_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files_Inputs/m2020/', matfile_name)
    matout_path = user_info.edlcontext.current_mat_file
    input_deck = loadmat(matin_path)
    input_cases = [item for sublist in (input_deck['input_case']).tolist() for item in sublist]
    input_deck = loadmat(matin_path)

    eng1.load(matfile_path, 'output_case', nargout=0)
    eng1.workspace['output_case']
    eng1.eval('who')
    output_cases = [item for sublist in np.array(eng1.workspace['output_case']).tolist() for item in sublist]

    eng1.load(matin_path, nargout=0)
    list_metrics_matin = scipy.io.whosmat(matin_path)
    list_metrics_matin = [i[0] for i in list_metrics_matin]

    my_list = []
    for i in range(len(list_metrics_matin)):
        arr = eng1.eval(list_metrics_matin[i])
        my_list.append(np.asarray(arr._data))

    ''' Convert matin into a dataframe '''
    matin_df = pd.DataFrame(my_list, index=list_metrics_matin, columns=input_cases).transpose().drop('check',                                                                                      axis=1)
    matin_df['input_case'] = pd.Categorical(matin_df['input_case'], categories=output_cases, ordered=True)
    matin_df = matin_df.sort_values(by='input_case')
    labels = ['out of spec' if i in list(fail_case_no) else 'ok' for i in matin_df['input_case']]
    matin_df = matin_df.drop(['input_case', 'nstate_delv'], axis = 1)
    flat_list = [item for sublist in arr_target.tolist() for item in sublist]
    matin_df.insert(0, target_metric, flat_list)

    return matin_df, input_dict_df, labels


def get_df_EDL_seq(user_info, event_selection, variable_loc, out_of_spec_df, target_metric, event_options, event_start,
                    fail_case_no, arr_target):
     input_dict_df = pd.read_excel('/Users/ssantini/Dropbox/Code/SensitivityAnalysis/matout_dict.xlsx')
     matin_path = user_info.edlcontext.current_mat_file
     user_selected_event = event_selection
     if variable_loc == 'out of spec scorecard metric, array existed' or \
             variable_loc == 'flagged scorecard metric, array was calculated':
         df_row = out_of_spec_df.loc[
                      out_of_spec_df['metric_name'].str.lower() == str(target_metric).lower()].iloc[:1]
         equation = [(df_row["calculation"]).to_string(index=False)]
     else:
         equation = [target_metric]

     dict_events = {
         '_Allsample': ['AGLsample0', 'AGLsample1', 'AGLsample2', 'AGLsample3', 'AGLsample4', 'AGLsample5',
                        'AGLsample6',
                        'AGLsample7', 'AGLsample8'],
         "_AllEDLEvents": ['_ei', '_rc', '_rev1', '_end1', '_hda', '_sufr', '_pd', '_hs', '_bs', '_sky', '_td']}

     if event_selection.endswith('_Allsample') or event_selection.endswith('_AllEDLEvents'):
         events = dict_events[event_selection]

     if event_options == "up-to-event":
         if 'AGLsample' in event_selection:
             events = dict_events['_Allsample']
         else:
             events = dict_events['_AllEDLEvents']
         for item in [event_selection]:
             event_search = [ele for ele in events if (ele in item)]
             event_position = [i for i, item in enumerate(events) if item in set(event_search)]
             if len(event_position) > 1:
                 target_event = events[min(event_position)]
             else:
                 target_event = events[event_position[0]]
             check = next((True for events in events if target_event in events), False)
             if check == True:
                 targetibdex = events.index(target_event)
                 del events[targetibdex: len(events)]
             events.append(event_selection)
     elif event_options == 'from-event':
         events = dict_events['_AllEDLEvents']
         for item in [event_selection]:
             event_search = [ele for ele in events if (ele in item)]
             event_position = [i for i, item in enumerate(events) if item in set(event_search)]
             if len(event_position) > 1:
                 target_event = events[min(event_position)]
             else:
                 target_event = events[event_position[0]]
         start_index = events.index(event_start)
         end_index = events.index(target_event)
         events = events[start_index:end_index + 1]
     # Only keep variables that are in this event, get variables from matfile
     else:
         events = [event_selection]
     list_metrics_matout = scipy.io.whosmat(matin_path)
     list_metrics_matout_clean = [i[0] for i in list_metrics_matout]

     list_metrics_matin = []
     for substring in events:
         list_variables = [s for s in list_metrics_matout_clean if s.endswith(substring)]
         list_metrics_matin.append(list_variables)
     list_metrics_matin = [item for sublist in list_metrics_matin for item in sublist]

     # Start engine
     eng1.load(matin_path, nargout=0)
     eng1.load(matin_path, 'output_case', nargout=0)
     output_cases = [item for sublist in np.array(eng1.workspace['output_case']).tolist() for item in sublist]

     # labels
     labels = ['out of spec' if i in fail_case_no else 'ok' for i in output_cases]

     my_list = []
     for i in range(len(list_metrics_matin)):
         arr = eng1.eval(list_metrics_matin[i])
         my_list.append(np.asarray(arr._data))

     list_metrics_matin.insert(0, target_metric)
     list_dict = pd.DataFrame({'var_name': list_metrics_matin})

     # print(list_metrics_matin)
     my_list.insert(0, np.reshape(arr_target, (8001,)))  # insert target metric
     matin_df = pd.DataFrame(my_list, index=list_metrics_matin, columns=output_cases).transpose()
     matin_df.astype('float32')
     # matin_df = matin_df.sort_index()
     unique_check = matin_df.apply(lambda x: x.nunique())
     matin_df = matin_df.drop(unique_check[unique_check == 1].index,
                              axis=1)  # drop variables whose values are all the same

     labels = ['out of spec' if i in list(fail_case_no) else 'ok' for i in output_cases]
     return matin_df, input_dict_df, labels

def passfail_boundary(matin_df, labels, cutoff_val, cutoff_val2, target_metric, boundary, arr_target):
    matin_df['fail_label'] = labels
    matin_lower = (matin_df[matin_df.fail_label == 'ok'])
    matin_upper = (matin_df[matin_df.fail_label == 'out of spec'])
    return matin_lower, matin_upper

def cutoff_boundary(matin_df, labels, cutoff_val, cutoff_val2, target_metric, boundary, arr_target):
    matin_df['fail_label'] = labels
    if len(cutoff_val2) == 0:
        matin_lower = matin_df.loc[matin_df[target_metric].astype(float) < float(cutoff_val)]
        matin_upper = matin_df.loc[matin_df[target_metric].astype(float) >= float(cutoff_val)]
    elif len(cutoff_val2) > 0:
        matin_lower = matin_df[(matin_df[target_metric].astype(float) >= float(cutoff_val)) & (matin_df[target_metric].astype(float) <= float(cutoff_val2))]
        matin_upper1 = matin_df[(matin_df[target_metric].astype(float) < float(cutoff_val))]
        matin_upper2 = matin_df[(matin_df[target_metric].astype(float) > float(cutoff_val2))]
        matin_upper = pd.concat([matin_upper1, matin_upper2])
    return matin_lower, matin_upper

def percentile_boundary(matin_df, labels, cutoff_val, cutoff_val2, target_metric, boundary, arr_target):
    matin_df['fail_label'] = labels
    matin_lower = matin_df.loc[matin_df[target_metric].astype(float) < np.percentile(arr_target, 100*float(boundary))]
    matin_upper = matin_df.loc[matin_df[target_metric].astype(float) >= np.percentile(arr_target, 100*float(boundary))]
    return matin_lower, matin_upper
################################################################################################################################################
#                              Boundary Conditions
################################################################################################################################################
