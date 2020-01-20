import time
from statsmodels.tsa import ar_model

from AT.simulator_thread.scenario_tools import anomalies


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
    results = model.fit(trend='nc')
    prediction = results.predict(start=start_index, end=end_index)

    # Anomaly check
    second = 1
    message = ''
    for value in prediction:
        zone = compute_zone(value, info)
        if zone != base_zone:
            if zone == -2:
                message = 'LCT in ' + str(second) + 's'
            elif zone == -1:
                message = 'LWT in ' + str(second) + 's'
            elif zone == 0:
                message = 'nominal in ' + str(second) + 's'
            elif zone == 1:
                message = 'HWT in ' + str(second) + 's'
            elif zone == 2:
                message = 'HCT in ' + str(second) + 's'
            else:
                print('Invalid zone value')
                raise
            break

        second += 1
    return message


def build_anomaly_report(window):
    """
    This function checks the status of the trace and builds the proper warning messages if necessary.
    """

    # Input parse
    values = window['values']
    # values = values.drop(labels='timestamp', axis='columns')
    info = window['info']

    # Iteration over each telemetry feed variable's trace to search anomalies and build the proper message
    detection_list = {}
    for item in values:
        # Retrieve trace as an array
        trace = list(values[item])

        # Check and build the threshold and forecast messages
        threshold_message = threshold_check(trace[-1], info[item])
        forecast_message = forecast_check(trace, info[item])
        detection_list[item] = {'threshold': '', 'forecast': ''}
        if threshold_message != '':
            detection_list[item]['threshold'] = threshold_message
        if forecast_message != '':
            detection_list[item]['forecast'] = forecast_message

    return detection_list


def build_diagnosis_report(detection_list):
    diagnosis_list = []
    for item in anomalies:
        anomaly = anomalies[item]
        is_happening = True
        for variable in anomaly:
            if variable not in detection_list:
                is_happening = False
            else:
                sign = anomaly[variable]['max_increment'] / abs(anomaly[variable]['max_increment'])
                threshold = detection_list[variable]['threshold']
                if sign == 1 and (threshold != 'HWT' and threshold != 'HCT'):
                    is_happening = False
                elif sign == -1 and (threshold != 'LWT' and threshold != 'LCT'):
                    is_happening = False

        if is_happening:
            diagnosis_list.append(item)
    return diagnosis_list


def build_recommendation_report(diagnosis_list):
    recommendation_list = []
    for item in diagnosis_list:
        if item == 'n2_tank_burst':
            procedure = '15'
            recommendation_list.append(procedure)
    return recommendation_list


def parse_detection_report(detection_report):
    detection_messages = []
    for item in detection_report:
        threshold = detection_report[item]['threshold']
        forecast = detection_report[item]['forecast']
        if (threshold != '' and threshold != 'nominal') and forecast == '':
            message = item + ': is ' + threshold + '.'
            detection_messages.append(message)
        elif (threshold == '' and threshold == 'nominal') and forecast != '':
            message = item + ': to ' + forecast + '.'
            detection_messages.append(message)
        elif (threshold != '' and threshold != 'nominal') and forecast != '':
            message = item + ': is ' + threshold + ', to ' + forecast + '.'
            detection_messages.append(message)
    return detection_messages


def parse_diagnosis_report(diagnosis_report):
    diagnosis_messages = []
    for item in diagnosis_report:
        anomaly_name = item.replace('_', ' ')
        message = 'Might be a ' + anomaly_name + '.'
        diagnosis_messages.append(message)
    return diagnosis_messages


def parse_recommendation_report(recommendation_report):
    recommendation_messages = []
    for item in recommendation_report:
        message = 'Request procedure ' + item + ' to Daphne.'
        recommendation_messages.append(message)
    return recommendation_messages


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
                    detection_report = build_anomaly_report(window)
                    detection_list = parse_detection_report(detection_report)

                    # Trigger diagnosis here
                    diagnosis_report = build_diagnosis_report(detection_report)
                    diagnosis_list = parse_diagnosis_report(diagnosis_report)

                    # Trigger recommendation here
                    recommendation_report = build_recommendation_report(diagnosis_report)
                    recommendation_list = parse_recommendation_report(recommendation_report)

                    # Send message to frontend
                    report = {'detection': detection_list,
                              'diagnosis': diagnosis_list,
                              'recommendation': recommendation_list}
                    at_to_hub.put({'type': 'automated_at_report', 'content': report})

        time.sleep(0.5)

    print('Anomaly treatment thread stopped.')
    return
