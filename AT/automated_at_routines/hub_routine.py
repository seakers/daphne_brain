import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from auth_API.helpers import get_or_create_user_information


def update_channel_layer_and_name(signal):
    # Update the user information and channel layer
    user_info = signal['content']
    channel_layer = get_channel_layer()
    channel_name = user_info.channel_name

    return channel_layer, channel_name


def hub_routine(front_to_hub, sim_to_hub, hub_to_sim, hub_to_at, at_to_hub, request):
    # Get the user information and channel layer
    user_info = get_or_create_user_information(request.session, request.user, 'AT')
    channel_layer = get_channel_layer()
    channel_name = user_info.channel_name

    # Set the "checking frequency"
    check_delay = 0.1

    # Set the ping routine counters
    life_limit = 40
    time_since_last_ping = 0

    # Initialize the ping routine timer
    timer_start = time.time()

    # Start the hub routine
    while time_since_last_ping < life_limit:
        # Check the frontend input queue
        if not front_to_hub.empty():
            signal = front_to_hub.get()
            print('New message from the frontend: ' + signal['type'])
            if signal['type'] == 'stop_telemetry':
                hub_to_sim.put({"type": "stop", "content": None})
            elif signal['type'] == 'ping':
                timer_start = time.time()
                hub_to_sim.put({"type": "ping", "content": None})
                hub_to_at.put({"type": "ping", "content": None})
            elif signal['type'] == 'get_telemetry_params':
                hub_to_sim.put({"type": "get_telemetry_params", "content": None})
            elif signal['type'] == 'ws_configuration_update':
                # Update the user information and channel layer
                channel_layer, channel_name = update_channel_layer_and_name(signal)

                # Reset the ping timeout
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

                # Try to convert the dataframes to json format (this fails from time to time with no explanation)
                json_values = ''
                json_info = ''
                try:
                    json_values = tf_window['values'].to_json()
                    json_info = tf_window['info'].to_json()
                except:
                    print('Dataframe conversion failed')

                # If the conversion was successful, update and send the telemetry update command for the frontend
                if json_values != '' and json_info != '':
                    content = {'values': json_values,
                               'info': json_info}
                    command = {'type': 'telemetry_update',
                               'content': content}
                    async_to_sync(channel_layer.send)(channel_name, command)
            elif signal['type'] == 'initialize_telemetry':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['info'].columns.values)
                content = {'variables_names': tf_variables}
                command = {'type': 'initialize_telemetry',
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

    # Clear the queues and print a stop message
    front_to_hub.queue.clear()
    print('Hub thread stopped.')
    return
