import time

from asgiref.sync import async_to_sync


def hub_routine(front_to_hub, sim_to_hub, hub_to_sim, hub_to_at, at_to_hub, channel_layer, channel_name):
    # Set the "checking frequency"
    check_delay = 0.1

    # Set the ping routine counters
    life_limit = 40
    time_since_last_ping = 0

    # Wait for the first simulator output in order to send an initialization command to the frontend
    first_status_has_arrived = False
    first_status_is_timeout = False
    first_status_timer = 0
    first_status_time_limit = 10
    while not first_status_has_arrived and not first_status_is_timeout:
        if not sim_to_hub.empty():
            # Parse the simulator message
            signal = sim_to_hub.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['info'].columns.values)
                content = {'variables_names': tf_variables,
                           'values': tf_window['values'].to_json(),
                           'info': tf_window['info'].to_json()}
                command = {'type': 'initialize_telemetry',
                           'content': content}
                async_to_sync(channel_layer.send)(channel_name, command)

                # Put the first simulator output back in the queue and update the while loop condition
                sim_to_hub.put(signal)
                first_status_has_arrived = True
        else:
            # Update counters and wait
            first_status_timer += check_delay
            time.sleep(check_delay)

            # Print loop info
            s1 = str(round(first_status_timer, 1))
            s2 = str(round(first_status_time_limit, 1))
            waiting_message = 'Waiting to receive first status (' + s1 + ' seconds passed out of ' + s2 + ')'
            print(waiting_message)

            # Check break condition
            if first_status_timer > first_status_time_limit:
                first_status_is_timeout = True
                time_since_last_ping = life_limit + 1
                print('First status not received. Aborting AT routine.')

    # Initialize the ping routine timer
    timer_start = time.time()

    # Start the hub routine
    while time_since_last_ping < life_limit:
        # Check the frontend input queue
        if not front_to_hub.empty():
            signal = front_to_hub.get()
            print('New message from the frontend: ' + signal)
            if signal == 'stop':
                break
            elif signal == 'ping':
                time_since_last_ping = 0
                timer_start = time.time()

        # Check the simulator input queue
        if not sim_to_hub.empty():
            signal = sim_to_hub.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Send the telemetry feed window to the anomaly detection queue
                last_window = {'type': 'window', 'content': tf_window}
                hub_to_at.put(last_window)

                # Update and send the telemetry update command for the frontend
                content = {'values': tf_window['values'].to_json(),
                           'info': tf_window['info'].to_json()}
                command = {'type': 'telemetry_update',
                           'content': content}
                async_to_sync(channel_layer.send)(channel_name, command)

        # Check the anomaly treatment output queue
        if not at_to_hub.empty():
            signal = at_to_hub.get()
            if signal['type'] == 'symptoms_report':
                async_to_sync(channel_layer.send)(channel_name, signal)

        # Update while loop condition and wait
        time_since_last_ping = time.time() - timer_start
        time.sleep(check_delay)

    hub_to_sim.put({'type': 'stop', 'content': ''})
    hub_to_at.put({'type': 'stop', 'content': ''})

    print('Hub thread stopped.')
    return
