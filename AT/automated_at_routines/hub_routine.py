import time

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from auth_API.helpers import get_or_create_user_information


def update_channel_layer_and_name(signal):
    # Update the user information and channel layer
    user_info = signal['content']
    channel_layer = get_channel_layer()
    channel_name = user_info.channel_name

    return channel_layer, channel_name


def hub_routine(front_to_hub, sEclss_to_hub, sim_to_hub_one, sim_to_hub_two, sim_to_hub_three, sim_to_hub_four,
                hub_to_sEclss, hub_to_sim_one, hub_to_sim_two, hub_to_sim_three, hub_to_sim_four, hub_to_sEclss_at,
                hub_to_sim_at_one, hub_to_sim_at_two, hub_to_sim_at_three, hub_to_sim_at_four,sEclss_at_to_hub,
                sim_at_to_hub_one, sim_at_to_hub_two, sim_at_to_hub_three, sim_at_to_hub_four, request):
    # Get the user information and channel layer
    # user_info = get_or_create_user_information(request.session, request.user, 'AT')
    # channel_layer = get_channel_layer()
    # channel_name = user_info.channel_name

    # Set the "checking frequency"
    check_delay = 0.1

    # Set the ping routine counters
    life_limit = 40
    time_since_last_ping = 0

    # Initialize the ping routine timer
    timer_start = time.time()

    # Real telemetry group
    sEclss_group_name = "sEclss_group"
    channel_layer_real = []

    # Fake telemetry users
    channel_layer_fake_one = None
    channel_layer_fake_two = None
    channel_layer_fake_three = None
    channel_layer_fake_four = None
    channel_name_fake_one = None
    channel_name_fake_two = None
    channel_name_fake_three = None
    channel_name_fake_four = None

    # Start the hub routine
    while time_since_last_ping < life_limit:
        # Check the frontend input queue
        if not front_to_hub.empty():
            signal = front_to_hub.get()
            print('New message from the frontend: ' + signal['type'])
            if signal['type'] == 'add_fake_telemetry_one':
                channel_layer_fake_one = signal['channel_layer']
                channel_name_fake_one = signal['channel_name']
            elif signal['type'] == 'add_fake_telemetry_two':
                channel_layer_fake_two = signal['channel_layer']
                channel_name_fake_two = signal['channel_name']

            elif signal['type'] == 'get_fake_telemetry_params':
                if signal['channel_name'] == channel_name_fake_one:
                    hub_to_sim_one.put({"type": "get_fake_telemetry_params", "content": None})
                    print(f"Channel {channel_name_fake_one} got fake telemetry params")
                elif signal['channel_name'] == channel_name_fake_two:
                    hub_to_sim_two.put({"type": "get_fake_telemetry_params", "content": None})
                    print(f"Channel {channel_name_fake_one} got fake telemetry params")
                else:
                    print(f"{signal['channel_name']} was did not get fake telemetry params")

            elif signal['type'] == 'stop_fake_telemetry_one':
                hub_to_sim_one.put({"type": "stop", "content": None})
                hub_to_sim_at_one.put({"type": "stop", "content": None})
                channel_layer_fake_one = None
                channel_name_fake_one = None
            elif signal['type'] == 'stop_fake_telemetry_two':
                hub_to_sim_two.put({"type": "stop", "content": None})
                hub_to_sim_at_two.put({"type": "stop", "content": None})
                channel_layer_fake_two = None
                channel_name_fake_two = None

            elif signal['type'] == 'add_to_sEclss_group':
                r = redis.Redis()
                channel_layer_real.append(signal['channel_layer'])
                channel_name = signal['channel_name']
                if r.sismember("seclss-group-users", channel_name) == 0:
                    async_to_sync(channel_layer_real[0].group_add)(sEclss_group_name, channel_name)
                    r.sadd("seclss-group-users", channel_name)
                    print(f"Channel {channel_name} added to group")

            elif signal['type'] == 'get_real_telemetry_params':
                hub_to_sEclss.put({"type": "get_real_telemetry_params", "content": None})

            elif signal['type'] == 'remove_channel_layer_from_real':
                channel_layer_to_remove = signal['channel_layer']
                channel_layer_real.remove(channel_layer_to_remove)

            elif signal['type'] == 'stop_real_telemetry':
                hub_to_sEclss.put({"type": "stop", "content": None})
                hub_to_sEclss_at.put({"type": "stop", "content": None})

            elif signal['type'] == 'ping':
                timer_start = time.time()
                hub_to_sEclss.put({"type": "ping", "content": None})
                hub_to_sim_one.put({"type": "ping", "content": None})
                hub_to_sim_two.put({"type": "ping", "content": None})
                hub_to_sEclss_at.put({"type": "ping", "content": None})
                hub_to_sim_at_one.put({"type": "ping", "content": None})
                hub_to_sim_at_two.put({"type": "ping", "content": None})

            elif signal['type'] == 'ws_configuration_update':
                # Reset the ping timeout
                timer_start = time.time()



        # Check sEclss input queue
        if not sEclss_to_hub.empty():
            signal = sEclss_to_hub.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Send the telemetry feed window to the anomaly detection queue
                last_window = {'type': 'window', 'content': tf_window}
                hub_to_sEclss_at.put(last_window)

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
                    async_to_sync(channel_layer_real[0].group_send)(sEclss_group_name, command)
            elif signal['type'] == 'initialize_telemetry':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['info'].columns.values)
                content = {'variables_names': tf_variables}
                command = {'type': 'initialize_telemetry',
                           'content': content}
                async_to_sync(channel_layer_real[0].group_send)("sEclss_group", command)

        # Check the simulator input queues
        if not sim_to_hub_one.empty():
            signal = sim_to_hub_one.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Send the telemetry feed window to the anomaly detection queue
                last_window = {'type': 'window', 'content': tf_window}
                hub_to_sim_at_one.put(last_window)

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
                    if channel_layer_fake_one is not None:
                        async_to_sync(channel_layer_fake_one.send)(channel_name_fake_one, command)
            elif signal['type'] == 'initialize_telemetry':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['info'].columns.values)
                content = {'variables_names': tf_variables}
                command = {'type': 'initialize_telemetry',
                           'content': content}
                if channel_layer_fake_one is not None:
                    async_to_sync(channel_layer_fake_one.send)(channel_name_fake_one, command)

        if not sim_to_hub_two.empty():
            signal = sim_to_hub_two.get()
            if signal['type'] == 'window':
                # Parse the signal
                tf_window = signal['content']

                # Send the telemetry feed window to the anomaly detection queue
                last_window = {'type': 'window', 'content': tf_window}
                hub_to_sim_at_two.put(last_window)

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
                    if channel_layer_fake_two is not None:
                        async_to_sync(channel_layer_fake_two.send)(channel_name_fake_two, command)
            elif signal['type'] == 'initialize_telemetry':
                # Parse the signal
                tf_window = signal['content']

                # Retrieve the telemetry feed variables and send an initialization command to the frontend
                tf_variables = list(tf_window['info'].columns.values)
                content = {'variables_names': tf_variables}
                command = {'type': 'initialize_telemetry',
                           'content': content}
                if channel_layer_fake_two is not None:
                    async_to_sync(channel_layer_fake_two.send)(channel_name_fake_two, command)

        # Check the anomaly treatment output queue for sEclss
        if not sEclss_at_to_hub.empty():
            signal = sEclss_at_to_hub.get()
            if signal['type'] == 'symptoms_report':
                async_to_sync(channel_layer_real[0].group_send)(sEclss_group_name, signal)

        # Check the anomaly treatment output queues for simulated telemetry
        if not sim_at_to_hub_one.empty():
            signal = sim_at_to_hub_one.get()
            if signal['type'] == 'symptoms_report':
                async_to_sync(channel_layer_fake_one.send)(channel_name_fake_one, signal)

        if not sim_at_to_hub_two.empty():
            signal = sim_at_to_hub_two.get()
            if signal['type'] == 'symptoms_report':
                async_to_sync(channel_layer_fake_two.send)(channel_name_fake_two, signal)

        # Update while loop condition and wait
        time_since_last_ping = time.time() - timer_start
        time.sleep(check_delay)

    hub_to_sEclss.put({'type': 'stop', 'content': ''})
    hub_to_sim_one.put({'type': 'stop', 'content': ''})
    hub_to_sim_two.put({'type': 'stop', 'content': ''})
    hub_to_sEclss_at.put({'type': 'stop', 'content': ''})
    hub_to_sim_at_one.put({'type': 'stop', 'content': ''})
    hub_to_sim_at_two.put({'type': 'stop', 'content': ''})

    # Clear the queues and print a stop message
    front_to_hub.queue.clear()
    print('Hub thread stopped.')
    return
