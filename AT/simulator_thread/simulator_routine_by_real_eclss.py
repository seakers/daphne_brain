import json
import time
import pandas as pd
from AT.global_objects import server_to_sEclss_queue, server_to_hera_queue

SENSOR_DATA = None
def set_sensor_data(sensor_data):
    global SENSOR_DATA
    SENSOR_DATA = json.dumps(sensor_data)
def get_sensor_data():
    return SENSOR_DATA
def get_param_values(sensor_data):
    status = {}
    new_row = {}
    tf_info_dict = {'parameter': ['display_name',
                                  'kg_name',
                                  'group',
                                  'units',
                                  'low_warning_threshold',
                                  'low_caution_threshold',
                                  'nominal',
                                  'high_caution_threshold',
                                  'high_warning_threshold',]}

    for item in sensor_data:
        name = item['Name']
        nominal = item['NominalValue']
        simulated_value = item['SimValue']
        units = item['Unit']
        group = item['ParameterGroup']
        lct = item['LowerWarningLimit']
        lwt = item['LowerCautionLimit']
        hwt = item['UpperCautionLimit']
        hct = item['UpperWarningLimit']
        stat=[key for key, value in item['Status'].items() if value]
        display_name = name + ' (' + group + ')'
        kg_name = name

        tf_info_dict[display_name] = [display_name, kg_name, group, units, lct, lwt, nominal, hwt, hct]
        new_row[display_name] = simulated_value
        status[display_name] = stat
    tf_info = pd.DataFrame(tf_info_dict)
    tf_info = tf_info.set_index('parameter')
    parsed_sensor_data = {'new_values': new_row, 'info': tf_info, 'status': status}
    return parsed_sensor_data

def get_hss_param_values(sensor_data):
    status ={}
    new_row = {}
    tf_info_dict = {'parameter': ['display_name',
                                  'kg_name',
                                  'group',
                                  'units',
                                  'low_warning_threshold',
                                  'low_caution_threshold',
                                  'nominal',
                                  'high_caution_threshold',
                                  'high_warning_threshold',]}

    for item in sensor_data:
        name = item['Name']
        nominal = item['NominalValue']
        simulated_value = item['SimValue']
        units = item['Unit']
        group = item['ParameterGroup']
        lct = item['LowerWarningLimit']
        lwt = item['LowerCautionLimit']
        hwt = item['UpperCautionLimit']
        hct = item['UpperWarningLimit']
        stat = [key for key, value in item['Status'].items() if value]
        display_name = name + ' (' + group + ')'
        kg_name = name

        tf_info_dict[display_name] = [display_name, kg_name, group, units, lct, lwt, nominal, hwt, hct]
        new_row[display_name] = simulated_value
        status[display_name] = stat
    set_sensor_data({'new_values': new_row, 'status': status})
    tf_info = pd.DataFrame(tf_info_dict)
    tf_info = tf_info.set_index('parameter')
    parsed_sensor_data = {'new_values': new_row, 'info': tf_info, 'status': status}
    # print(parsed_sensor_data)
    return parsed_sensor_data


def generate_initial_window(sensor_data):
    tf_window = {'values': '', 'info': sensor_data['info']}
    tf_values_dict = {}

    for item in sensor_data['new_values']:
        values = []
        for count in range(60):
            values.append(sensor_data['new_values'][item])
        tf_values_dict[item] = values

    tf_values = pd.DataFrame(tf_values_dict)
    tf_window['values'] = tf_values

    return tf_window


def update_window(sensor_data, tf_window, counter):
    new_values_dict = sensor_data['new_values']
    new_row = []
    for item in new_values_dict:
        value = new_values_dict[item]
        new_row.append(value)

    # Update and send telemetry feed window
    tf_window['values'] = tf_window['values'].drop(index=counter)
    tf_window['values'].loc[counter + 60] = new_row
    tf_window['info'] = sensor_data['info']

    return tf_window


def handle_eclss_update(sEclss_to_hub, hub_to_sEclss, ser_to_sEclss):
    tf_window = {'values': None, 'info': None}
    keep_alive = True
    first_update = True
    counter = 0
    check_delay = 0.1
    print_freq = 10  # This is only to occasionally print a health check message through the terminal

    # Set the ping routine counters
    life_limit = 40.
    time_since_last_ping = 0.
    current_time = time.time()

    while keep_alive and time_since_last_ping < life_limit:
        time_since_last_ping = time.time() - current_time
        if not hub_to_sEclss.empty():
            signal = hub_to_sEclss.get()
            if signal['type'] == 'stop':
                print("Real killed by signal")
                keep_alive = False
            elif signal['type'] == 'ping':
                current_time = time.time()
            elif signal['type'] == 'get_real_telemetry_params':
                if tf_window['info'] is None:
                    hub_to_sEclss.put(signal)
                else:
                    sEclss_to_hub.put({'type': 'initialize_telemetry', 'content': tf_window})

        while not ser_to_sEclss.empty():
            signal = ser_to_sEclss.get()
            if signal['type'] == 'sensor_data':
                sensor_data = signal['content']
                parsed_sensor_data = get_hss_param_values(sensor_data)
                # print(sensor_data)
                if first_update:
                    print("Initialized tf window.")
                    tf_window = generate_initial_window(parsed_sensor_data)
                    first_update = False
                else:
                    tf_window = update_window(parsed_sensor_data, tf_window, counter - 1)

                sEclss_to_hub.put({'type': 'window', 'content': tf_window})
                counter += 1
                if counter % print_freq == 0:
                    print('The ECLSS sensor data handler is healthy.')

        time.sleep(check_delay)

    # Clear the queues and print a stop message
    sEclss_to_hub.queue.clear()
    hub_to_sEclss.queue.clear()
    ser_to_sEclss.queue.clear()
    print('Simulator thread stopped.')
    return
