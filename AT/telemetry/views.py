from rest_framework.views import APIView
from rest_framework.response import Response
import threading
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from auth_API.helpers import get_or_create_user_information
import pandas as pd
import os


class SimulateTelemetry(APIView):
    def post(self, request):

        def read_and_update():
            # Load the complete (false) telemetry feed
            filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed.csv')
            tf_data = pd.read_csv(filename)

            # Load the (false) telemetry feed variables thresholds
            filename = os.path.join(os.getcwd(), 'AT', 'Databases', 'telemetry_feed_thresholds.csv')
            tf_thresholds = pd.read_csv(filename)

            # Get the channel layer for the websocket communication
            thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
            channel_layer = get_channel_layer()

            # Initialize the telemetry feed real time record and window
            k = 1
            initial_span = 60
            lower_row = 0
            upper_row = initial_span - 1
            # tf_record = tf_data.iloc[lower_row:upper_row]
            tf_window = tf_data.iloc[lower_row:upper_row]

            # Simulate the real time feeding
            time_limit = len(tf_data.index) - initial_span
            while k < time_limit:
                # Build and send the plot update command for the frontend
                command = {}
                command['type'] = 'telemetry_update'
                command['dataframe'] = tf_window.to_json()
                async_to_sync(channel_layer.send)(thread_user_info.channel_name, command)

                # Update telemetry feed record and window
                new_info = tf_data.iloc[upper_row + 1]
                tf_window.drop(index=lower_row, inplace=True)
                tf_window.loc[upper_row + 1] = new_info
                # tf_record.loc[upper_row + 1] = new_info

                # Update counters and wait (to be improved)
                k += 1
                lower_row += 1
                upper_row += 1
                time.sleep(1)

            return None

        thread = threading.Thread(target=read_and_update)
        thread.start()
        return Response()
