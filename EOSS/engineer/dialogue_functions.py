import json
import logging

from thrift.Thrift import TException, TApplicationException

from EOSS.vassar.api import VASSARClient
from EOSS.data import problem_specific
from daphne_context.models import UserInformation

logger = logging.getLogger('EOSS.engineer')


def get_architecture_scores(design_id, designs, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        scores = client.get_architecture_score_explanation(context["screen"]["problem"],
                                                           designs.get(id=design_id))

        # End the connection before return statement
        client.end_connection()
        return scores

    except Exception:
        logger.exception('Exception in loading architecture score information')
        client.end_connection()
        return None


def get_satisfying_data_products(design_id, designs, subobjective, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        subobjective_explanation = client.get_subscore_details(context["screen"]["problem"],
                                                               designs.get(id=design_id),
                                                               subobjective.upper())
        satisfying_data_products = [subobjective_explanation.taken_by[i] for i, x in enumerate(subobjective_explanation.scores) if x == 1.0][:5]
        # End the connection before return statement
        client.end_connection()
        return satisfying_data_products

    except Exception:
        logger.exception('Exception in checking satisfying data products for a subobjective')
        client.end_connection()
        return None


def get_unsatisfied_justifications(design_id, designs, subobjective, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        subobjective_explanation = client.get_subscore_details(context["screen"]["problem"],
                                                               designs.get(id=design_id),
                                                               subobjective.upper())
        if max(subobjective_explanation.scores) < 1.:
            unsatisfied_data_products = [subobjective_explanation.taken_by[i] for i, x in enumerate(subobjective_explanation.scores) if x < 1.0]
            unsatisfied_justifications = [subobjective_explanation.justifications[i] for i, x in enumerate(subobjective_explanation.scores) if x < 1.0]
            # Only show the first 4 explanations
            explanations = [
                {
                    "data_product": dp,
                    "explanations": ", ".join(unsatisfied_justifications[i])
                } for i, dp in enumerate(unsatisfied_data_products)
            ][:5]
        else:
            unsatisfied_justifications = []
        # End the connection before return statement
        client.end_connection()
        return explanations

    except TException:
        logger.exception('Exception in justifying not satisfying a subobjective')
        client.end_connection()
        return None


def get_panel_scores(design_id, designs, panel, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        stakeholders_to_excel = {
            "atmospheric": "ATM",
            "oceanic": "OCE",
            "terrestrial": "TER",
            "weather": "WEA",
            "climate": "CLI",
            "land and ecosystems": "ECO",
            "water": "WAT",
            "human health": "HEA"
        }

        panel_code = stakeholders_to_excel[panel.lower()]
        panel_scores = client.get_panel_score_explanation(context["screen"]["problem"],
                                                          designs.get(id=design_id),
                                                          panel_code)

        # End the connection before return statement
        client.end_connection()
        return panel_scores

    except TException:
        logger.exception('Exception in loading panel score information')
        client.end_connection()
        return None


def get_objective_scores(design_id, designs, objective, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        objective_scores = client.get_objective_score_explanation(context["screen"]["problem"],
                                                                  designs.get(id=design_id),
                                                                  objective.upper())

        # End the connection before return statement
        client.end_connection()
        return objective_scores

    except TException:
        logger.exception('Exception in loading objective score information')
        client.end_connection()
        return None


def get_instruments_for_objective(objective, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        instruments = client.get_instruments_for_objective(context["screen"]["problem"], objective.upper())

        # End the connection before return statement
        client.end_connection()
        return instruments

    except TException:
        logger.exception('Exception in loading related instruments to an objective')
        client.end_connection()
        return None


def get_instruments_for_stakeholder(stakeholder, context):
    port = context["screen"]["vassar_port"]
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        stakeholders_to_excel = {
            "atmospheric": "ATM",
            "oceanic": "OCE",
            "terrestrial": "TER",
            "weather": "WEA",
            "climate": "CLI",
            "land and ecosystems": "ECO",
            "water": "WAT",
            "human health": "HEA"
        }
        panel_code = stakeholders_to_excel[stakeholder.lower()]
        stakeholder_instruments = client.get_instruments_for_panel(context["screen"]["problem"], panel_code)

        # End the connection before return statement
        client.end_connection()
        return stakeholder_instruments

    except TException:
        logger.exception('Exception in loading related instruments to a panel')
        client.end_connection()
        return None


def get_instrument_parameter(vassar_instrument, instrument_parameter, context, new_dialogue_contexts):
    new_dialogue_contexts["engineer_context"].vassar_instrument = vassar_instrument
    new_dialogue_contexts["engineer_context"].instrument_parameter = instrument_parameter

    capabilities_sheet = problem_specific.get_capabilities_sheet(context["screen"]["problem"])
    capability_found = False
    capability_value = None
    for row in capabilities_sheet.itertuples(name='Instrument'):
        if row[1].split()[1] == vassar_instrument:
            for i in range(2, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_found = True
                    capability_value = row[i].split()[1]

    if capability_found:
        return 'The ' + instrument_parameter + ' for ' + vassar_instrument + ' is ' + capability_value
    else:
        instrument_sheet = problem_specific.get_instrument_sheet(context["screen"]["problem"], vassar_instrument)

        for i in range(2, len(instrument_sheet.columns)):
            if instrument_sheet[i][0].split()[0] == instrument_parameter:
                capability_found = True
        if capability_found:
            return 'I have found different values for this parameter depending on the measurement. ' \
                   'Please tell me for which measurement you want this parameter: ' \
                   + ', '.join([measurement[11:-1] for measurement in instrument_sheet[1]])
        else:
            return 'I have not found any information for this measurement.'


def get_instrument_parameter_followup(vassar_instrument, instrument_parameter, instrument_measurement, context):
    instrument_sheet = problem_specific.get_instrument_sheet(context["screen"]["problem"], vassar_instrument)

    capability_value = None
    for row in instrument_sheet.itertuples(index=True, name='Measurement'):
        if row[2][11:-1] == instrument_measurement:
            for i in range(3, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_value = row[i].split()[1]

    return 'The ' + instrument_parameter + ' for instrument ' + vassar_instrument + ' and measurement ' + \
           instrument_measurement + ' is ' + capability_value


def get_measurement_requirement(vassar_measurement, instrument_parameter, context, new_dialogue_contexts):
    new_dialogue_contexts["engineer_context"].vassar_measurement = vassar_measurement
    new_dialogue_contexts["engineer_context"].instrument_parameter = instrument_parameter

    requirements_sheet = problem_specific.get_requirements_sheet(context["screen"]["problem"])
    requirement_found = False
    requirements = []
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement_found = True
            requirements.append({"subobjective": row[1], "type": row[4], "thresholds": row[5]})

    if requirement_found:
        if len(requirements) > 1:
            return 'I have found different values for this requirement depending on the stakeholder. ' \
                   'Please tell me for which stakeholder you want this requirement: ' \
                   + ', '.join([requirement["subobjective"] for requirement in requirements])
        else:
            threshold = requirements[0]["thresholds"][1:-1].split(',')[-1]
            target_value = requirements[0]["thresholds"][1:-1].split(',')[0]
            return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' (subobjective ' + \
                   requirements[0]["subobjective"] + ') is ' + threshold + ' and its target value is ' + \
                   target_value + '.'
    else:
        return 'I have not found any information for this requirement.'


def get_measurement_requirement_followup(vassar_measurement, instrument_parameter, subobjective, context):
    requirements_sheet = problem_specific.get_requirements_sheet(context["screen"]["problem"])
    requirement = None
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[1] == subobjective.upper() and row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement = {"subobjective": row[1], "type": row[4], "thresholds": row[5]}

    threshold = requirement["thresholds"][1:-1].split(',')[-1]
    target_value = requirement["thresholds"][1:-1].split(',')[0]
    return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' for subobjective ' \
           + requirement["subobjective"] + ' is ' + threshold + ' and its target value is ' + target_value + '.'


def get_cost_explanation(design_id, designs, context):
    try:
        # Start connection with VASSAR
        port = context["screen"]["vassar_port"]
        client = VASSARClient(port)
        client.start_connection()

        # Get the correct architecture
        arch = designs.get(id=design_id)
        problem = context["screen"]["problem"]

        cost_explanation = client.get_arch_cost_information(problem, arch)

        # End the connection before return statement
        client.end_connection()

        def budgets_to_json(explanation):
            json_list = []
            for exp in explanation:
                json_exp = {
                    'orbit_name': exp.orbit_name,
                    'payload': exp.payload,
                    'launch_vehicle': exp.launch_vehicle,
                    'total_mass': exp.total_mass,
                    'total_power': exp.total_power,
                    'total_cost': exp.total_cost,
                    'mass_budget': exp.mass_budget,
                    'power_budget': exp.power_budget,
                    'cost_budget': exp.cost_budget
                }
                json_list.append(json_exp)
            return json_list

        json_explanation = budgets_to_json(cost_explanation)
        for explanation in json_explanation:
            explanation["subcosts"] = [type + ": $" + str("%.2f" % round(number, 2)) + 'M' for type, number in explanation["cost_budget"].items()]

        return json_explanation

    except TApplicationException as exc:
        logger.exception('Exception when retrieving information from the current architecture!')
        client.end_connection()
        raise exc
