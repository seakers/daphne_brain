import pandas as pd
import matlab.engine
import json
import numpy as np
from daphne_API.edl import ScorecardDataFrameFuncs


def locate_variable(metric_name, scorecard_dataframe, out_of_spec_df, matfile_path, criteria):
    check1 = scorecard_dataframe['metric_name'].str.lower() == metric_name # check in scorecard
    index1 = check1[check1 == True].index.tolist() # get indices
    check2 = out_of_spec_df['metric_name'].str.lower() == metric_name# check in out of spec if array exists
    index2 = check2[check2 == True].index.tolist()  # get indices

    if metric_name in list(scorecard_dataframe['metric_name'].str.lower()):
        this = 'string exists'
        index1 = this
    if metric_name in list(out_of_spec_df['metric_name'].str.lower()):
        index2 = 'string exists in scorecard'


    variable_location = []
    metric_array = []
    fail_indices = []
    fail_case_no = []
    flag_case_no = []
    flag_indices = []

    if len(index1) > 0 and len(index2) > 0:
        variable_location = 'metric is in scorecard and it is an out of spec metric'
        metric_array = out_of_spec_df.loc[out_of_spec_df.metric_name.str.lower() == metric_name, 'arrays'].values[0]
        #metric_array = out_of_spec_df[out_of_spec_df["metric_name"].str.lower().str.contains(metric_name)].arrays.array[0]
        sub_df = out_of_spec_df[((out_of_spec_df.metric_name).str.lower() == metric_name)].iloc[[0]]
        fail_indices, fail_case_no, flag_indices, flag_case_no = ScorecardDataFrameFuncs.get_case_numbers(metric_name, sub_df, matfile_path, criteria)


    elif len(index1) > 0 and len(index2) == 0:
        variable_location = 'scorecard metric but not out of spec, requires calculating metric'
        sub_df = scorecard_dataframe[((scorecard_dataframe.metric_name).str.lower() == metric_name)]
        sub_df = sub_df.drop_duplicates(subset='metric_name')
        #df_index = sub_df.index.tolist()
        metric_array = ScorecardDataFrameFuncs.get_scorecard_arrays(sub_df, matfile_path)
        sub_df['arrays'] = pd.Series((metric_array), index = sub_df.index)
        metric_array = metric_array[0]
        fail_indices, fail_case_no, flag_indices, flag_case_no = ScorecardDataFrameFuncs.get_case_numbers(metric_name, sub_df, matfile_path, criteria)
        i = 1

    elif len(index1) == 0 and len(index2) == 0:
        variable_location = 'it is probably a matfile variable'
        eng1 = matlab.engine.start_matlab()
        eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
        eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

        '''Load as dictionary'''
        dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

        if dict_NL.get(metric_name):
            param_name1 = dict_NL[metric_name]

        else:
            param_name1 = metric_name
        var2_mat = eng1.load(matfile_path, param_name1, nargout=0)
        val2 = eng1.workspace[param_name1]
        metric_array = np.asarray(val2)
        out_of_spec_indices = []
        fail_case_no= np.array([])
        flag_case_no = np.array([])
        fail_indices = []
        flag_indices = []
    else:
        variable_location = 'variable does not exist'


    return variable_location, metric_array, fail_indices, fail_case_no, flag_indices, flag_case_no

