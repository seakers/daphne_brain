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
        # Ugly patch. The commented block of code underneath should be used. It worked at some point, but right now
        # it's giving an error that I don't understand nor know how to fix.
        all_values_dict = ast.literal_eval(telemetry_values_json)
        measurement_values_list = list(all_values_dict[measurement].values())
        last_measurement_value = measurement_values_list[-1]

        # values_dataframe = pd.read_json(values_json)
        # last_measurement_value = values_dataframe[measurement].iloc[-1]
        # last_measurement_value = round(last_measurement_value, 5)
        return last_measurement_value


def pdf_link_from_procedure(procedure):
    path = os.path.join(os.getcwd(), "AT", "databases", "procedures", procedure + '.pdf')
    return urllib.parse.urlencode({"filename": path})