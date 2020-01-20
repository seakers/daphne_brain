import time

from asgiref.sync import async_to_sync


def hub_routine(front_to_hub, sim_to_hub, hub_to_sim, hub_to_at, at_to_hub, channel, channel_name):
    print('Thread handler thread started.')

    # Wait for the first simulator output in order to send an initialization command to the frontend
    first_status_has_arrived = False
    while not first_status_has_arrived:
        if not sim_to_hub.empty():
            # Parse the simulator message
            signal = sim_to_hub.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['values'].columns.values)
                # tf_variables.remove('timestamp')
                command = {'type': 'initialize_telemetry', 'variables': tf_variables}
                async_to_sync(channel.send)(channel_name, command)

                # Put the first simulator output back in the queue and update the while loop condition
                sim_to_hub.put(signal)
                first_status_has_arrived = True
        else:
            time.sleep(0.01)

    # Set and initialize the ping routine counters
    life_limit = 40
    time_since_last_ping = 0
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
                command = {'type': 'telemetry_update',
                           'values': tf_window['values'].to_json(),
                           'info': tf_window['info'].to_json()}
                async_to_sync(channel.send)(channel_name, command)

        # Check the anomaly treatment output queue
        if not at_to_hub.empty():
            signal = at_to_hub.get()
            if signal['type'] == 'automated_at_report':
                async_to_sync(channel.send)(channel_name, signal)

        # Update while loop condition and wait
        time_since_last_ping = time.time() - timer_start
        time.sleep(0.1)

    hub_to_sim.put({'type': 'stop', 'content': ''})
    hub_to_at.put({'type': 'stop', 'content': ''})

    print('Hub thread stopped.')
    return
