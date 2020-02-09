import json
import pandas as pd

import AT.recommendation.dialogue_functions as recommendation


def get_measurement_current_value(measurement, context):
    # Retrieve  and parse the (jsoned) telemetry feed values dataframe from the context
    values_json = context['screen']['current_telemetry_values']
    values_dataframe = pd.read_json(values_json)

    # Retrieve  and parse the (jsoned) telemetry feed info dataframe from the context
    info_json = context['screen']['current_telemetry_info']
    info_dataframe = pd.read_json(info_json)

    # Retrieve the measurement current value
    measurement_values_column = values_dataframe[measurement]
    last_measurement_value = measurement_values_column.iloc[-1]

    # Retrieve the measurement units
    meausrement_info_column = info_dataframe[measurement]
    units = meausrement_info_column['units']

    # Build the output dictionary
    result = {'measurement_value': last_measurement_value, 'measurement_units': units}

    return result
