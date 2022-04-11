import logging
import functools
from EOSS.models import EOSSContext


from EOSS.vassar.api import VASSARClient
from EOSS.data import problem_specific
from daphne_context.models import UserInformation

logger = logging.getLogger('EOSS.engineer')


def find_design_by_id(design_set, design_id):
    for design in design_set:
        if design["id"] == design_id:
            return design


def get_architecture_scores(design_id, designs, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    this_design = find_design_by_id(designs, design_id)
    scores = client.get_architecture_score_explanation(eosscontext.problem_id, this_design)
    # If arch scores have not been precomputed
    if scores == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        scores = client.get_architecture_score_explanation(eosscontext.problem_id, this_design)

    return scores


def get_satisfying_data_products(design_id, designs, subobjective, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    this_design = find_design_by_id(designs, design_id)
    subobjective_explanations = client.get_subobjective_score_explanation(this_design, subobjective.upper())
    if subobjective_explanations == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        subobjective_explanations = client.get_subobjective_score_explanation(this_design, subobjective.upper())
    
    satisfying_data_products = [explanation["taken_by"] for explanation in subobjective_explanations if explanation["score"] == 1.0][:5] # Take at most 5
    return satisfying_data_products


def get_unsatisfied_justifications(design_id, designs, subobjective, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    this_design = find_design_by_id(designs, design_id)
    subobjective_explanations = client.get_subobjective_score_explanation(this_design, subobjective.upper())
    if subobjective_explanations == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        subobjective_explanations = client.get_subobjective_score_explanation(this_design, subobjective.upper())

    if len(subobjective_explanations) > 0 and max([explanation["score"] for explanation in subobjective_explanations]) < 1.:
        unsatisfied_data_products = [explanation["taken_by"] for explanation in subobjective_explanations if explanation["score"] < 1.0]
        unsatisfied_justifications = [explanation["justifications"] for explanation in subobjective_explanations if explanation["score"] < 1.0]
        # Only show the first 4 explanations
        explanations = [
            {
                "data_product": dp,
                "explanations": ", ".join(unsatisfied_justifications[i])
            } for i, dp in enumerate(unsatisfied_data_products)
        ][:5]
    else:
        unsatisfied_justifications = []

    return explanations


def get_panel_scores(design_id, designs, panel, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    this_design = find_design_by_id(designs, design_id)
    panel_scores = client.get_panel_score_explanation(eosscontext.problem_id, this_design, panel)
    # If arch scores have not been precomputed
    if panel_scores == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        panel_scores = client.get_panel_score_explanation(eosscontext.problem_id, this_design, panel)

    return panel_scores


def get_objective_scores(design_id, designs, objective, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    this_design = find_design_by_id(designs, design_id)
    objective_scores = client.get_objective_score_explanation(eosscontext.problem_id, this_design, objective.upper())
    # If arch scores have not been precomputed
    if objective_scores == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        objective_scores = client.get_objective_score_explanation(eosscontext.problem_id, this_design, objective.upper())

    return objective_scores


def get_instruments_for_objective(objective, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)
    
    instruments = client.get_instruments_for_objective(eosscontext.problem_id, objective.upper())
    return instruments


def get_instruments_for_stakeholder(stakeholder, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    stakeholder_instruments = client.get_instruments_for_panel(eosscontext.problem_id, stakeholder)
    return stakeholder_instruments


def get_instrument_parameter(vassar_instrument, instrument_parameter, context, new_dialogue_contexts):
    new_dialogue_contexts["engineer_context"].vassar_instrument = vassar_instrument
    new_dialogue_contexts["engineer_context"].instrument_parameter = instrument_parameter

    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)
    attribute_value = client.get_parameter_value_for_instrument(eosscontext.problem_id, instrument_parameter, vassar_instrument)
    capability_found = len(attribute_value) > 0

    if capability_found:
        return 'The ' + instrument_parameter + ' for ' + vassar_instrument + ' is ' + attribute_value[0]["value"]
    else:
        measurement_attribute_value = client.get_capability_value_for_instrument(eosscontext.group_id, instrument_parameter, vassar_instrument)
        capability_found = len(measurement_attribute_value) > 0
        
        if capability_found:
            return 'I have found different values for this parameter depending on the measurement. ' \
                   'Please tell me for which measurement you want this parameter: ' \
                   + ', '.join([capability["Measurement"]["name"] for capability in measurement_attribute_value])
        else:
            return 'I have not found any information for this measurement.'


def get_instrument_parameter_followup(vassar_instrument, instrument_parameter, instrument_measurement, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)
    measurement_attribute_value = client.get_capability_value_for_instrument(eosscontext.group_id, instrument_parameter, vassar_instrument, instrument_measurement)

    return 'The ' + instrument_parameter + ' for instrument ' + vassar_instrument + ' and measurement ' + \
           instrument_measurement + ' is ' + measurement_attribute_value[0]["value"]


def get_measurement_requirement(vassar_measurement, measurement_parameter, context, new_dialogue_contexts):
    new_dialogue_contexts["engineer_context"].vassar_measurement = vassar_measurement
    new_dialogue_contexts["engineer_context"].measurement_parameter = measurement_parameter

    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)
    requirements = client.get_measurement_requirements(eosscontext.problem_id, vassar_measurement, measurement_parameter)

    requirement_found = len(requirements) > 0

    if requirement_found:
        if len(requirements) > 1:
            return 'I have found different values for this requirement depending on the subobjective. ' \
                   'Please tell me for which subobjective you want this requirement: ' \
                   + ', '.join([requirement["Stakeholder_Needs_Subobjective"]["name"] for requirement in requirements])
        else:
            threshold = requirements[0]["thresholds"][-1]
            target_value = requirements[0]["thresholds"][0]
            subobjective = requirements[0]["Stakeholder_Needs_Subobjective"]["name"]
            return 'The threshold for ' + measurement_parameter + ' for ' + vassar_measurement + ' (subobjective ' + \
                   subobjective + ') is ' + threshold + ' and its target value is ' + \
                   target_value + '.'
    else:
        return 'I have not found any information for this requirement.'


def get_measurement_requirement_followup(vassar_measurement, instrument_parameter, subobjective, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)
    requirements = client.get_measurement_requirements(eosscontext.problem_id, vassar_measurement, instrument_parameter, subobjective.upper())

    threshold = requirements[0]["thresholds"][-1]
    target_value = requirements[0]["thresholds"][0]
    subobjective = requirements[0]["Stakeholder_Needs_Subobjective"]["name"]
    return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' for subobjective ' \
           + subobjective + ' is ' + threshold + ' and its target value is ' + target_value + '.'


def get_cost_explanation(design_id, designs, context):
    # Start connection with VASSAR
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    client = VASSARClient(user_information=eosscontext.user_information)

    # Get the correct architecture
    print(designs[0])
    this_design = find_design_by_id(designs, design_id)

    # Get the cost information
    cost_explanation = client.get_arch_cost_information(eosscontext.problem_id, this_design)

    # If cost information has not been precomputed
    if cost_explanation == []:
        client.reevaluate_architecture(this_design, eosscontext.vassar_request_queue_url)
        cost_explanation = client.get_arch_cost_information(eosscontext.problem_id, this_design)

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
