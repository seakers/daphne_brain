import json
import logging

from EOSS.vassar.api import VASSARClient
from daphne_API import problem_specific
from dialogue.models import UserInformation

logger = logging.getLogger('VASSAR')


def get_architecture_scores(design_id, designs, context: UserInformation):
    port = context.eosscontext.vassar_port
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        num_design_id = int(design_id)
        scores = client.client.getArchitectureScoreExplanation(context.eosscontext.problem,
                                                                   json.loads(designs[num_design_id].inputs))

        # End the connection before return statement
        client.end_connection()
        return scores

    except Exception:
        logger.exception('Exception in loading architecture score information')
        client.end_connection()
        return None


def get_panel_scores(design_id, designs, panel, context: UserInformation):
    port = context.eosscontext.vassar_port
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        num_design_id = int(design_id)
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
        panel_scores = client.client.getPanelScoreExplanation(context.eosscontext.problem,
                                                              json.loads(designs[num_design_id].inputs),
                                                              panel_code)

        # End the connection before return statement
        client.end_connection()
        return panel_scores

    except Exception:
        logger.exception('Exception in loading panel score information')
        client.end_connection()
        return None


def get_objective_scores(design_id, designs, objective, context: UserInformation):
    port = context.eosscontext.vassar_port
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        num_design_id = int(design_id)
        objective_scores = client.client.getObjectiveScoreExplanation(context.eosscontext.problem,
                                                                      json.loads(designs[num_design_id].inputs),
                                                                      objective)

        # End the connection before return statement
        client.end_connection()
        return objective_scores

    except Exception:
        logger.exception('Exception in loading objective score information')
        client.end_connection()
        return None


def get_instruments_for_objective(objective, context: UserInformation):
    port = context.eosscontext.vassar_port
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.start_connection()
        instruments = client.client.getInstrumentsForObjective(context.eosscontext.problem, objective)

        # End the connection before return statement
        client.end_connection()
        return instruments

    except Exception:
        logger.exception('Exception in loading related instruments to an objective')
        client.end_connection()
        return None


def get_instruments_for_stakeholder(stakeholder, context: UserInformation):
    port = context.eosscontext.vassar_port
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
        stakeholder_instruments = client.client.getInstrumentsForPanel(context.eosscontext.problem, panel_code)

        # End the connection before return statement
        client.end_connection()
        return stakeholder_instruments

    except Exception:
        logger.exception('Exception in loading related instruments to a panel')
        client.end_connection()
        return None


def get_instrument_parameter(vassar_instrument, instrument_parameter, context: UserInformation):
    context.eosscontext.engineercontext.vassar_instrument = vassar_instrument
    context.eosscontext.engineercontext.instrument_parameter = instrument_parameter
    context.eosscontext.engineercontext.save()
    context.save()

    capabilities_sheet = problem_specific.get_capabilities_sheet(context.eosscontext.problem)
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
        instrument_sheet = problem_specific.get_instrument_sheet(context.eosscontext.problem, vassar_instrument)

        for i in range(2, len(instrument_sheet.columns)):
            if instrument_sheet[i][0].split()[0] == instrument_parameter:
                capability_found = True
        if capability_found:
            return 'I have found different values for this parameter depending on the measurement. ' \
                   'Please tell me for which measurement you want this parameter: ' \
                   + ', '.join([measurement[11:-1] for measurement in instrument_sheet[1]])
        else:
            return 'I have not found any information for this measurement.'


def get_instrument_parameter_followup(vassar_instrument, instrument_parameter, instrument_measurement, context: UserInformation):
    instrument_sheet = problem_specific.get_instrument_sheet(context.eosscontext.problem, vassar_instrument)

    capability_value = None
    for row in instrument_sheet.itertuples(index=True, name='Measurement'):
        if row[2][11:-1] == instrument_measurement:
            for i in range(3, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_value = row[i].split()[1]

    return 'The ' + instrument_parameter + ' for instrument ' + vassar_instrument + ' and measurement ' + \
           instrument_measurement + ' is ' + capability_value


def get_measurement_requirement(vassar_measurement, instrument_parameter, context: UserInformation):
    context.eosscontext.engineercontext.vassar_measurement = vassar_measurement
    context.eosscontext.engineercontext.instrument_parameter = instrument_parameter
    context.eosscontext.engineercontext.save()
    context.save()

    requirements_sheet = problem_specific.get_requirements_sheet(context.eosscontext.problem)
    requirement_found = False
    requirements = []
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement_found = True
            requirements.append({"stakeholder": row[1], "type": row[4], "thresholds": row[5]})

    if requirement_found:
        if len(requirements) > 1:
            stakeholders_to_human = {
                "ATM": "Atmospheric",
                "OCE": "Oceanic",
                "TER": "Terrestrial",
                "WEA": "weather",
                "CLI": "climate",
                "ECO": "land and ecosystems",
                "WAT": "water",
                "HEA": "human health"
            }
            return 'I have found different values for this requirement depending on the stakeholder. ' \
                   'Please tell me for which stakeholder you want this requirement: ' \
                   + ', '.join([stakeholders_to_human[requirement["stakeholder"][0:3]] for requirement in requirements])
        else:
            threshold = requirements[0]["thresholds"][1:-1].split(',')[-1]
            target_value = requirements[0]["thresholds"][1:-1].split(',')[0]
            return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' (subojective ' + \
                   requirements[0]["stakeholder"] + ') is ' + threshold + ' and its target value is ' + \
                   target_value + '.'
    else:
        return 'I have not found any information for this requirement.'


def get_measurement_requirement_followup(vassar_measurement, instrument_parameter, stakeholder, context: UserInformation):
    requirements_sheet = problem_specific.get_requirements_sheet(context.eosscontext.problem)
    stakeholders_to_excel = {
        "Atmospheric": "ATM",
        "Oceanic": "OCE",
        "Terrestrial": "TER",
        "Weather": "WEA",
        "Climate": "CLI",
        "Land and ecosystems": "ECO",
        "Water": "WAT",
        "Human health": "HEA"
    }
    requirement = None
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[1][0:3] == stakeholders_to_excel[stakeholder] and row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement = {"stakeholder": row[1], "type": row[4], "thresholds": row[5]}

    threshold = requirement["thresholds"][1:-1].split(',')[-1]
    target_value = requirement["thresholds"][1:-1].split(',')[0]
    return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' for panel ' \
           + requirement["stakeholder"] + ' is ' + threshold + ' and its target value is ' + target_value + '.'
