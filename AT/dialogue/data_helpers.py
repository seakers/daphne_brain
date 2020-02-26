import pandas as pd
import os
import urllib.parse
import json
import ast


def last_measurement_value_from_context(measurement, context):
    # Retrieve the (jsoned) telemetry values from the context.
    telemetry_values_json = context['screen']['current_telemetry_values']

    if telemetry_values_json == '':
        return None
    else:
        # Parse the telemetry feed from the context into a dictionary
        all_values_dict = ast.literal_eval(telemetry_values_json)

        # Check if the dictionary has a key with the requested measurement and proceed accordingly
        if measurement in all_values_dict:
            measurement_values_list = list(all_values_dict[measurement].values())
            last_measurement_value = measurement_values_list[-1]
        else:
            last_measurement_value = None

        return last_measurement_value


def pdf_link_from_procedure(procedure):
    path = os.path.join(os.getcwd(), "AT", "databases", "procedures", procedure + '.pdf')
    return urllib.parse.urlencode({"filename": path})