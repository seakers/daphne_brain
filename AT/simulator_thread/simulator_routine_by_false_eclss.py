import time
import numpy as np
import pandas as pd
import json
import os


def add_noise(variable, variables, std_fact, digits):
    std = variables[variable]['nominal'] * std_fact
    noise = round(np.random.normal(0, std), digits)
    return noise


def generate_initial_window(status, variables, window_span, std_fact, digits):
    # Initialize the telemetry feed values dictionary
    tf_values_dict = {}

    # Create the initial timestamp entry ('timestamp': [00:00:00, 00:00:01, ...]])
    timestamp = []
    for second in range(window_span):
        timestamp.append(time.strftime('%H:%M:%S', time.gmtime(second)))
    # tf_values_dict['timestamp'] = timestamp

    # Create the initial variables value
    for key in status:
        values = []
        for second in range(window_span):
            values.append(variables[key]['nominal'] + add_noise(key, variables, std_fact, digits))
        tf_values_dict[key] = values

    # Parse the variables information into a dictionary
    tf_info_dict = {'parameter': ['display_name',
                                  'kg_name',
                                  'group',
                                  'units',
                                  'low_warning_threshold',
                                  'low_caution_threshold',
                                  'nominal',
                                  'high_caution_threshold',
                                  'high_warning_threshold', ]}
    for key in variables:
        variable_info = variables[key]
        tf_info_dict[key] = [variable_info['display_name'],
                             variable_info['kg_name'],
                             variable_info['group'],
                             variable_info['units'],
                             variable_info['low_warning_threshold'],
                             variable_info['low_caution_threshold'],
                             variable_info['nominal'],
                             variable_info['high_caution_threshold'],
                             variable_info['high_warning_threshold'], ]

    # Convert both dictionaries to dataframes
    tf_values = pd.DataFrame(tf_values_dict)
    tf_info = pd.DataFrame(tf_info_dict)
    tf_info = tf_info.set_index('parameter')
    tf_window = {'values': tf_values, 'info': tf_info}

    return tf_window


def update_window(tf_window, status, variables, t, lower_row, upper_row, std_fact, digits):
    # Compute new timestamp and generate new row
    new_timestamp = time.strftime('%H:%M:%S', time.gmtime(t + 1))
    tf_columns = list(tf_window['values'].columns.values)
    new_row = []
    for key in tf_columns:
        if key == 'timestamp':
            new_row.append(new_timestamp)
        else:
            # Add noise before sending
            new_row.append(status[key] + add_noise(key, variables, std_fact, digits))

    # Update and send telemetry feed window
    tf_window['values'] = tf_window['values'].drop(index=lower_row - 1)
    tf_window['values'].loc[upper_row] = new_row

    return tf_window


def calculate_contribution(event, variable, parameters, t_now, delta, initial_delay):
    # ******************************
    # A)     __________                   B)     /\
    #       /          \                        /  \
    # _____/            \_____     OR     _____/    \_____
    #    t1  t2      t3  t4                  t1  t3  t4
    # notice that t1 = start and duration = t3 - t1 in both cases
    # ******************************

    # Initialize and parse
    contribution = 0
    start = event['start'] + initial_delay
    duration = event['duration']
    t1 = start
    t3 = start + duration

    # Compute the time that the variable would require to reach the maximum increment
    dt_max = abs(parameters['max_increment'] / parameters['pace_in'])

    # Scenario A can happen in two situations:
    #   - The variable can reach its maximum allowed increment before the anomaly fades out.
    #   - The
    if dt_max < duration:
        t_out = abs(parameters['max_increment'] / parameters['pace_out'])
        t2 = start + dt_max
        t4 = t3 + t_out
        if t1 < t_now <= t2:
            delta = t_now - t1
            contribution = delta * parameters['pace_in']
        elif t2 < t_now <= t3:
            contribution = parameters['max_increment']
        elif t3 < t_now <= t4:
            delta = t_now - t3
            contribution = parameters['max_increment'] + delta * parameters['pace_out']
    else:
        delta_out = abs(duration * parameters['pace_in'] / parameters['pace_out'])
        t4 = t3 + delta_out
        if t1 < t_now <= t3:
            contribution = (t_now - t1) * parameters['pace_in']
        elif t3 < t_now < t4:
            contribution = (t3 - t1) * parameters['pace_in'] + (t_now - t3) * parameters['pace_out']

    return contribution


def generate_new_values(status, variables, anomalies, timeline, t_now, delta, initial_delay, digits):
    # Initialize contributions
    accumulated_contributions = {}
    for variable in status:
        accumulated_contributions[variable] = 0

    # Compute contributions
    for event in timeline:
        anomaly = anomalies[event['name']]
        for affected_variable in anomaly:
            parameters = anomaly[affected_variable]
            contribution = calculate_contribution(event, affected_variable, parameters, t_now, delta, initial_delay)
            accumulated_contributions[affected_variable] += contribution

    # Add contributions
    for key in status:
        status[key] = accumulated_contributions[key] + variables[key]['nominal']
        status[key] = round(status[key], digits)

    return status


def simulate_by_dummy_eclss(sim_to_hub, hub_to_sim):
    # Set the simulation
    variables_json_filename = os.path.join(os.getcwd(), 'AT', 'simulator_thread', 'simulator_variables.json')
    anomalies_json_filename = os.path.join(os.getcwd(), 'AT', 'simulator_thread', 'simulator_anomalies.json')
    timeline_json_filename = os.path.join(os.getcwd(), 'AT', 'simulator_thread', 'simulator_timeline.json')

    variables_content = open(variables_json_filename, "r")
    anomalies_content = open(anomalies_json_filename, "r")
    timeline_content = open(timeline_json_filename, "r")

    variables = json.load(variables_content)
    anomalies = json.load(anomalies_content)
    timeline = json.load(timeline_content)

    window_span = 60
    dt = 0.1
    display_lapse = 1
    std_fact = 0.001
    digits = 5

    # Initialize the status variable (to the nominal value of all the simulation variables)
    status = {}
    for key in variables:
        status[key] = variables[key]['nominal']

    # Generate and send and initial (noised) window to the frontend
    tf_window = generate_initial_window(status, variables, window_span, std_fact, digits)
    sim_to_hub.put({'type': 'window', 'content': tf_window})
    time_last_display = time.time()

    # Initialize the simulation loop counters
    keep_alive = True
    t = window_span - 1
    lower_row = 0
    upper_row = window_span - 1

    # Set the ping routine counters
    life_limit = 40.
    time_since_last_ping = 0.
    current_time = time.time()

    # Simulation loop
    while keep_alive and time_since_last_ping < life_limit:
        time_since_last_ping = time.time() - current_time
        # Check the communication queue messages
        if not hub_to_sim.empty():
            signal = hub_to_sim.get()
            if signal['type'] == 'stop':
                print("Fake killed by signal")
                keep_alive = False
            elif signal['type'] == 'ping':
                current_time = time.time()
            elif signal['type'] == 'get_fake_telemetry_params':
                sim_to_hub.put({'type': 'initialize_telemetry', 'content': tf_window})

        # Update the time counter
        t = round(t + dt, 5)

        # Update status
        status = generate_new_values(status, variables, anomalies, timeline, t, dt, window_span, digits)

        # Send a new telemetry feed window to the hub thread periodically
        elapsed_time_since_last_display = time.time() - time_last_display
        if elapsed_time_since_last_display >= display_lapse:
            # Update telemetry feed window and send it to the hub thread
            tf_window = update_window(tf_window, status, variables, t, lower_row + 1, upper_row + 1, std_fact, digits)
            sim_to_hub.put({'type': 'window', 'content': tf_window})

            # Update row and time counters
            lower_row += 1
            upper_row += 1
            time_last_display = time.time()

        # Wait
        time.sleep(dt)

    # Clear the queues and print a stop message
    sim_to_hub.queue.clear()
    hub_to_sim.queue.clear()
    print('Simulator thread stopped.')
    return
