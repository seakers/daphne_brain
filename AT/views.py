import json
import threading

from channels.layers import get_channel_layer
from rest_framework.response import Response
from rest_framework.views import APIView
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.automated_at_routines.hub_routine import hub_routine
from AT.global_objects import at_to_hub_queue

# QUEUES
from AT.global_objects import frontend_to_hub_queue
from AT.global_objects import hub_to_at_queue
from AT.global_objects import hub_to_simulator_queue
from AT.global_objects import simulator_to_hub_queue
from auth_API.helpers import get_or_create_user_information


class SimulateTelemetry(APIView):
    def post(self, request):
        # Get the user information and channel layer
        thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_layer = get_channel_layer()
        channel_name = thread_user_info.channel_name

        # Hub thread initialization
        hub_thread = threading.Thread(target=hub_routine,
                                      args=(frontend_to_hub_queue,
                                            simulator_to_hub_queue,
                                            hub_to_simulator_queue,
                                            hub_to_at_queue,
                                            at_to_hub_queue,
                                            channel_layer,
                                            channel_name,))
        hub_thread.start()

        # Simulator thread initialization
        simulator_thread = threading.Thread(target=simulate_by_dummy_eclss,
                                            args=(simulator_to_hub_queue,
                                                  hub_to_simulator_queue))
        simulator_thread.start()

        # Anomaly detection thread initialization
        at_thread = threading.Thread(target=anomaly_treatment_routine,
                                     args=(hub_to_at_queue,
                                           at_to_hub_queue,))
        at_thread.start()

        # Thread status check
        sim_is_alive = hub_thread.is_alive()
        hub_is_alive = hub_thread.is_alive()
        ad_is_alive = at_thread.is_alive()
        if hub_is_alive and sim_is_alive and ad_is_alive:
            print('**********\nAll AT threads started successfully.\n**********')
        else:
            print('**********')
            if not hub_thread.is_alive():
                print('Thread handler thread start failure.')
            if not simulator_thread.is_alive():
                print('Simulator thread start failure.')
            if not at_thread.is_alive():
                print('Anomaly treatment thread start failure.')
            print('**********')
        return Response()


class StopTelemetry(APIView):
    def post(self, request):
        frontend_to_hub_queue.put('stop')
        return Response()


class StartSeclssFeed(APIView):
    def post(self, request):
        # Get the user information and channel layer
        thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_layer = get_channel_layer()
        channel_name = thread_user_info.channel_name

        # Hub thread initialization
        hub_thread = threading.Thread(target=hub_routine,
                                      args=(frontend_to_hub_queue,
                                            simulator_to_hub_queue,
                                            hub_to_simulator_queue,
                                            hub_to_at_queue,
                                            at_to_hub_queue,
                                            channel_layer,
                                            channel_name,))
        hub_thread.start()

        # Anomaly detection thread initialization
        at_thread = threading.Thread(target=anomaly_treatment_routine,
                                     args=(hub_to_at_queue,
                                           at_to_hub_queue,))
        at_thread.start()

        # Thread status check
        hub_is_alive = hub_thread.is_alive()
        ad_is_alive = at_thread.is_alive()
        if hub_is_alive and ad_is_alive:
            print('**********\nAll AT threads started successfully.\n**********')
        else:
            print('**********')
            if not hub_thread.is_alive():
                print('Thread handler thread start failure.')
            if not at_thread.is_alive():
                print('Anomaly treatment thread start failure.')
            print('**********')
            return Response()

class SeclssFeed(APIView):
    def post(self, request, is_alive):
        sensor_data = request.data['parameters']
        print(sensor_data)
        parsed_sensor_data = json.loads(sensor_data)
        simulator_to_hub_queue.put({'type': 'window', 'content': tf_window})
        return Response(parsed_sensor_data)
