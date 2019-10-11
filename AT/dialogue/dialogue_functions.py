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


def show_measurement(data):

    answer = {}
    answer['task_is_successful'] = False
    answer['fail_explanation'] = 'Undefined (check file/timestamp existence)'
    answer['dataframe'] = None
    answer['thresholds'] =None

    filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed.csv')
    tf_data = pd.read_csv(filename)
    filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_thresholds.csv')
    tf_thresholds = pd.read_csv(filename)

    measurement = data['measurement']
    timestamp = data['timestamp']
    total_rows = len(tf_data.index)

    upper_limit = tf_thresholds.loc[1, measurement]
    lower_limit = tf_thresholds.loc[0, measurement]

    index = tf_data.loc[tf_data['timestamp'] == timestamp].index.values

    if len(index) > 0:
        n = 20
        row = index[0]
        lower_row = max(row - n, 0)
        upper_row = min(row + n, total_rows)
        answer['task_is_successful'] = True
        answer['dataframe'] = tf_data.iloc[lower_row:upper_row][['timestamp', measurement]]
        answer['thresholds'] = [lower_limit, upper_limit]

    return answer
