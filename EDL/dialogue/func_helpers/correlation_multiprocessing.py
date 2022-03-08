import json
import pickle

import matlab
import scipy

import numpy as np
import os
import yaml

from EDL.dialogue.MatEngine_object import eng1
from EDL.dialogue.func_helpers import CalculateFuncs, ScorecardDataFrameFuncs, get_variable_info
from EDL.models import EDLContextScorecards
from daphne_context.models import UserInformation
import pandas as pd
from multiprocessing import Pool

num_partitions = 16  # no. partitions to split dataframe
num_cores = 8


def parallelize_dataframe(matin_df, func, list_metrics_arm):
    matin_array = matin_df.to_numpy().transpose()
    # df_split = np.array_split(matin_df, num_partitions, axis=1)
    df_pairs = [(matin_array, i) for i in range(matin_array.shape[0])]
    pool = Pool(num_cores)
    df = (pool.map(func, df_pairs))[1:]
    df = [np.pad(item, (len(list_metrics_arm) - len(item), 0), 'constant') for item in df]
    df = pd.DataFrame(df, index=list_metrics_arm, columns=list_metrics_arm)
    return df


# Pearson Correlation Test
def vcorrcoef(arg_tuple):
    X_full, i = arg_tuple
    print("oi")
    X = X_full[i:, :]
    y = X_full[i, :]
    Xm = np.reshape(np.mean(X, axis=1), (X.shape[0], 1))
    ym = np.mean(y)
    r_num = np.sum((X - Xm) * (y - ym), axis=1)
    r_den = np.sqrt(np.sum((X - Xm) ** 2, axis=1) * np.sum((y - ym) ** 2))
    r = r_num / r_den
    print(i)
    return r