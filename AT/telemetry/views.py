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

        def read_and_update(smth):
            # Load the complete (false) telemetry feed csv files
            tf = {}
            filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_values.csv')
            tf['values'] = pd.read_csv(filename)
            filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_info.csv')
            tf['info'] = pd.read_csv(filename)
            tf_variables = list(tf['values'].columns.values)
            tf_variables.remove('timestamp')

            # Get the channel layer for the websocket communication
            thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
            channel_layer = get_channel_layer()

            # Send an initialization message for the frontend
            command = {}
            command['type'] = 'initialize_telemetry'
            command['variables'] = tf_variables
            async_to_sync(channel_layer.send)(thread_user_info.channel_name, command)

            # Send an itialization command to the frontend
            command = {}
            command['type'] = 'telemetry_update'
            command['values'] = ""
            command['info'] = tf['info'].to_json()

            # Initialize the telemetry feed real time window
            k = 1
            initial_span = 60
            time_limit = len(tf['values'].index) - initial_span
            lower_row = 0
            upper_row = initial_span - 1
            tf_window = {}
            tf_window['values'] = tf['values'].iloc[lower_row:(upper_row + 1)]
            tf_window['info'] = tf['info']

            # Simulate the real time feeding
            print('Telemetry simulation STARTED')
            while k < time_limit:
                # Testing
                if not smth.empty():
                    signal = smth.get()
                    print('In secondary thread: queue says ' + signal)

                # Update and send the plot update command for the frontend
                command['values'] = tf_window['values'].to_json()
                async_to_sync(channel_layer.send)(thread_user_info.channel_name, command)

                # Update counters
                k += 1
                lower_row += 1
                upper_row += 1

                # Update telemetry feed record and window
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

        # Create a thread communication queue
        thread_queue = Queue()
        thread_queue.put('hello')

        # Thread initialization
        thread = threading.Thread(target=read_and_update, args=(thread_queue,))
        thread.start()

        # time.sleep(5)
        # thread_queue.put('hello again')
        return Response()
