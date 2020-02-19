import json
import pandas as pd

import AT.recommendation.dialogue_functions as recommendation
from AT.neo4j_queries.query_functions import retrieve_thresholds_from_measurement
from AT.neo4j_queries.query_functions import retrieve_units_from_measurement
from AT.neo4j_queries.query_functions import retrieve_risks_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_symptoms_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_procedures_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_affected_subsystems_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_affected_components_from_procedure
from AT.neo4j_queries.query_functions import retrieve_time_from_procedure
from AT.dialogue.data_helpers import last_measurement_value_from_context
from AT.dialogue.data_helpers import pdf_link_from_procedure


def get_measurement_current_value(measurement, context):
    # Retrieve the last value from the context
    last_value = last_measurement_value_from_context(measurement, context)
    print(context)

    # If not empty, retrieve the units and build the result.
    if last_value is not None:
        units = retrieve_units_from_measurement(measurement)
        result = {'measurement_value': last_value, 'measurement_units': units}
    else:
        print('The telemetry context is empty or incomplete.')
        result = {'measurement_value': 'None', 'measurement_units': 'None'}

    return result


def get_measurement_thresholds(measurement):
    # Query the neo4j graph for the thresholds and units
    thresholds = retrieve_thresholds_from_measurement(measurement)
    units = retrieve_units_from_measurement(measurement)

    # Parse the result
    result_list = []
    for key in thresholds:
        result = {'threshold_type': key, 'threshold_value': thresholds[key], 'threshold_units': units}
        result_list.append(result)

    return result_list


def check_measurement_status(measurement, context):
    # Retrieve the last value from the context
    last_value = last_measurement_value_from_context(measurement, context)

    # Query the neo4j graph for the thresholds
    thresholds = retrieve_thresholds_from_measurement(measurement)

    if last_value is not None:
        if last_value <= thresholds['LCL']:
            zone = 'below the Low Critical Limit'
        elif thresholds['LCL'] < last_value <= thresholds['LWL']:
            zone = 'below the Low Warning Limit (but above the Low Critical Limit)'
        elif thresholds['LWL'] < last_value <= thresholds['UWL']:
            zone = 'nominal'
        elif thresholds['UWL'] < last_value <= thresholds['UCL']:
            zone = 'above the High Warning Limit (but below the High Critical Limit)'
        elif thresholds['UCL'] < last_value:
            zone = 'above the High Critical Limit'
        else:
            zone = 'ZONE ERROR'
    else:
        zone = 'None'

    return zone


def get_anomaly_risks(anomaly):
    # Query the neo4j graph for the anomaly risks
    risks = retrieve_risks_from_anomaly(anomaly)

    return risks


def get_anomaly_symptoms(anomaly):
    # Query the neo4j graph for the anomaly risks
    symptoms = retrieve_symptoms_from_anomaly(anomaly)

    return symptoms


def get_procedure_affected_components(procedure):
    # Query the neo4j graph for the anomaly risks
    components = retrieve_affected_components_from_procedure(procedure)

    return components


def get_anomaly_procedures(anomaly):
    # Query the neo4j graph for the anomaly procedures
    procedures = retrieve_procedures_from_anomaly(anomaly)
    procedure_info_list = []
    for procedure in procedures:
        pdf_link = pdf_link_from_procedure(procedure)
        procedure_info = {'procedure_name': procedure, 'pdf_link': pdf_link}
        procedure_info_list.append(procedure_info)
    return procedure_info_list


def get_anomaly_etr(anomaly):
    # Query the neo4j graph for the anomaly procedures
    procedures = retrieve_procedures_from_anomaly(anomaly)
    total_time = 0
    procedure_info_list = []
    for procedure in procedures:
        procedure_time = retrieve_time_from_procedure(procedure)
        total_time += procedure_time
        procedure_info = {'procedure_name': procedure, 'procedure_time': procedure_time}
        procedure_info_list.append(procedure_info)
    total_procedure_info = {'procedure_name': 'TOTAL TIME', 'procedure_time': total_time}
    procedure_info_list.append(total_procedure_info)
    return procedure_info_list


def get_procedure_etr(procedure_name):
    # Query the neo4j graph for the procedure etr
    procedures_time = retrieve_time_from_procedure(procedure_name)
    procedure_info = {'procedure_name': procedure_name, 'procedure_time': procedures_time}
    return procedure_info


def get_procedure_pdf(procedure):
    # Query the neo4j graph for the anomaly risks
    pdf_link = pdf_link_from_procedure(procedure)
    procedure_info = {'procedure_name': procedure, 'pdf_link': pdf_link}
    return procedure_info


def get_anomaly_affected_subsystem(anomaly):
    # Query the neo4j graph for the anomaly risks
    subsystems = retrieve_affected_subsystems_from_anomaly(anomaly)

    return subsystems
