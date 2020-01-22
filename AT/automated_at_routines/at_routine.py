import time


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
        message = 'LCT'
    elif zone == -1:
        message = 'LWT'
    elif zone == 0:
        message = 'nominal'
    elif zone == 1:
        message = 'HWT'
    elif zone == 2:
        message = 'HCT'
    else:
        print('Invalid zone value')
        raise

    return message


def build_symptoms_report(window):
    """
    This function checks the status of the trace and builds the proper warning messages if necessary.
    """

    # Input parse
    values = window['values']
    # values = values.drop(labels='timestamp', axis='columns')
    info = window['info']

    # Iteration over each telemetry feed variable's trace to search anomalies and build the proper message
    symptoms_report = []
    for variable in values:
        # Retrieve trace as an array
        trace = list(values[variable])

        # Check and build the threshold and forecast messages
        last_point = trace[-1]
        variable_info = info[variable]
        threshold_message = threshold_check(last_point, variable_info)
        if threshold_message != '' and threshold_message != 'nominal':
            text = variable + ' is ' + threshold_message + '.'
            event = {'parameter': variable, 'symptom': threshold_message, 'text': text}
            symptoms_report.append(event)

    return symptoms_report


def anomaly_treatment_routine(hub_to_at, at_to_hub):
    print('AD thread started')

    keep_alive = True
    while keep_alive:
        while not hub_to_at.empty():
            signal = hub_to_at.get()
            if signal['type'] == 'stop':
                keep_alive = False
            elif signal['type'] == 'window':
                # To prevent the anomaly detection thread from falling behind the telemetry feed, empty the queue and
                # only process the last received window
                if hub_to_at.empty():
                    window = signal['content']
                    symptoms_report = build_symptoms_report(window)

                    # Send message to frontend
                    at_to_hub.put({'type': 'symptoms_report', 'content': symptoms_report})

        time.sleep(0.5)

    print('Anomaly treatment thread stopped.')
    return
