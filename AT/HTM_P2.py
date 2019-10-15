from __future__ import division

import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
import time
import datetime as dt  # Imports dates library

from nupic.encoders import RandomDistributedScalarEncoder
from nupic.encoders.date import DateEncoder
from nupic.algorithms.spatial_pooler import SpatialPooler
from nupic.algorithms.temporal_memory import TemporalMemory


from scipy.stats import norm


class Encoder:  # Defines an encoder class to put into the variables of the
    def __init__(self, variable, encoders):
        self.variable = variable
        self.encoders = encoders


def multiencode(encoders, Data, iter):
    res = [0]
    for x in encoders:
        for y in x.encoders:
            eval("enc = " + y + ".encode(Data['" + x.variable + "'][iter])", locals(), globals())
            res = np.concatenate([res, enc])
    return res[1:]

# Index must be provided as another column in order to be considered a variable


def HTM_AD(Data='Test',
           vars={'value':['num']},
           prec_param=5,
           pooler_out=2024,  # Number of columns of the pooler output
           cell_col=5,  # HTM cells per column
           W=72,  # Window parameter
           W_prim=5,  # Local window for anomaly detection likelihood
           eps=1e-6,  # to Avoid by zero divisions
           athreshold=0.95):
    """
    This function performs HTM based anomaly detection on a time series provided
    :param Data:
    :param vars: Possible values: num, tod, weekend
    :param prec_param: A parameter that defines how much precision the number encoder has
        The encoder precision depends on the variability of the data,
        The real precision is computed taking into account both the precision parameter and data std
        A high precision might mean a high error at predicting the variable value in noisy variables
    :param pooler_out: Number of columns of the pooler output
    :param cell_col: HTM cells per column
    :param W: Window parameter
    :param W_prim: Local window for anomaly detection likelihood
    :param eps: to Avoid by zero divisions
    :param athreshold: To classify based on anomaly likelihood whether there is an anomaly or not
    :return: The Data + 3 columns
        Anomaly: indicates the error of within the value predicted by the HTM network
        Anomaly_likelihood: indicates the likelihood of the data into being anomalous
        Anomaly_flag: classifies the data in anomalous vs non anomalous
    """

    if Data == 'Test':  # If there is not data available, simply loads the temperature benchmark dataset
        # Import data
        Data = pd.read_csv('AT/Data/sample.csv',
                           parse_dates=True,
                           index_col='timestamp')
        Data = Data.resample('H').bfill().interpolate()


    TODE = DateEncoder(timeOfDay=(21, 1))
    WENDE = DateEncoder(weekend=21)

    var_encoders = set()
    # Spatial Pooler Parameters
    for x in vars:
        for y in vars[x]:
            if y == 'num':
                exec("RDSE_" + x + " = RandomDistributedScalarEncoder(resolution=Data['" + x + "'].std()/prec_param)",
                     locals(), globals())
                var_encoders.add(Encoder(x, ["RDSE_" + x]))
            elif y == 'weekend':
                var_encoders.add(Encoder(x, ["WENDE"]))
            elif y == 'tod':
                var_encoders.add(Encoder(x, ["TODE"]))
            else:
                return {"error": "Variable encoder type is not recognized "}

    encoder_width = 0  # Computes encoder width
    for x in var_encoders:
        for y in x.encoders:
            exec("s = " + y + ".getWidth()", locals(), globals())
            encoder_width += s


    SP = SpatialPooler(inputDimensions=encoder_width,
                       columnDimensions=pooler_out,
                       potentialPct=0.8,
                       globalInhibition=True,
                       numActiveColumnsPerInhArea=pooler_out//50,  # Gets 2% of the total area
                       boostStrength=1.0,
                       wrapAround=False)
    TM = TemporalMemory(columnDimensions=(pooler_out,),
                        cellsPerColumn=cell_col)

    Data['Anomaly'] = 0.0
    Data['Anomaly_Likelihood'] = 0.0

    # Train Spatial Pooler
    print("Spatial pooler learning")

    start = time.time()

    active_columns = np.zeros(pooler_out)

    for x in range(len(Data)):
        encoder = multiencode(var_encoders, Data, x)
        SP.compute(encoder, True, active_columns)

    end = time.time()
    print(end - start)

    # Temporal pooler
    print("Temporal pooler learning")

    start = time.time()

    A_score = np.zeros(len(Data))
    for x in range(len(Data)):
        encoder = multiencode(var_encoders, Data, x)
        SP.compute(encoder, False, active_columns)
        col_index = active_columns.nonzero()[0]
        TM.compute(col_index, learn=True)
        if x > 0:
            inter = set(col_index).intersection(Prev_pred_col)
            inter_l = len(inter)
            active_l = len(col_index)
            A_score[x] = 1 - (inter_l / active_l)
            Data.iat[x, -2] = A_score[x]
        Prev_pred_col = list(set(x // cell_col for x in TM.getPredictiveCells()))

    end = time.time()
    print(end - start)

    AL_score = np.zeros(len(Data))
    # Computes the likelihood of the anomaly
    for x in range(len(Data)):
        if x > 0:
            W_vec = A_score[max(0, x-W): x]
            W_prim_vec = A_score[max(0, x-W_prim): x]
            AL_score[x] = 1 - 2*norm.sf(abs(np.mean(W_vec)-np.mean(W_prim_vec))/max(np.std(W_vec), eps))
            Data.iat[x, -1] = AL_score[x]

    Data['Anomaly_flag'] = athreshold < Data['Anomaly_Likelihood']

    return Data
