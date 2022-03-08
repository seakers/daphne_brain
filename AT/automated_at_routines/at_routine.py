import time
from statsmodels.tsa import ar_model


def compute_zone(value, info):
    """
    This function returns an integer depending on the threshold zone on which a value is located.
    """

    zone = 0
    if value <= info['low_critic_threshold']:
        zone = -2
    elif value <= info['low_warning_threshold']:
        zone = -1
    elif value <= info['high_warning_threshold']:
        zone = 0
    elif value <= info['high_critic_threshold']:
        zone = 1
    else:
        zone = 2

    return zone


def threshold_check(value, info):
    """
    This function returns an string depending on the threshold zone on which a value is located.
    """

    message = ''
    zone = compute_zone(value, info)
    if zone == -2:
        message = 'below low critical threshold'
    elif zone == -1:
        message = 'below low warning threshold'
    elif zone == 0:
        message = ''
    elif zone == 1:
        message = 'above high warning threshold'
    elif zone == 2:
        message = 'above high critical threshold'
    else:
        print('Invalid zone value')
        raise

    return message


def forecast_check(trace, info):
    """
    This function uses a trace to forecast its evolution, and then builds a warning message if such forecast becomes
    anomalous (outside thresholds).
    """

    # Input parse
    last_point = trace[-1]
    base_zone = compute_zone(last_point, info)

    # AR model fitting and prediction
    forecast_span = 120  # number of points to forecast (its value in seconds depends on the simulation configuration)
    start_index = len(trace) - 1
    end_index = start_index + forecast_span
    model = ar_model.AR(endog=trace)
    results = model.fit()
    prediction = results.predict(start=start_index, end=end_index)

    # Anomaly check
    second = 1
    message = ''
    for value in prediction:
        zone = compute_zone(value, info)
        if zone != base_zone:
            if zone == -2:
                message = 'low critical zone in ' + str(second) + ' seconds'
            elif zone == -1:
                message = 'low warning zone in ' + str(second) + ' seconds'
            elif zone == 0:
                message = 'nominal zone in ' + str(second) + ' seconds'
            elif zone == 1:
                message = 'high warning zone in ' + str(second) + ' seconds'
            elif zone == 2:
                message = 'high critical zone in ' + str(second) + ' seconds'
            else:
                print('Invalid zone value')
                raise
            break

        second += 1
    return message


def build_message(window):
    """
    This function checks the status of the trace and builds the proper warning messages if necessary.
    """

    # Input parse
    values = window['values']
    values = values.drop(labels='timestamp', axis='columns')
    info = window['info']

    # Iteration over each telemetry feed variable's trace to search anomalies and build the proper message
    messages = []
    for item in values:
        # Retrieve trace as an array
        trace = list(values[item])

        # Check and build the threshold and forecast messages
        threshold_message = threshold_check(trace[-1], info[item])
        forecast_message = forecast_check(trace, info[item])
        if threshold_message != '':
            message = item.capitalize() + ' is ' + threshold_message + '.'
            messages.append(message)
        if forecast_message != '':
            message = item.capitalize() + ' might switch to ' + forecast_message + '.'
            messages.append(message)

    if len(messages) == 0:
        messages.append('OK')

    return messages


def anomaly_treatment_routine(hub_to_at, at_to_hub):
    print('AD thread started')

    keep_alive = True
    while keep_alive:
        while not hub_to_at.empty():
            signal = hub_to_at.get()
            if signal['type'] == 'stop':
                keep_alive = False
                # at_to_hub.put({'type': 'stop', 'content': ''})
            elif signal['type'] == 'window':
                # To prevent the anomaly detection thread from falling behind the telemetry feed, empty the queue and
                # only process the last received window
                if hub_to_at.empty():
                    window = signal['content']
                    anomaly_list = build_message(window)

                    # Trigger diagnosis here

                    # Send message to frontend
                    at_to_hub.put({'type': 'diagnosed_anomalies', 'content': anomaly_list})

        time.sleep(0.5)

    print('Anomaly treatment thread stopped.')
    return
