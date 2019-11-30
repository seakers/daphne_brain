import pandas as pd
from asgiref.sync import async_to_sync
import os
from queue import Queue
import time


def hub_routine(front_to_hub, sim_to_hub, hub_to_sim, hub_to_ad, diag_to_hub, channel, channel_name):
    print('Thread handler thread started.')

    # Wait for the first simulator output in order to send an initialization command to the frontend
    first_status_has_arrived = False
    while not first_status_has_arrived:
        if not sim_to_hub.empty():
            tf_window = sim_to_hub.get()

            # Parse the signal, retrieve the telemetry feed variables and send an initialization command to the frontend
            tf_variables = list(tf_window['values'].columns.values)
            tf_variables.remove('timestamp')
            command = {'type': 'initialize_telemetry', 'variables': tf_variables}
            async_to_sync(channel.send)(channel_name, command)

            # Put the first simulator output back in the queue and update the while loop condition
            sim_to_hub.put(tf_window)
            first_status_has_arrived = True
        else:
            time.sleep(0.01)

    # Initialize
    time_since_last_ping = 0
    timer_start = time.time()
    life_limit = 40

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

            # Send the telemetry feed window to the anomaly detection queue
            last_window = {'type': 'window', 'content': signal}
            hub_to_ad.put(last_window)

            # Update and send the telemetry update command for the frontend
            command = {'type': 'telemetry_update',
                       'values': tf_window['values'].to_json(),
                       'info': tf_window['info'].to_json()}
            async_to_sync(channel.send)(channel_name, command)

        # Check the diagnosis output queue
        if not diag_to_hub.empty():
            signal = diag_to_hub.get()

        # Update while loop condition and wait
        time_since_last_ping = time.time() - timer_start
        time.sleep(0.1)

    hub_to_sim.put('stop')
    hub_to_ad.put({'type': 'stop', 'content': ''})

    print('Thread handler thread stopped.')
    return None