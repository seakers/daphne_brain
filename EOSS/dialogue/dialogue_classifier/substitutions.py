# from  EOSS.dialogue.dialogue_classifier.db_client import Client, technologies
from EOSS.dialogue.dialogue_classifier.db_client import Client, technologies

def load_data_sources():
    substitutions = dict()
    # Connect to the database to retrieve names
    postgres_client = Client()

    return {
        "db_client": postgres_client,
        "technologies": technologies
    }

def substitution_functions():
    # Define template substitutions depending on the type
    substitutions = dict()
    def subs_measurement(data_sources):
        measurements = data_sources["db_client"].get_measurements()
        return measurements
    substitutions['measurement'] = subs_measurement

    def subs_technology(data_sources):
        technologies = list(data_sources["technologies"])
        for tech_type in data_sources["db_client"].get_instrument_types():
            technologies.append(tech_type)
        return technologies
    substitutions['technology'] = subs_technology

    def subs_mission(data_sources):
        missions = data_sources["db_client"].get_missions()
        return missions
    substitutions['mission'] = subs_mission

    def subs_agency(data_sources):
        agencies = data_sources["db_client"].get_agencies()
        return agencies
    substitutions['space_agency'] = subs_agency

    def subs_instrument_ifeed(data_sources):
        options = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'j', 'k', 'l']
        return options
    substitutions['instrument'] = subs_instrument_ifeed

    def subs_year(data_sources):
        # return list(range(1965, 2055))
        return "Extract 4-digit years (e.g., 1965, 2025)."
    substitutions['year'] = subs_year

    def subs_design_id(data_sources):
        # return ["D" + str(i) for i in range(500, 550)]
        return '''
    Extract a number with the followig rules: If the user mentions a number like "1789", or "567" or "D345" format it as "D1789", "D567", "D345" respectively. Always include the "D" prefix.
    '''
    substitutions['design_id'] = subs_design_id

    def subs_objective(data_sources):
        objectives = data_sources["db_client"].get_objectives()
        if objectives:
            return objectives
        else:
            return "No objectives available"
    substitutions['objective'] = subs_objective

    def subs_subobjective(data_sources):
        subobjectives = data_sources["db_client"].get_subobjectives()
        if subobjectives:
            return subobjectives
        else:
            return "No subobjectives available"  # Or some other default value
    substitutions['subobjective'] = subs_subobjective

    def subs_not_partial_full(data_sources):
        options = ["not", "partially", "fully"]
        return options
    substitutions['not_partial_full'] = subs_not_partial_full

    def subs_agent(data_sources):
        options = ["expert", "historian", "analyst", "explorer", "engineer", "critic"]
        return options
    substitutions['agent'] = subs_agent

    def subs_orbit(data_sources):
        return list(range(1, 5))
    substitutions['orbit'] = subs_orbit

    def subs_number(data_sources):
        return list(range(1, 8))
    substitutions['number'] = subs_number

    def subs_instrument_parameter(data_sources):
        instrument_parameters = data_sources["db_client"].get_instrument_attributes()
        if instrument_parameters:
            return instrument_parameters
        else:
            return "No objectives available" 
    substitutions['instrument_parameter'] = subs_instrument_parameter

    def subs_vassar_instrument(data_sources):
        vassar_instruments = data_sources["db_client"].get_vassar_instruments()
        return vassar_instruments
    substitutions['vassar_instrument'] = subs_vassar_instrument

    def subs_vassar_measurement(data_sources):
        vassar_measurements = data_sources["db_client"].get_vassar_measurements()
        return vassar_measurements
    substitutions['vassar_measurement'] = subs_vassar_measurement

    def subs_vassar_stakeholder(data_sources):
        stakeholders = data_sources["db_client"].get_stakeholders()
        if stakeholders:
            return stakeholders
        else:
            return "No stakeholders available" 
    substitutions['vassar_stakeholder'] = subs_vassar_stakeholder

    return substitutions