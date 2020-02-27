import json
import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.response import Response
from rest_framework.views import APIView
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.automated_at_routines.hub_routine import hub_routine
from AT.global_objects import at_to_hub_queue
from AT.simulator_thread.simulator_routine_by_false_eclss import simulate_by_dummy_eclss
from AT.simulator_thread.simulator_routine_by_real_eclss import handle_eclss_update
from AT.neo4j_queries.query_functions import diagnose_symptoms_by_subset_of_anomaly
from AT.neo4j_queries.query_functions import diagnose_symptoms_by_intersection_with_anomaly
from AT.neo4j_queries.query_functions import retrieve_all_anomalies
from AT.neo4j_queries.query_functions import retrieve_procedures_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_ordered_steps_from_procedure
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure


# QUEUES
from AT.global_objects import frontend_to_hub_queue
from AT.global_objects import hub_to_at_queue
from AT.global_objects import hub_to_simulator_queue
from AT.global_objects import simulator_to_hub_queue
from AT.global_objects import server_to_simulator_queue
from auth_API.helpers import get_or_create_user_information


def check_threads_status(simulator_thread, hub_thread, at_thread):
    sim_is_alive = simulator_thread.is_alive()
    hub_is_alive = hub_thread.is_alive()
    ad_is_alive = at_thread.is_alive()

    # Check if all the treads are in a healthy status. Display a message according to the result.
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
    return


def convert_threshold_tag_to_neo4j_relationship(threshold_tag):
    relationship = ''
    if threshold_tag == 'LCL' or threshold_tag == 'LWL':
        relationship = 'Exceeds_LWL'
    elif threshold_tag == 'UCL' or threshold_tag == 'UWL':
        relationship = 'Exceeds_UWL'
    else:
        print('Invalid threshold tag')
        raise

    return relationship


class SimulateTelemetry(APIView):
    def post(self, request):
        # Hub thread initialization
        hub_thread = threading.Thread(target=hub_routine,
                                      args=(frontend_to_hub_queue, simulator_to_hub_queue, hub_to_simulator_queue,
                                            hub_to_at_queue, at_to_hub_queue, request))
        hub_thread.start()

        # Simulator thread initialization
        simulator_thread = threading.Thread(target=simulate_by_dummy_eclss,
                                            args=(simulator_to_hub_queue, hub_to_simulator_queue))
        simulator_thread.start()

        # Anomaly detection thread initialization
        at_thread = threading.Thread(target=anomaly_treatment_routine,
                                     args=(hub_to_at_queue, at_to_hub_queue,))
        at_thread.start()

        # Thread status check
        check_threads_status(simulator_thread, hub_thread, at_thread)
        return Response()


class StopTelemetry(APIView):
    def post(self, request):
        print('STOP')
        signal = {'type': 'stop', 'content': None}
        frontend_to_hub_queue.put(signal)
        return Response()


class StartSeclssFeed(APIView):
    def post(self, request):
        # Hub thread initialization
        hub_thread = threading.Thread(target=hub_routine,
                                      args=(frontend_to_hub_queue, simulator_to_hub_queue, hub_to_simulator_queue,
                                            hub_to_at_queue, at_to_hub_queue, request))
        hub_thread.start()

        # Simulator thread initialization
        simulator_thread = threading.Thread(target=handle_eclss_update,
                                            args=(simulator_to_hub_queue, hub_to_simulator_queue,
                                                  server_to_simulator_queue))
        simulator_thread.start()

        # Anomaly detection thread initialization
        at_thread = threading.Thread(target=anomaly_treatment_routine,
                                     args=(hub_to_at_queue, at_to_hub_queue,))
        at_thread.start()

        # Thread status check
        check_threads_status(simulator_thread, hub_thread, at_thread)
        return Response()


class SeclssFeed(APIView):
    def post(self, request):
        sensor_data = request.data['parameters']
        # print(sensor_data)
        parsed_sensor_data = json.loads(sensor_data)
        server_to_simulator_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data})
        return Response(parsed_sensor_data)


class RequestDiagnosis(APIView):
    def post(self, request):
        # Retrieve the symptoms list from the request
        symptoms_list = json.loads(request.data['symptomsList'])

        # Parse the symptoms list to meet the neo4j query function requirements
        parsed_symptoms_list = []
        for item in symptoms_list:
            threshold_tag = item['threshold_tag']
            relationship = convert_threshold_tag_to_neo4j_relationship(threshold_tag)
            symptom = {'measurement': item['measurement'],
                       'display_name': item['display_name'],
                       'relationship': relationship}
            parsed_symptoms_list.append(symptom)

        # Query the neo4j graph (do not delete first line until second one is tested)
        # diagnosis_list = diagnose_symptoms_by_subset_of_anomaly(parsed_symptoms_list)
        diagnosis_list = diagnose_symptoms_by_intersection_with_anomaly(parsed_symptoms_list)

        # Build the diagnosis report and send it to the frontend
        diagnosis_report = {'symptoms_list': symptoms_list, 'diagnosis_list': diagnosis_list}

        return Response(diagnosis_report)


class LoadAllAnomalies(APIView):
    def post(self, request):
        # Query the neo4j graph
        anomaly_list = retrieve_all_anomalies()

        return Response(anomaly_list)


class RetrieveProcedureFromAnomaly(APIView):
    def post(self, request):
        # Retrieve the anomaly name list from the request
        anomaly_name = json.loads(request.data['anomaly_name'])

        # Obtain all the procedures related to the anomaly
        procedure_names = retrieve_procedures_from_anomaly(anomaly_name)

        return Response(procedure_names)


class RetrieveStepsFromProcedure(APIView):
    def post(self, request):
        # Retrieve the symptoms list from the request
        procedure_name = json.loads(request.data['procedure_name'])

        # Build the diagnosis report and send it to the frontend
        # steps_list = retrieve_ordered_steps_from_procedure(procedure_name)
        steps_list = retrieve_fancy_steps_from_procedure(procedure_name)

        return Response(steps_list)
