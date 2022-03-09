import pandas as pd
import os
import urllib.parse
import json
import ast


def last_measurement_value_from_context(measurement, context):
    # Retrieve the (jsoned) telemetry values from the context.
    telemetry_values_json = context['screen']['current_telemetry_values']

    measurements = []
    if telemetry_values_json == '':
        return None
    else:
        # Parse the telemetry feed from the context into a dictionary
        all_values_dict = ast.literal_eval(telemetry_values_json)

        for item in all_values_dict:
            name = item.split(' (')[0]
            parameter_group = item[item.find('(') + 1: item.find(')')]
            measurements.append({'name': name, 'parameter_group': parameter_group, 'values': list(
                all_values_dict[item].values())})

        measurement_info_list = []
        # Check if the dictionary has a key with the requested measurement and proceed accordingly
        for item in measurements:
            if item.get('name') == measurement:
                measurement_values_list = item.get('values')
                last_measurement_value = measurement_values_list[-1]
                measurement_info_list.append({'name': item.get('name'), 'parameter_group': item.get(
                    'parameter_group'), 'value': last_measurement_value})

        return measurement_info_list


def pdf_link_from_procedure(procedure):
    path = os.path.join(os.getcwd(), "AT", "databases", "procedures", procedure + '.pdf')
    return urllib.parse.urlencode({"filename": path})
