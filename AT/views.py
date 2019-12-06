from rest_framework.views import APIView
from rest_framework.response import Response
import threading
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information
from collections import OrderedDict
from AT.simulator_thread.simulator_routine_by_dummy_eclss import simulate_by_dummy_eclss
from AT.hub_thread.hub_routine import hub_routine
from AT.ad_thread.ad_routine import anomaly_detection_routine
from AT.diagnosis_thread.diagnosis_routine import diagnosis_routine

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
        simulator_thread = threading.Thread(target=simulate_by_dummy_eclss,
                                            args=(simulator_to_hub_queue,
                                                  hub_to_simulator_queue))
        simulator_thread.start()

        # Anomaly detection thread initialization
        ad_thread = threading.Thread(target=anomaly_detection_routine,
                                     args=(hub_to_ad_queue,
                                           ad_to_diagnosis_queue,))
        ad_thread.start()

        # Diagnosis thread initialization
        diagnosis_thread = threading.Thread(target=diagnosis_routine,
                                            args=(ad_to_diagnosis_queue,
                                                  diagnosis_to_hub_queue,))
        diagnosis_thread.start()

        # Thread status check
        sim_is_alive = hub_thread.is_alive()
        hub_is_alive = hub_thread.is_alive()
        ad_is_alive = ad_thread.is_alive()
        diag_is_alive = diagnosis_thread.is_alive()
        if hub_is_alive and sim_is_alive and ad_is_alive and diag_is_alive:
            print('**********\nAll AT threads started successfully.\n**********')
        else:
            print('**********')
            if not hub_thread.is_alive():
                print('Thread handler thread start failure.')
            if not simulator_thread.is_alive():
                print('Simulator thread start failure.')
            if not ad_thread.is_alive():
                print('Anomaly detection thread start failure.')
            if not diag_is_alive:
                print('Diagnosis thread start failure.')
            print('**********')
        return Response()


class StopTelemetry(APIView):
    def post(self, request):
        frontend_to_hub_queue.put('stop')
        return Response()

class SeclssFeed(APIView):

    def post(self, request):
        print(request.data)
        sensorData = OrderedDict(request.data)
        print(sensorData)
        return Response()
