import pandas as pd


def last_measurement_value_from_context(measurement, context):
    # Retrieve the (jsoned) telemetry values from the context.
    values_json = context['screen']['current_telemetry_values']

    if values_json == '':
        return None
    else:
        values_dataframe = pd.read_json(values_json)
        last_measurement_value = values_dataframe[measurement].iloc[-1]
        last_measurement_value = round(last_measurement_value, 5)
        return last_measurement_value
