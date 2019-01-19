import yaml
import pandas as pd
import numpy as np
from numpy import nan
import os, sys

def generate_scorecard_dataframe(scorecard_dict):
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
                and scorecard_dataframe_labeled['direction'][i] != 'N/A' and pd.isna(scorecard_dataframe_labeled['out_of_spec'][i]) != True\
                and scorecard_dataframe_labeled['out_of_spec'][i] != 0 and scorecard_dataframe_labeled['flag'][i] != 0:
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
            status_list.append(('N/A'))

    status_df = pd.DataFrame({'status': status_list})
    scorecard_dataframe_labeled['status'] = status_df
    return scorecard_dataframe_labeled