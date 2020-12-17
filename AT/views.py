import json
import threading

import redis
from rest_framework.response import Response
from rest_framework.views import APIView
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.automated_at_routines.hub_routine import hub_routine
from AT.simulator_thread.simulator_routine_by_false_eclss import simulate_by_dummy_eclss
from AT.simulator_thread.simulator_routine_by_real_eclss import handle_eclss_update
from AT.neo4j_queries.query_functions import diagnose_symptoms_by_intersection_with_anomaly, \
    retrieve_figures_from_procedure
from AT.neo4j_queries.query_functions import retrieve_all_anomalies
from AT.neo4j_queries.query_functions import retrieve_procedures_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure
from AT.neo4j_queries.query_functions import retrieve_objective_from_procedure
from AT.neo4j_queries.query_functions import retrieve_equipment_from_procedure
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information

# THREADS + QUEUES
import AT.global_objects as global_obj


def check_threads_status():
    hub_is_alive = global_obj.hub_thread.is_alive()
    sEclss_is_alive = global_obj.sEclss_thread.is_alive()
    sim_is_alive_one = global_obj.simulator_threads[0].is_alive()
    sim_is_alive_two = global_obj.simulator_threads[1].is_alive()
    sim_is_alive_three = global_obj.simulator_threads[2].is_alive()
    sim_is_alive_four = global_obj.simulator_threads[3].is_alive()
    sEclss_at_is_alive = global_obj.sEclss_at_thread.is_alive()
    sim_at_is_alive_one = global_obj.simulator_at_threads[0].is_alive()
    sim_at_is_alive_two = global_obj.simulator_at_threads[1].is_alive()
    sim_at_is_alive_three = global_obj.simulator_at_threads[2].is_alive()
    sim_at_is_alive_four = global_obj.simulator_at_threads[3].is_alive()

    # Check if all the treads are in a healthy status. Display a message according to the result.
    if hub_is_alive and sEclss_is_alive and sim_is_alive_one and sim_is_alive_two and sim_is_alive_three \
            and sim_is_alive_four and sEclss_at_is_alive and sim_at_is_alive_one and sim_at_is_alive_two \
            and sim_at_is_alive_three and sim_at_is_alive_four:
        print('**********\nAll AT threads started successfully.\n**********')
    else:
        print('**********')
        if not hub_is_alive:
            print('Hub thread start failure.')
        if not sEclss_is_alive:
            print('sEclss thread start failure.')
        if not sim_is_alive_one:
            print('Simulator thread 1 start failure.')
        if not sim_is_alive_two:
            print('Simulator thread 2 start failure.')
        if not sim_is_alive_three:
            print('Simulator thread 3 start failure.')
        if not sim_is_alive_four:
            print('Simulator thread 4 start failure.')
        if not sEclss_at_is_alive:
            print('Anomaly treatment thread for sEclss start failure.')
        if not sim_at_is_alive_one:
            print('Anomaly treatment thread 1 for the simulator thread start failure.')
        if not sim_at_is_alive_two:
            print('Anomaly treatment thread 2 for the simulator thread start failure.')
        if not sim_at_is_alive_three:
            print('Anomaly treatment thread 3 for the simulator thread start failure.')
        if not sim_at_is_alive_four:
            print('Anomaly treatment thread 4 for the simulator thread start failure.')
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


class SeclssFeed(APIView):
    def post(self, request):
        if 'parameters' in request.data:
            sensor_data = request.data['parameters']
            # print(sensor_data)
            parsed_sensor_data = json.loads(sensor_data)
            if global_obj.sEclss_thread is not None \
                    and global_obj.sEclss_thread.is_alive() \
                    and global_obj.sEclss_thread.name == "Real Telemetry Thread":
                global_obj.server_to_sEclss_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data})
            return Response(parsed_sensor_data)
        else:
            print('ERROR retrieving the sensor data from the ECLSS simulator')
            return Response({
                "status": "error",
                "message": "ERROR retrieving the sensor data from the ECLSS simulator"
            })

class HeraFeed(APIView):
    def post(self, request):
        # habitatStatus
        if 'habitatStatus' in request.data:
            habitat_status = request.data['habitatStatus']
            parsed_sensor_data = json.loads(habitat_status)['Parameters']
            if global_obj.hera_thread is not None \
                    and global_obj.hera_thread.is_alive() \
                    and global_obj.hera_thread.name == "Hera Telemetry Thread":
                global_obj.server_to_hera_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data})
                #global_obj.server_to_hera_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data['Parameters']})
            return Response(parsed_sensor_data)
        else:
            print(request.data)
            print(request.headers)
            print('ERROR retrieving the sensor data from the Hera simulator')
            return Response({
                "status": "error",
                "message": "ERROR retrieving the sensor data from the Hera simulator"
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
        figures = retrieve_figures_from_procedure(procedure_name)

        # Build the output dictionary
        info = {
            'procedureStepsList': steps_list,
            'procedureObjective': objective,
            'procedureEquipment': equipment,
            'procedureFigures': figures,
        }

        return Response(info)
