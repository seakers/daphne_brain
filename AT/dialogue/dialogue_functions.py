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
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure
from AT.dialogue.data_helpers import last_measurement_value_from_context
from AT.dialogue.data_helpers import pdf_link_from_procedure


def get_measurement_current_value(measurement, parameter_group, context):
    # Retrieve the last value from the context
    measurement_display_name = measurement + ' (' + parameter_group + ')'
    last_value = last_measurement_value_from_context(measurement_display_name, context)

    # If not empty, retrieve the units and build the result.
    text_response = ''
    if last_value is not None:
        units = retrieve_units_from_measurement(measurement)
        text_response = 'The current value of the ' + str(measurement_display_name) + \
                        ' measurement is: ' + str(last_value) + ' [' + units + '].'
    else:
        text_response = 'There is no measurement with this name and parameter group within the current sensor data.'

    result = text_response
    return result


def get_measurement_thresholds(measurement, parameter_group):
    # Query the neo4j graph for the thresholds and units
    thresholds = retrieve_thresholds_from_measurement(measurement, parameter_group)
    units = retrieve_units_from_measurement(measurement)

    # Check if the requested measurement exists and proceed accordingly
    if thresholds['LCL'] == 'None':
        units = ''
        error_message = 'This measurement does not exist'
        thresholds = {'LCL': error_message, 'LWL': error_message, 'UWL': error_message, 'UCL': error_message}
    else:
        units = '[' + units + ']'

    # Parse the result
    result_list = []
    for key in thresholds:
        result = {'threshold_type': key,
                  'threshold_value': thresholds[key],
                  'threshold_units': units}
        result_list.append(result)
    return result_list


def check_measurement_status(measurement, parameter_group, context):
    # Retrieve the last value from the context
    measurement_display_name = measurement + ' (' + parameter_group + ')'
    last_value = last_measurement_value_from_context(measurement_display_name, context)

    # Query the neo4j graph for the thresholds
    thresholds = retrieve_thresholds_from_measurement(measurement, parameter_group)

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

    # Check the final outcome and build the result accordingly
    if zone == 'None':
        result = 'There is no measurement with this name and parameter group within the current sensor data.'
    elif zone == 'ZONE ERROR':
        result = 'I had some troubles checking this measurement status. Please report this to someone.'
    else:
        text = 'The ' + measurement_display_name + ' measurement is currently ' + zone + '.'
        result = text
    return result


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
    # Query the neo4j graph for the anomaly procedures for estimated time of resolution (etr)
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
    # Query the neo4j graph for the procedure estimated time of resolution (etr)
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


def get_procedure_steps_from_procedure_name(procedure_name, context):
    # Query the neo4j graph for procedure steps from procedure name
    procedure_infolist = retrieve_fancy_steps_from_procedure(procedure_name)
    context['screen']['selected_procedures'] = procedure_name
    procedure_steps = []
    for procedure_step in procedure_infolist:
        procedure_info = {'label': procedure_step['label'], 'action': procedure_step['action']}
        procedure_steps.append(procedure_info)
    context['screen']['all_steps_from_procedure'] = procedure_steps


def get_first_step_from_procedure_name(procedure_name, context):
    get_procedure_steps_from_procedure_name(procedure_name, context)
    first_step = context['screen']['all_steps_from_procedure'][0]
    context['screen']['next_step_pointer'] = 1
    context['screen']['previous_step_pointer'] = 0
    context['screen']['current_step_pointer'] = 0
    return first_step


def get_next_step_from_context(context):
    next_step_pointer = context['screen']['next_step_pointer']
    if next_step_pointer == -1:
        return ""
    else:
        next_step = context['screen']['all_steps_from_procedure'][next_step_pointer]
        context['screen']['next_step_pointer'] += 1
        context['screen']['previous_step_pointer'] += 1
        context['screen']['current_step_pointer'] = context['screen']['next_step_pointer']
        return next_step


def get_previous_step_from_context(context):
    previous_step_pointer = context['screen']['previous_step_pointer']
    if previous_step_pointer == -1:
        previous_step_pointer += 1
        return ""
    else:
        previous_step = context['screen']['all_steps_from_procedure'][previous_step_pointer]
        context['screen']['next_step_pointer'] -= 1
        context['screen']['previous_step_pointer'] -= 1
        context['screen']['current_step_pointer'] = context['screen']['previous_step_pointer']
        return previous_step


def get_current_step_from_context(context):
    current_step_pointer = context['screen']['current_step_pointer']
    current_step = context['screen']['all_steps_from_procedure'][current_step_pointer]
    return current_step
