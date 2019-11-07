from rest_framework.views import APIView
from rest_framework.response import Response
import threading
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from auth_API.helpers import get_or_create_user_information
import pandas as pd
import os
from queue import Queue


class SimulateTelemetry(APIView):
    def post(self, request):

        def read_and_update(the_queue, the_channel, the_user_info):
            # Load the complete (false) telemetry feed csv files
            tf = {}
            tf['values'] = pd.read_csv(os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_values.csv'))
            tf['info'] = pd.read_csv(os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_info.csv'))
            tf_variables = list(tf['values'].columns.values)
            tf_variables.remove('timestamp')

            # Send an initialization message for the frontend
            command = {'type': 'initialize_telemetry', 'variables': tf_variables}
            print(the_user_info.channel_name)
            async_to_sync(the_channel.send)(the_user_info.channel_name, command)

            # Send an itialization command to the frontend
            command = {'type': 'telemetry_update', 'values': "", 'info': tf['info'].to_json()}

            # Initialize the telemetry feed real time window
            k = 1
            initial_span = 60
            time_limit = len(tf['values'].index) - initial_span
            lower_row = 0
            upper_row = initial_span - 1
            tf_window = {'values': tf['values'].iloc[lower_row:(upper_row + 1)], 'info': tf['info']}

            # Simulate the real time feeding
            print('Telemetry simulation STARTED')
            while k < time_limit:
                # Testing
                if not the_queue.empty():
                    signal = the_queue.get()
                    print('In secondary thread: queue says ' + signal)

                # Update and send the plot update command for the frontend
                command['values'] = tf_window['values'].to_json()
                async_to_sync(the_channel.send)(the_user_info.channel_name, command)

                # Update counters
                k += 1
                lower_row += 1
                upper_row += 1

                # Update telemetry feed window
                new_info = tf['values'].iloc[upper_row]
                tf_window['values'].drop(index=lower_row - 1, inplace=True)
                tf_window['values'].loc[upper_row] = new_info

                # Wait (to be improved)
                time.sleep(1)
                percent = round(100 * (k / time_limit), 1)
                msg = 'Telemetry simulation status: ' + str(percent) + '%'
                print(msg)

            print('Telemetry simulation ENDED')

            return None

        # Get the user information and channel layer
        thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_layer = get_channel_layer()

        # Create a communication queue (frontend <-> main thread <-> secondary thread)
        comm_queue = Queue()
        command = {'type': 'create_queue', 'queue': comm_queue}
        print('I GET HERE')
        print('Channel name: "' + thread_user_info.channel_name + '"')
        async_to_sync(channel_layer.send)(thread_user_info.channel_name, command)
        print('AND HERE TOO')

        # Thread initialization
        thread = threading.Thread(target=read_and_update, args=(comm_queue, channel_layer, thread_user_info,))
        thread.start()

        return Response()
