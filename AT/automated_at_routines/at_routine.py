import time


def compute_zone(value, info):
    """
    This function returns an integer depending on the threshold zone on which a value is located.
    """

    zone = 0
    if value <= info['low_warning_threshold']:
        zone = -2
    elif value <= info['low_caution_threshold']:
        zone = -1
    elif value <= info['high_caution_threshold']:
        zone = 0
    elif value <= info['high_warning_threshold']:
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
        tag = 'LowerWarningLimit'
    elif zone == -1:
        tag = 'LowerCautionLimit'
    elif zone == 0:
        tag = 'nominal'
    elif zone == 1:
        tag = 'UpperCautionLimit'
    elif zone == 2:
        tag = 'UpperWarningLimit'
    else:
        print('Invalid zone value')
        raise

    return tag


def build_detection_text(variable, threshold_tag):
    text = ''
    if threshold_tag == 'LowerWarningLimit':
        text = variable + " " + 'Exceeds Lower Warning Limit'
    elif threshold_tag == 'LowerCautionLimit':
        text = variable + " " + 'Exceeds Lower Caution Limit'
    elif threshold_tag == 'UpperCautionLimit':
        text = variable + " " + 'Exceeds Upper Caution Limit'
    elif threshold_tag == 'UpperWarningLimit':
        text = variable + " " + 'Exceeds Upper Warning Limit'
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
            display_name = variable_info['display_name']
            event = {'measurement': variable,
                     'display_name': display_name,
                     'detection_text': detection_text,
                     'threshold_tag': threshold_tag}
            symptoms_report.append(event)

    return symptoms_report


def symptom_reports_are_equal(old_report, new_report):
    if len(old_report) != len(new_report):
        return False
    else:
        N = len(old_report)
        are_equal = True
        for i in range(0, N):
            old_display_name = old_report[i]['display_name']
            new_display_name = new_report[i]['display_name']
            old_threshold_tag = old_report[i]['threshold_tag']
            new_threshold_tag = new_report[i]['threshold_tag']
            same_name = (old_display_name == new_display_name)
            same_tag = (old_threshold_tag == new_threshold_tag)
            if not same_name or not same_tag:
                are_equal = False
        return are_equal


def decide_alarm(old_report, new_report, t_nominal, cs_is_pending, cs_wait):
    # Check whether the previous and new symptoms reports are equal or not
    are_equal = symptom_reports_are_equal(old_report, new_report)

    # Act depending on the case
    if are_equal and len(old_report) != 0:
        # This means that the symptoms reports are equal and nonempty. No new anomalies have appeared and no clear sound
        # should is pending.
        return 'None', t_nominal, False
    else:
        if len(new_report) == 0 and len(old_report) != 0:
            # This means that the situation just switched to nominal. No clear sound is triggered since we want to wait
            # a safe time before doing so. Hence we mark the clear sound as pending and compute the time in which this
            # switch took place.
            return 'None', time.time(), True
        elif len(new_report) == 0 and len(old_report) == 0:
            # This means that the situation has been nominal for a while. Hence we check our auxiliary variables.
            elapsed_time = time.time() - t_nominal
            if elapsed_time >= cs_wait and cs_is_pending:
                # If we waited pass the safe time and the clear sound is pending, then we emmit a clear sound.
                return 'alarmOut', t_nominal, False
            else:
                # Do nothing otherwise
                return 'None', t_nominal, cs_is_pending
        else:
            # We can only get here if the symptoms reports are not equal and the new one is not empty. Hence we make an
            # alarm sound.
            return 'alarmIn', t_nominal, False


def anomaly_treatment_routine(hub_to_at, at_to_hub):
    keep_alive = True
    last_symptoms_report = []
    t_nominal = -1  # This variable is used to store the last time the telemetry switched from off nominal to nominal
    cs_is_pending = False  # cs stand for "clear sound"
    cs_wait = 5  # cs stands for "clear sound"

    # Set the ping routine counters
    life_limit = 40.
    time_since_last_ping = 0.
    current_time = time.time()

    while keep_alive and time_since_last_ping < life_limit:
        time_since_last_ping = time.time() - current_time
        while not hub_to_at.empty():
            signal = hub_to_at.get()
            if signal['type'] == 'stop':
                keep_alive = False
            elif signal['type'] == 'ping':
                current_time = time.time()
            elif signal['type'] == 'window':
                # To prevent the anomaly detection thread from falling behind the telemetry feed, empty the queue and
                # only process the last received window
                if hub_to_at.empty():
                    window = signal['content']
                    # Build the new symptoms report

                    symptoms_report = build_symptoms_report(window)

                    # Decide if an alarm has to be triggered or not
                    alarm, t_nominal, cs_is_pending = decide_alarm(last_symptoms_report, symptoms_report,
                                                                   t_nominal, cs_is_pending, cs_wait)

                    # Update the last symptoms report
                    last_symptoms_report = symptoms_report

                    # Build the message for the frontend
                    content = {'symptoms_report': symptoms_report, 'alarm': alarm}

                    # Send message to frontend
                    at_to_hub.put({'type': 'symptoms_report', 'content': content})

        time.sleep(0.5)

    # Clear the queues and print a stop message
    at_to_hub.queue.clear()
    hub_to_at.queue.clear()
    print('Anomaly treatment thread stopped.')
    return
