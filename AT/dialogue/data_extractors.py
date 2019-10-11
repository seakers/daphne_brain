from dialogue.param_extraction_helpers import sorted_list_of_features_by_index, crop_list
import pandas as pd
import os


def extract_measurement(processed_question, number_of_features, context):
    filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_thresholds.csv')
    tf_thresholds = pd.read_csv(filename)
    tf_variables = list(tf_thresholds.columns)
    tf_variables.remove('threshold')
    measurements = tf_variables
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_timestamp(processed_question, number_of_features, context):
    timestamps = []
    for hr in range(0, 24):
        for min in range(0, 60):
            for sec in range(0, 60):
                str_hr = str(hr)
                str_min = str(min)
                str_sec = str(sec)
                if hr < 10:
                    str_hr = '0' + str_hr
                if min < 10:
                    str_min = '0' + str_min
                if sec < 10:
                    str_sec = '0' + str_sec
                string = str_hr + ':' + str_min + ':' + str_sec
                timestamps.append(string)

    return sorted_list_of_features_by_index(processed_question, timestamps, number_of_features)

extract_function = {}
extract_function["measurement"] = extract_measurement
extract_function["timestamp"] = extract_timestamp
