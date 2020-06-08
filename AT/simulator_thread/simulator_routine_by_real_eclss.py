import time
import pandas as pd


def get_param_values(sensor_data):
    new_row = {}
    tf_info_dict = {'parameter': ['display_name',
                                  'kg_name',
                                  'group',
                                  'units',
                                  'low_critic_threshold',
                                  'low_warning_threshold',
                                  'nominal',
                                  'high_warning_threshold',
                                  'high_critic_threshold', ]}

    for item in sensor_data:
        name = item['Name']
        nominal = item['NominalValue']
        simulated_value = item['SimValue']
        units = item['Unit']
        group = item['ParameterGroup']
        lct = item['LowerCriticalLimit']
        lwt = item['LowerWarningLimit']
        hwt = item['UpperWarningLimit']
        hct = item['UpperCriticalLimit']

        display_name = name + ' (' + group + ')'
        kg_name = name

        tf_info_dict[display_name] = [display_name, kg_name, group, units, lct, lwt, nominal, hwt, hct]
        new_row[display_name] = simulated_value

    tf_info = pd.DataFrame(tf_info_dict)
    tf_info = tf_info.set_index('parameter')
    parsed_sensor_data = {'new_values': new_row, 'info': tf_info}
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


def handle_eclss_update(sim_to_hub, hub_to_sim, ser_to_sim):

    tf_window = {'values': '', 'info': ''}
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
        if not hub_to_sim.empty():
            signal = hub_to_sim.get()
            if signal['type'] == 'stop':
                keep_alive = False
            elif signal['type'] == 'ping':
                time_since_last_ping = time.time() - current_time
                current_time = time.time()
            elif signal['type'] == 'get_telemetry_params':
                if tf_window['info'] == '':
                    hub_to_sim.put(signal)
                else:
                    sim_to_hub.put({'type': 'initialize_telemetry', 'content': tf_window})

        while not ser_to_sim.empty():
            signal = ser_to_sim.get()
            if signal['type'] == 'sensor_data':
                sensor_data = signal['content']
                parsed_sensor_data = get_param_values(sensor_data)

                if first_update:
                    tf_window = generate_initial_window(parsed_sensor_data)
                    first_update = False
                else:
                    tf_window = update_window(parsed_sensor_data, tf_window, counter - 1)

                sim_to_hub.put({'type': 'window', 'content': tf_window})
                counter += 1
                if counter % print_freq == 0:
                    print('The ECLSS sensor data handler is healthy.')

        time.sleep(check_delay)

    # Clear the queues and print a stop message
    sim_to_hub.queue.clear()
    hub_to_sim.queue.clear()
    ser_to_sim.queue.clear()
    print('Simulator thread stopped.')
    return
