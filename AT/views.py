import json
import threading

from rest_framework.response import Response
from rest_framework.views import APIView
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.automated_at_routines.hub_routine import hub_routine
from AT.simulator_thread.simulator_routine_by_false_eclss import simulate_by_dummy_eclss
from AT.simulator_thread.simulator_routine_by_real_eclss import handle_eclss_update
from AT.neo4j_queries.query_functions import diagnose_symptoms_by_intersection_with_anomaly
from AT.neo4j_queries.query_functions import retrieve_all_anomalies
from AT.neo4j_queries.query_functions import retrieve_procedures_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure
from AT.neo4j_queries.query_functions import retrieve_objective_from_procedure
from AT.neo4j_queries.query_functions import retrieve_equipment_from_procedure


# THREADS + QUEUES
import AT.global_objects as global_obj


def check_threads_status():
    sim_is_alive = global_obj.simulator_thread.is_alive()
    hub_is_alive = global_obj.hub_thread.is_alive()
    ad_is_alive = global_obj.at_thread.is_alive()

    # Check if all the treads are in a healthy status. Display a message according to the result.
    if hub_is_alive and sim_is_alive and ad_is_alive:
        print('**********\nAll AT threads started successfully.\n**********')
    else:
        print('**********')
        if not global_obj.hub_thread.is_alive():
            print('Thread handler thread start failure.')
        if not global_obj.simulator_thread.is_alive():
            print('Simulator thread start failure.')
        if not global_obj.at_thread.is_alive():
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
        if global_obj.simulator_thread is not None and global_obj.simulator_thread.is_alive():
            if global_obj.simulator_thread.name == "Fake Telemetry Thread":
                return Response({
                    "status": "already_running",
                    "message": "Fake Telemetry Thread was already running, this is fine if someone else is using "
                               "Daphne-AT."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "The Real Telemetry Thread was already running, and you are trying to initialize a Fake "
                               "Telemetry Thread. Please ensure the other thread is stopped before trying to call this "
                               "again."
                })

        # Simulator thread initialization
        global_obj.simulator_thread = threading.Thread(target=simulate_by_dummy_eclss,
                                                       name="Fake Telemetry Thread",
                                                       args=(global_obj.simulator_to_hub_queue,
                                                             global_obj.hub_to_simulator_queue))
        global_obj.simulator_thread.start()

        # Thread status check
        if global_obj.simulator_thread.is_alive():
            print("Fake Telemetry Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting Fake Telemetry Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Fake Telemetry Thread. Try again."
            })


class StopTelemetry(APIView):
    def post(self, request):
        signal = {'type': 'stop_telemetry', 'content': None}
        global_obj.frontend_to_hub_queue.put(signal)

        # Wait 2 seconds for simulator thread to terminate
        global_obj.simulator_thread.join(2.0)
        if global_obj.simulator_thread.is_alive():
            return Response({
                "status": "error",
                "message": "The Telemetry Thread did not stop in 2 seconds. Please try again."
            })
        else:
            return Response({
                "status": "success",
                "message": "The Telemetry Thread has stopped correctly. Please proceed."
            })


class StartSeclssFeed(APIView):
    def post(self, request):
        if global_obj.simulator_thread is not None and global_obj.simulator_thread.is_alive():
            if global_obj.simulator_thread.name == "Real Telemetry Thread":
                return Response({
                    "status": "already_running",
                    "message": "Real Telemetry Thread was already running, this is fine if someone else is using "
                               "Daphne-AT."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "The Fake Telemetry Thread was already running, and you are trying to initialize a Real "
                               "Telemetry Thread. Please ensure the other thread is stopped before trying to call this "
                               "again."
                })

        # Simulator thread initialization
        global_obj.simulator_thread = threading.Thread(target=handle_eclss_update,
                                                       name="Real Telemetry Thread",
                                                       args=(global_obj.simulator_to_hub_queue,
                                                             global_obj.hub_to_simulator_queue,
                                                             global_obj.server_to_simulator_queue))
        global_obj.simulator_thread.start()

        # Thread status check
        if global_obj.simulator_thread.is_alive():
            print("Real Telemetry Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting Real Telemetry Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Real Telemetry Thread. Try again."
            })


class StartHubThread(APIView):
    def post(self, request):
        if global_obj.hub_thread is not None and global_obj.hub_thread.is_alive():
            return Response({
                "status": "already_running",
                "message": "Hub Thread was already running, this is fine if someone else is using Daphne-AT."
            })

        # Hub thread initialization
        global_obj.hub_thread = threading.Thread(target=hub_routine,
                                                 name="Hub Thread",
                                                 args=(global_obj.frontend_to_hub_queue,
                                                       global_obj.simulator_to_hub_queue,
                                                       global_obj.hub_to_simulator_queue,
                                                       global_obj.hub_to_at_queue,
                                                       global_obj.at_to_hub_queue,
                                                       request))
        global_obj.hub_thread.start()

        # Thread status check
        if global_obj.hub_thread.is_alive():
            print("Hub Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting Hub Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Hub Thread. Try again."
            })


class StartATThread(APIView):
    def post(self, request):
        if global_obj.at_thread is not None and global_obj.at_thread.is_alive():
            return Response({
                "status": "already_running",
                "message": "AT Thread was already running, this is fine if someone else is using Daphne-AT."
            })

        # Anomaly detection thread initialization
        global_obj.at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                name="AT Thread",
                                                args=(global_obj.hub_to_at_queue,
                                                      global_obj.at_to_hub_queue,))
        global_obj.at_thread.start()

        # Thread status check
        if global_obj.at_thread.is_alive():
            print("AT Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting AT Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting AT Thread. Try again."
            })


class SeclssFeed(APIView):
    def post(self, request):
        if 'parameters' in request.data:
            sensor_data = request.data['parameters']
            # print(sensor_data)
            parsed_sensor_data = json.loads(sensor_data)
            if global_obj.simulator_thread is not None \
                    and global_obj.simulator_thread.is_alive() \
                    and global_obj.simulator_thread.name == "Real Telemetry Thread":
                global_obj.server_to_simulator_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data})
            return Response(parsed_sensor_data)
        else:
            print('ERROR retrieving the sensor data from the ECLSS simulator')
            return Response({
                "status": "error",
                "message": "ERROR retrieving the sensor data from the ECLSS simulator"
            })


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


class RetrieveInfoFromProcedure(APIView):
    def post(self, request):
        # Retrieve the procedure name from the request
        procedure_name = json.loads(request.data['procedure_name'])

        # Query the neo4j to retrieve the procedure information
        steps_list = retrieve_fancy_steps_from_procedure(procedure_name)
        objective = retrieve_objective_from_procedure(procedure_name)
        equipment = retrieve_equipment_from_procedure(procedure_name)

        # Build the output dictionary
        info = {
            'procedureStepsList': steps_list,
            'procedureObjective': objective,
            'procedureEquipment': equipment,
        }

        return Response(info)
