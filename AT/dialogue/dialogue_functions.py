import pandas as pd
import json
import os

import AT.recommendation.dialogue_functions as recommendation


def find_last_anomaly():
    # Read and store the (false) telemetry feed and thresholds .csv files
    filename = 'C:/Users/oscar/Desktop/SEAK LAB/Telemetry feed/telemetry_feed.csv'
    tf_data = pd.read_csv(filename)
    filename = 'C:/Users/oscar/Desktop/SEAK LAB/Telemetry feed/telemetry_feed_thresholds.csv'
    tf_thresholds = pd.read_csv(filename)

    tf_variables = list(tf_data.columns)
    tf_variables.remove('timestamp')
    n_rows = len(tf_data.index)
    n_columns = len(tf_data.columns)

    variables = []
    types = []
    timestamp = None

    is_anomaly = False
    row = n_rows - 1
    while is_anomaly == False and row >= 0:
        for variable in tf_variables:
            val = float(tf_data.loc[row, variable])
            if val > float(tf_thresholds.loc[1, variable]):
                is_anomaly = True
                variables.append(variable)
                types.append('above')
            elif val < float(tf_thresholds.loc[0, variable]):
                is_anomaly = True
                variables.append(variable)
                types.append('below')

        timestamp = tf_data.loc[row, 'timestamp']
        row = row - 1

    return variables, types, timestamp
