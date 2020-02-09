import json
import pandas as pd

import AT.recommendation.dialogue_functions as recommendation
from AT.neo4j_queries.query_functions import retrieve_thresholds_from_measurement


def get_measurement_current_value(measurement, context):
    # Retrieve the (jsoned) telemetry context. Raise an error if the telemetry context is empty
    values_json = context['screen']['current_telemetry_values']
    info_json = context['screen']['current_telemetry_info']
    if values_json != '' and info_json != '':
        # Parse the telemetry context (convert to dataframes)
        values_dataframe = pd.read_json(values_json)
        info_dataframe = pd.read_json(info_json)

        # Retrieve the measurement current value and units
        last_measurement_value = values_dataframe[measurement].iloc[-1]
        units = info_dataframe[measurement]['units']

        # Build the output dictionary
        result = {'measurement_value': last_measurement_value, 'measurement_units': units}
    else:
        print('The telemetry context is empty or incomplete.')
        result = {'measurement_value': 'None', 'measurement_units': 'None'}

    return result


def get_measurement_thresholds(measurement):
    # Retrieve  and parse the (jsoned) telemetry feed values dataframe from the context
    thresholds, units = retrieve_thresholds_from_measurement(measurement)

    # Parse the result
    result_list = []
    for key in thresholds:
        result = {'threshold_type': key, 'threshold_value': thresholds[key], 'threshold_units': units}
        result_list.append(result)

    return result_list
