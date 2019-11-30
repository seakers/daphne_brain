from rest_framework.views import APIView
from rest_framework.response import Response
import threading
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information

from queue import Queue
from AT.simulator_thread.simulator_routine import simulate
from AT.hub_thread.hub_routine import hub_routine
from AT.ad_thread.ad_routine import anomaly_detection_routine

# QUEUES
from AT.queue_objects import frontend_to_hub_queue
from AT.queue_objects import simulator_to_hub_queue
from AT.queue_objects import hub_to_simulator_queue
from AT.queue_objects import hub_to_ad_queue
from AT.queue_objects import ad_to_diagnosis_queue
from AT.queue_objects import diagnosis_to_hub_queue


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
                                            hub_to_ad_queue,
                                            diagnosis_to_hub_queue,
                                            channel_layer,
                                            channel_name,))
        hub_thread.start()

        # Simulator thread initialization
        simulator_thread = threading.Thread(target=simulate,
                                            args=(simulator_to_hub_queue,
                                                  hub_to_simulator_queue))
        simulator_thread.start()

        # Anomaly detection thread initialization
        ad_thread = threading.Thread(target=anomaly_detection_routine,
                                     args=(hub_to_ad_queue,
                                           ad_to_diagnosis_queue,
                                           channel_layer,
                                           channel_name,))
        ad_thread.start()

        # Tread status check
        if hub_thread.is_alive() and simulator_thread.is_alive() and ad_thread.is_alive():
            print('**********\nAll AT threads started successfully.\n**********')
        else:
            print('**********')
            if not hub_thread.is_alive():
                print('Thread handler thread start failure.')
            if not simulator_thread.is_alive():
                print('Simulator thread start failure.')
            if not ad_thread.is_alive():
                print('Anomaly detection thread start failure.')
            print('**********')


        return Response()


class StopTelemetry(APIView):
    def post(self, request):
        frontend_to_hub_queue.put('stop')

        return Response()