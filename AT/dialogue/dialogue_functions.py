import pandas as pd
import os


def find_last_anomaly():
    # Read and store the (false) telemetry feed and thresholds .csv files

    filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed.csv')
    tf_data = pd.read_csv(filename)
    filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_thresholds.csv')
    tf_thresholds = pd.read_csv(filename)

    tf_variables = list(tf_data.columns)
    tf_variables.remove('timestamp')
    n_rows = len(tf_data.index)
    n_columns = len(tf_data.columns)

    anomaly_list = []
    is_anomaly = False
    row = n_rows - 1
    while is_anomaly == False and row >= 0:
        anomaly_item = {}
        timestamp = tf_data.loc[row, 'timestamp']
        for variable in tf_variables:
            val = float(tf_data.loc[row, variable])
            if val > float(tf_thresholds.loc[1, variable]):
                is_anomaly = True
                anomaly_item['variable'] = variable.capitalize()
                anomaly_item['type'] = 'above'
                anomaly_item['timestamp'] = timestamp
                anomaly_list.append(anomaly_item)
            elif val < float(tf_thresholds.loc[0, variable]):
                is_anomaly = True
                anomaly_item['variable'] = variable.capitalize()
                anomaly_item['type'] = 'below'
                anomaly_item['timestamp'] = timestamp
                anomaly_list.append(anomaly_item)
        row = row - 1

    return anomaly_list
