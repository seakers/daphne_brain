import json

from AT.models import ATContext
from AT.neo4j_queries.query_functions import retrieve_thresholds_from_measurement, retrieve_all_components, \
    retrieve_procedures_title_from_anomaly, retrieve_step_from_procedure, retrieve_procedures_from_pNumber
from AT.neo4j_queries.query_functions import retrieve_units_from_measurement
from AT.neo4j_queries.query_functions import retrieve_risks_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_symptoms_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_procedures_fTitle_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_affected_subsystems_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_affected_components_from_procedure
from AT.neo4j_queries.query_functions import retrieve_time_from_procedure
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure
from AT.dialogue.data_helpers import last_measurement_value_from_context
from AT.dialogue.data_helpers import pdf_link_from_procedure


def get_measurement_current_value(measurement, context):
    # Retrieve the last value from the context
    measurement_info = last_measurement_value_from_context(measurement, context)

    # If not empty, retrieve the units and build the result.
    text_response = []

    if measurement_info is not None:
        for values in measurement_info:
            units = retrieve_units_from_measurement(measurement)
            info_list = {'name': str(measurement), 'parameter_group': str(values.get('parameter_group')),
                         'value': str(values.get('value')), 'units': units}
            text_response.append(info_list)
    else:
        text_response.append('There is no measurement with this name and parameter group within the current sensor '
                             'data.')

    result = text_response
    return result


def get_measurement_thresholds(measurement):
    # Query the neo4j graph for the thresholds and units
    thresholds = retrieve_thresholds_from_measurement(measurement)
    units = retrieve_units_from_measurement(measurement)

    # Check if the requested measurement exists and proceed accordingly
    if thresholds is None:
        units = ''
        error_message = 'This measurement does not exist'
        thresholds = {'LowerCautionLimit': error_message, 'LowerWarningLimit': error_message, 'UpperWarning'
                                                                                              'Limit': error_message,
                      'UpperCautionLimit': error_message}
    else:
        units = units

    # Parse the result
    result_list = []
    for item in thresholds:
        for key in item:
            result = {'threshold_type': key,
                      'threshold_value': item[key],
                      'threshold_units': units}
            result_list.append(result)
    return result_list


def check_measurement_status(measurement, context):
    # Retrieve the last value from the context
    measurement_info = last_measurement_value_from_context(measurement, context)

    # Query the neo4j graph for the thresholds
    thresholds_info = retrieve_thresholds_from_measurement(measurement)

    result = []

    if measurement_info and thresholds_info:
        for measurement in measurement_info:
            response = []
            for threshold in thresholds_info:
                if measurement['parameter_group'] == threshold['ParameterGroup']:
                    if measurement['value'] <= threshold['LowerWarningLimit']:
                        response = measurement['name'] + ' (' + threshold['ParameterGroup'] + ') ' + 'is below the ' \
                                                                                                     'Lower ' \
                                                                                                     'Warning ' \
                                                                                                     'Limit '
                    elif threshold['LowerCautionLimit'] < measurement['value'] <= threshold['LowerWarningLimit']:
                        response = measurement['name'] + ' (' + threshold['ParameterGroup'] + ') ' + 'is below the ' \
                                                                                                     'Lower ' \
                                                                                                     'Caution ' \
                                                                                                     'Limit (but ' \
                                                                                                     'above the Lower '\
                                                                                                     'Warning Limit) '
                    elif threshold['LowerCautionLimit'] < measurement['value'] <= threshold['UpperCautionLimit']:
                        response = measurement['name'] + ' (' + threshold['ParameterGroup'] + ') ' + ' is nominal'
                    elif threshold['UpperCautionLimit'] < measurement['value'] <= threshold['UpperWarningLimit']:
                        response = measurement['name'] + ' (' + threshold['ParameterGroup'] + ') ' + 'is above the ' \
                                                                                                     'Upper ' \
                                                                                                     'Caution ' \
                                                                                                     'Limit (but ' \
                                                                                                     'below the Upper '\
                                                                                                     'Warning Limit) '
                    elif threshold['UpperWarningLimit'] < measurement['value']:
                        response = measurement['name'] + ' (' + threshold['ParameterGroup'] + ') ' + 'is above the ' \
                                                                                                     'Upper ' \
                                                                                                     'Warning ' \
                                                                                                     'Limit '
                    else:
                        response = 'I had some troubles checking this measurement status. Please report this to ' \
                                   'someone. '
            result.append(response)
    else:
        response = 'There is no measurement with this name and parameter group within the current sensor data.'
        result.append(response)

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


def get_anomaly_procedure_without_number(anomaly):
    # Query the neo4j graph for the anomaly procedures
    procedures = retrieve_procedures_title_from_anomaly(anomaly)
    procedure_info_list = []
    for procedure in procedures:
        pdf_link = pdf_link_from_procedure(procedure)
        procedure_info = {'procedure_name': procedure, 'pdf_link': pdf_link}
        procedure_info_list.append(procedure_info)
    return procedure_info_list


def get_anomaly_procedures(anomaly):
    # Query the neo4j graph for the anomaly procedures
    procedures = retrieve_procedures_fTitle_from_anomaly(anomaly)
    procedure_info_list = []
    for procedure in procedures:
        pdf_link = pdf_link_from_procedure(procedure)
        procedure_info = {'procedure_name': procedure, 'pdf_link': pdf_link}
        procedure_info_list.append(procedure_info)
    return procedure_info_list


def get_anomaly_etr(anomaly):
    # Query the neo4j graph for the anomaly procedures for estimated time of resolution (etr)
    procedures = retrieve_procedures_fTitle_from_anomaly(anomaly)
    total_time = 0
    procedure_info_list = []
    for procedure in procedures:
        procedure_time = retrieve_time_from_procedure(procedure)
        procedure_info = {'procedure_name': procedure, 'procedure_time': procedure_time}
        procedure_info_list.append(procedure_info)
    return procedure_info_list


def get_procedure_etr(procedure):
    # Query the neo4j graph for the procedure estimated time of resolution (etr)
    procedures_time = retrieve_time_from_procedure(procedure)
    procedure_info = {'procedure_name': procedure, 'procedure_time': procedures_time}
    return procedure_info


def get_procedure_pdf(procedure):
    try:
        float(procedure)
        procedure = retrieve_procedures_from_pNumber(procedure)
    except ValueError:
        print("Not a number")
    pdf_link = pdf_link_from_procedure(procedure)
    procedure_info = {'procedure_name': procedure, 'pdf_link': pdf_link}
    return procedure_info


def get_anomaly_affected_subsystem(anomaly):
    # Query the neo4j graph for the anomaly risks
    subsystems = retrieve_affected_subsystems_from_anomaly(anomaly)
    return subsystems


def get_steps_from_procedure(procedure, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    # Query the neo4j graph for procedure steps from procedure name
    procedure_infolist = retrieve_fancy_steps_from_procedure(procedure)
    atcontext.selected_procedures = json.dumps([procedure])
    procedure_steps = []
    for procedure_step in procedure_infolist:
        procedure_info = {'label': procedure_step['label'], 'action': procedure_step['action']}
        procedure_steps.append(procedure_info)
    new_dialogue_contexts["atdialogue_context"].all_steps_from_procedure = json.dumps(procedure_steps)
    atcontext.save()
    return procedure_steps


def get_first_step_from_procedure(procedure, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    procedure_steps = get_steps_from_procedure(procedure, context, new_dialogue_contexts)
    first_step = procedure_steps[0]
    new_dialogue_contexts["atdialogue_context"].next_step_pointer = 1
    new_dialogue_contexts["atdialogue_context"].previous_step_pointer = 0
    new_dialogue_contexts["atdialogue_context"].current_step_pointer = 0
    atcontext.save()
    return first_step


def get_next_step_from_context(all_steps_from_procedure, next_step_pointer, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    if next_step_pointer == -1:
        return ""
    else:
        next_step = json.loads(all_steps_from_procedure)[next_step_pointer]
        new_dialogue_contexts["atdialogue_context"].all_steps_from_procedure = all_steps_from_procedure
        new_dialogue_contexts["atdialogue_context"].next_step_pointer = next_step_pointer + 1
        new_dialogue_contexts["atdialogue_context"].previous_step_pointer = next_step_pointer - 1
        new_dialogue_contexts["atdialogue_context"].current_step_pointer = next_step_pointer
    atcontext.save()
    return next_step


def get_previous_step_from_context(all_steps_from_procedure, previous_step_pointer, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    if previous_step_pointer == -1:
        previous_step_pointer += 1
        return ""
    else:
        previous_step = json.loads(all_steps_from_procedure)[previous_step_pointer]
        new_dialogue_contexts["atdialogue_context"].all_steps_from_procedure = all_steps_from_procedure
        new_dialogue_contexts["atdialogue_context"].next_step_pointer = previous_step_pointer + 1
        new_dialogue_contexts["atdialogue_context"].previous_step_pointer = previous_step_pointer - 1
        new_dialogue_contexts["atdialogue_context"].current_step_pointer = previous_step_pointer
    atcontext.save()
    return previous_step


def get_current_step_from_context(all_steps_from_procedure, current_step_pointer, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    current_step = json.loads(all_steps_from_procedure)[current_step_pointer]
    new_dialogue_contexts["atdialogue_context"].all_steps_from_procedure = all_steps_from_procedure
    new_dialogue_contexts["atdialogue_context"].next_step_pointer = current_step_pointer + 1
    new_dialogue_contexts["atdialogue_context"].previous_step_pointer = current_step_pointer - 1
    new_dialogue_contexts["atdialogue_context"].current_step_pointer = current_step_pointer
    atcontext.save()
    return current_step


def get_component_images(component):
    component_list = retrieve_all_components()
    for item in component_list:
        if item == component:
            unspaced = item.replace(" ", "_")
            unstripped = unspaced + ".png"
    return unstripped


def get_step_from_procedure(step_number, procedure, context, new_dialogue_contexts):
    atcontext = ATContext.objects.get(id=context["screen"]["id"])
    procedure_steps = get_steps_from_procedure(procedure, context, new_dialogue_contexts)
    this_step = retrieve_step_from_procedure(step_number, procedure)

    # Get current step
    step_info = []
    if this_step:
        step_info = {'step': step_number, 'action': this_step}

    next_step = 0
    for step in procedure_steps:
        next_step = next_step + 1
        if step.get('action') == this_step:
            break

    new_dialogue_contexts["atdialogue_context"].next_step_pointer = next_step
    new_dialogue_contexts["atdialogue_context"].previous_step_pointer = next_step - 2
    new_dialogue_contexts["atdialogue_context"].current_step_pointer = next_step - 1
    atcontext.save()
    return step_info
