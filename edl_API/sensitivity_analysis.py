from __future__ import division, absolute_import, print_function
import numpy as np
import os
import yaml
import pandas as pd
import pickle
import matlab.engine
from scipy.io import loadmat
import scipy.io
from scipy import stats
from daphne_API.edl import ScorecardDataFrameFuncs
from daphne_API.edl import get_variable_info
from daphne_API.edl import CalculateFuncs
from daphne_API.MatEngine_object import eng1
from daphne_API.models import UserInformation, EDLContextScorecards
from sklearn.utils import resample

from auth_API.helpers import get_or_create_user_information, get_user_information

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st


def run_SA(metric_name, user_info):

    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    input_dict_df = pd.read_excel('/Users/ssantini/Dropbox/Code/SensitivityAnalysis/input_deck_dict.xlsx')
    matfile_path = user_info.edlcontext.current_mat_file
    matfile_name = os.path.basename(matfile_path.replace(".mat", "_matin.mat"))
    matin_path = os.path.join('/Users/ssantini/Code/EDL_Simulation_Files_Inputs/m2020/', matfile_name)

    file_to_search = os.path.basename(matfile_path.replace(".mat", ".yml"))
    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=file_to_search, edl_context_id__exact=user_info.edlcontext.id)
    if scorecard_query.count() > 0:
        scorecard = scorecard_query.first()
        scorecard_labeled = pickle.loads(scorecard.current_scorecard_df)
        scorecard_labeled = scorecard_labeled.dropna()
        out_of_spec_df = pickle.loads(scorecard.current_scorecard_df_fail)
        out_of_spec_df = out_of_spec_df.dropna()

    variable_loc, arr, outofspec_indices, fail_case_no, flag_indices, flag_case_no = get_variable_info.locate_variable(
        str.lower(metric_name), scorecard_labeled, out_of_spec_df, matfile_path, 'all cases')

    if metric_name == 'major axis ':
        metric_output = arr.reshape(1,3600)
    else:
        metric_output = arr.reshape(1, 8001)

    input_deck = loadmat(matin_path)
    input_cases = [item for sublist in (input_deck['input_case']).tolist() for item in sublist]

    eng1.load(matfile_path, 'output_case', nargout = 0)
    eng1.workspace['output_case']
    eng1.eval('who')
    output_case = list(fail_case_no)

    ''' get indices that match input and output case'''
    labels = ['out of spec' if i in output_case else 'ok' for i in input_cases]
    eng1.load(matin_path, nargout=0)

    list_metrics_matin = scipy.io.whosmat(matin_path)
    list_metrics_matin = [i[0] for i in list_metrics_matin]

    '''Lists for Sobol and SA '''
    my_list = []
    for i in range(len(list_metrics_matin)):
        arr = eng1.eval(list_metrics_matin[i])
        my_list.append(np.asarray(arr._data))

    ''' Convert matin into a dataframe '''
    matin_df = pd.DataFrame(my_list, index=list_metrics_matin, columns=input_cases).transpose().drop('check', axis=1)
    matin_df['fail_label'] = labels
    matin_pass_df = (matin_df[matin_df.fail_label == 'ok']).drop(['fail_label', 'input_case'], axis=1)
    matin_fail_df = (matin_df[matin_df.fail_label == 'out of spec']).drop(['fail_label', 'input_case'], axis=1)


    ''' K-S test'''
    p_vals = []
    description = []
    label = []
    model = []
    counter = 0
    distance =[]
    for column in matin_fail_df:
        #print(column)
        counter += 1

        if matin_fail_df.shape[0] < matin_pass_df.shape[0] and (matin_fail_df.shape[0]/matin_pass_df.shape[0]) < 0.35:

            arr1 = (matin_pass_df[column]).values
            arr2 = (matin_fail_df[column]).values
            arr1.reshape(1, len(arr1))
            arr2.reshape(1, len(arr2))
            boot = resample(arr2, replace=True, n_samples=(matin_pass_df.shape[0] - matin_fail_df.shape[0]),
                            random_state=1)
            #arr2 = boot.reshape(len(boot), 1)
            # arr2 = arr2.reshape(1, len(arr2))
        # string_ev = 'corrcoef(' + str(column) + '(output_case),a)'
        # corr_mat = eng1.eval(string_ev)
            test_result = stats.ks_2samp(arr1, boot)
            p_vals.append(test_result[1])
            distance.append(test_result[0])
            description.append((input_dict_df[input_dict_df['Variable'].str.contains(column)].Description.array[0]))
            label.append((input_dict_df[input_dict_df['Variable'].str.contains(column)].Label.array[0]))
            model.append((input_dict_df[input_dict_df['Variable'].str.contains(column)].Model.array[0]))

    ''' Put results together into dataframe'''
    print(list_metrics_matin)
    df_results = pd.DataFrame(
        {'metric_name': list(matin_pass_df.columns), 'p_vals': p_vals, 'description': description, 'label': label,
         'model': model, 'distance': distance}).sort_values(by='distance', ascending= False)

    sub_df = df_results.iloc[0:15, :]
    #sub_df = df_results.tail(15)

    return sub_df