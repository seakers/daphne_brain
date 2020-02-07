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


def build_threshold_tag(value, info):
    """
    This function returns an string depending on the threshold zone on which a value is located.
    In the knowledge graph with the information about the anomalies, the word "limit" is used instead of "threshold",
    and hence the change of nomenclature here. Also, no distinction is made when being beyond the warning limit.
    """

    tag = ''
    zone = compute_zone(value, info)
    if zone == -2:
        tag = 'LCL'
    elif zone == -1:
        tag = 'LWL'
    elif zone == 0:
        tag = 'nominal'
    elif zone == 1:
        tag = 'UWL'
    elif zone == 2:
        tag = 'UCL'
    else:
        print('Invalid zone value')
        raise

    return tag


def build_detection_text(variable, threshold_tag):
    text = ''
    if threshold_tag == 'LCL':
        text = variable + ': Is below Lower Critic Limit.'
    elif threshold_tag == 'LWL':
        text = variable + ': Is below Lower Warning Limit.'
    elif threshold_tag == 'UWL':
        text = variable + ': Is above Upper Warning Limit.'
    elif threshold_tag == 'UCL':
        text = variable + ': Is above Upper Critic Limit.'
    else:
        print('Invalid threshold tag')
        raise

    return text


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
        threshold_tag = build_threshold_tag(last_point, variable_info)
        if threshold_tag != '' and threshold_tag != 'nominal':
            detection_text = build_detection_text(variable, threshold_tag)
            event = {'measurement': variable,
                     'detection_text': detection_text,
                     'threshold_tag': threshold_tag}
            symptoms_report.append(event)

    return symptoms_report


def anomaly_treatment_routine(hub_to_at, at_to_hub):

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
