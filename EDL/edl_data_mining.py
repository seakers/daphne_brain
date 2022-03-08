from __future__ import division, absolute_import, print_function
import os
import pandas as pd
import pickle
from scipy.io import loadmat
import scipy.io
from scipy import stats
from sklearn.utils import resample

from EDL.api import EDLDataMiningClient
from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import get_variable_info
from EDL.models import EDLContextScorecards
from auth_API.helpers import get_or_create_user_information, get_user_information
import numpy as np


def run_datamining_edl(selected_cases, target_metric, matout_path, cases_option, percentile, direction, user_info):



    scorecard_query = EDLContextScorecards.objects.filter(scorecard_name__exact=os.path.basename(matout_path).replace(".mat", ".yml")).first()
    complete_scorecard = pickle.loads(scorecard_query.current_scorecard_df)
    flagged_scorecard = pickle.loads(scorecard_query.current_scorecard_df_flag)
    outofspec_scorecard = pickle.loads(scorecard_query.current_scorecard_df_fail)
    ###################################################################################################################
    # Check where the parameter requested exists in scorecard. Then check if it
    # is out of spec or flagged (since array would exist). If not, generate array.
    ''' Check if it is a matin file'''
    scorecard_metrics = (complete_scorecard['metric_name']).tolist()
    scorecard_metrics = [x.lower() for x in scorecard_metrics if x is not None]
    matout_metrics  = [i[0] for i in scipy.io.whosmat(matout_path)]

    var_loc, arr_target, outofspec_indices1, fail_case_no1, flag_indices1, flag_case_no1 = get_variable_info.locate_variable(
        target_metric, complete_scorecard,
        outofspec_scorecard, matout_path, 'all cases')
    if var_loc == 'out of spec scorecard metric, array existed':
        df_row = outofspec_scorecard.loc[outofspec_scorecard['metric_name'].str.lower() == str(target_metric).lower()].iloc[:1]
        equation = [(df_row["calculation"]).to_string(index = False)]
    if var_loc == 'flagged scorecard metric, array was calculated':
        df_row = complete_scorecard.loc [complete_scorecard['metric_name'].str.lower() == str(target_metric).lower()].iloc[:1]
        equation = [(df_row["calculation"]).to_string(index = False)]
    else:
        equation = [target_metric]
    ###################################################################################################################
    # Check event of metric of interest, delete
    events = ['_ei', '_rc', '_rev1', '_end1', '_hda', '_sufr', '_pd', '_hs', '_bs', '_sky','_td']
    for item in equation:
        event_search = [ele for ele in events if(ele in item)]
        event_position = [i for i, item in enumerate(events) if item in set(event_search)]
        if len(event_position) > 1:
            target_event = events[min(event_position)]
        else:
            target_event = events[event_position[0]]
        check = next((True for events in events if target_event in events), False)
        if check == True:
            targetibdex = events.index(target_event)
            del events[targetibdex: len(events)]
    ###################################################################################################################
    # Only keep variables that are in this event
    # Get variables from matfile
    list_metrics_matout = scipy.io.whosmat(matout_path)
    list_metrics_matout_clean = [i[0] for i in list_metrics_matout]

    # Just for checking, below are the events in the matfile, we had roughly 806 events. For an initial approach,
    # we selected the events in the previous section, which result in ~2,500 variables
    # list_all_events = [words for segments in list_metrics_matout_clean for words in segments.split('_')[-1:]]
    # list_all_events = (list(set(list_all_events)))

    list_metrics_arm = []
    for substring in events:
        list_variables = [s for s in list_metrics_matout_clean if s.endswith(substring)]
        list_metrics_arm.append(list_variables)
    list_metrics_arm = [item for sublist in list_metrics_arm for item in sublist]

    # Start engine
    eng1.load(matout_path, nargout = 0)
    eng1.load(matout_path, 'output_case', nargout=0)
    output_cases = [item for sublist in np.array(eng1.workspace['output_case']).tolist() for item in sublist]

    my_list = []
    for i in range(len(list_metrics_arm)):
        arr = eng1.eval(list_metrics_arm[i])
        my_list.append(np.asarray(arr._data))

    list_metrics_arm.insert(0, target_metric)
    my_list.insert(0, np.reshape(arr_target, (8001,))) #insert target metric 

    # Convert to dataframe so we can then convert it to a .dat file for Harris' code
    arm_df = pd.DataFrame(my_list, index=list_metrics_arm, columns=output_cases).transpose()
    arm_df.astype('float32')
    arm_df = arm_df.sort_index()
    
    #remove arrays whose values are all the same
    unique_check = arm_df.apply(lambda x: x.nunique())
    arm_df_unique = arm_df.drop(unique_check[unique_check==1].index, axis=1)
    arm_df_unique = arm_df.drop(unique_check[unique_check < 50].index, axis=1)
    arm_df_unique = arm_df_unique.loc[:, ~arm_df_unique.columns.duplicated()] #some columns seem to be repeated, drop duplicates 
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex = 'specv')))]
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex = 'xmax')))]# this was causing issues in discretizing
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex='xmin')))]
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex='nf_solution_strength')))]
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex='vterm_sky')))]
    arm_df_unique = arm_df_unique[arm_df_unique.columns.drop(list(arm_df_unique.filter(regex='num_replans')))]
    list_metrics_unique = list(arm_df_unique.columns.values) # update the list of metrics without duplicates

    df_arm_class = arm_df_unique[list_metrics_unique] # copy

    if percentile in ["0.25", "0.50", "0.75"]:
        value = float(percentile)
        idx = ["0", "0.25", "0.50", "0.75"].index(percentile)
        binning = "quartile"
        q = 4
        labels = ["0"]*q
        optionss = ["0", "0.25", "0.50", "0.75"]
    elif percentile in ["0.1", "0.9"]:
        q = 10
        binning = "deciles"
        labels = ["0"]*q
        optionss = [str(i/10) for i in range(len(np.arange(0, 1, 0.1).tolist()))]
        idx = optionss.index(percentile)
    elif percentile in ["0.01", "0.99"]:
        q = 100
        binning = 'tails'
        labels = ["0"]*q
        optionss = [str(i / 100) for i in range(len(np.arange(0, 1, 0.01).tolist()))]
        idx = optionss.index(percentile)

    if direction == "below":
        labels = [labels[i].replace("0", "1") if i < idx else labels[i].replace("0", "0") for i in range(len(labels))]
    elif direction == "above":
        labels = [labels[i].replace("0", "0") if i < idx else labels[i].replace("0", "1") for i in
                  range(len(labels))]

    for item in list_metrics_unique:
            arr = df_arm_class[item]
            print(item)
            if list_metrics_unique.index(item) == 0:
               df_arm_class[item] = pd.qcut(x=arr, q=q, labels=optionss, duplicates='drop')
               if direction == "below":
                   df_arm_class[item] = (df_arm_class[item].astype(float) < float(percentile)).astype(float)
                   df_arm_class[item]= df_arm_class[item].round(0).astype(int)
               elif direction == "above":
                   df_arm_class[item] = (df_arm_class[item].astype(float) >= float(percentile)).astype(float)
                   df_arm_class[item] = df_arm_class[item].round(0).astype(int)
               else:
                   df_arm_class.crossrng_bs = (df_arm_class.crossrng_bs.astype(float) < float(percentile)).astype(float)
            else:
                df_arm_class[item] = pd.qcut(x=arr, q=[0, 0.01, 0.25, .75, .99, 1],
                                         labels=['0', '1', '2', '3', '4'], duplicates='drop')

    df_arm_class = df_arm_class.dropna()

    if cases_option == 'plot-selection':
        selected_cases = selected_cases
        df_arm_class = df_arm_class.ix[selected_cases]
        
    # Save as CSV
    df_arm_class.to_csv('/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/datamining_sets/test6.dat', header=True, index = True )
    file_path = '/Users/ssantini/Code/Code_Daphne/daphne_brain/EDL/data/datamining_sets/test6.dat'
    class_no = 1
    no_params = len(df_arm_class.columns)
    client = EDLDataMiningClient()
    client.start_connection()
    features = client.get_driving_features(file_path, class_no, no_params)
    client.end_connection()

    return features