import pandas
from string import ascii_uppercase

from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
'''
    Because this functionality is hardcoded, it is not compatible with daphne's new aws architecture. The current issue
    specifically being addressed in these changes is the fluid ordering of both satellites and instruments in the aws
    architecture implementation.
'''

def get_orbit_dataset(problem_id):
    dbClient = GraphqlClient()
    orbit_info = dbClient.get_orbits_and_attributes(problem_id)
    dataset = []
    counter = 0
    for orb_obj in orbit_info:
        orbit = orb_obj['orbit']
        counter += 1
        orb_dict = {}
        orb_dict['alias'] = str(counter * 1000)
        orb_dict['name'] = orbit['name']
        for attribute in orbit['attributes']:
            if attribute['Orbit_Attribute']['name'] == 'type':
                orb_dict['type'] = attribute['value']
            elif attribute['Orbit_Attribute']['name'] == 'altitude':
                orb_dict['altitude'] = attribute['value']
            elif attribute['Orbit_Attribute']['name'] == 'RAAN#':
                orb_dict['LST'] = attribute['value']
        dataset.append(orb_dict)
    return dataset


def get_orbits_info(vassar_client: VASSARClient, problem_id: int):
    orbit_names = vassar_client.get_orbit_list(problem_id)
    orbit_infos = generate_orbit_info_from_names(orbit_names)
    orbit_infos.insert(0, "<b>Orbit name: Orbit information</b>")
    return orbit_infos

def generate_orbit_info_from_names(orbit_names):
    return [f"{orbit_name}: {create_orbit_info(orbit_name)}" for orbit_name in orbit_names]

def create_orbit_info(orbit_name):
    text_orbit = ""
    orbit_type_codes = {
        "GEO": "Geostationary",
        "LEO": "Low Earth",
        "HEO": "Highly Elliptical",
        "SSO": "Low Earth, Sun-Synchronous",
    }
    orbit_inclination_codes = {
        "equat": "Equatorial",
        "near-equat": "Near Equatorial",
        "mid-lat": "Mid Latitude",
        "near-polar": "Near Polar",
        "polar": "Polar",
    }
    orbit_ltan_codes = {
        "DD": "Dawn-Dusk",
        "AM": "Morning",
        "noon": "Noon",
        "PM": "Afternoon",
    }
    
    orbit_parts = orbit_name.split('-')
    text_orbit = ""

    # Orbit type
    text_orbit += orbit_type_codes[orbit_parts[0]] + ", "

    # Orbit altitude
    orbit_altitude_num = int(orbit_parts[1])
    if orbit_altitude_num < 400:
        text_orbit += "Very Low "
    elif orbit_altitude_num < 550:
        text_orbit += "Low "
    elif orbit_altitude_num < 700:
        text_orbit += "Medium "
    elif orbit_altitude_num < 850:
        text_orbit += "High "
    else:
        text_orbit += "Very High "
    text_orbit += f"Altitude ({orbit_altitude_num} km), "

    # Orbit inclination / LTAN
    orbit_inclination = orbit_parts[2]
    if orbit_inclination != "SSO":
        text_orbit += f"{orbit_inclination_codes[orbit_inclination]}"
    else:
        orbit_ltan = orbit_parts[3]
        text_orbit += f"{orbit_ltan_codes[orbit_ltan]}"

    return text_orbit


def get_instrument_dataset(problem_id):
    dbClient = GraphqlClient()
    instrument_info = dbClient.get_instruments_and_attributes(problem_id)
    dataset = []
    counter = 0
    for inst_obj in instrument_info:
        instrument = inst_obj['instrument']
        inst_dict = {}
        inst_dict['alias'] = ascii_uppercase[counter]
        inst_dict['name'] = instrument['name']
        for attribute in instrument['attributes']:
            if attribute['Instrument_Attribute']['name'] == 'Concept':
                inst_dict['type'] = attribute['value']
            elif attribute['Instrument_Attribute']['name'] == 'Intent':
                inst_dict['technology'] = attribute['value']
            elif attribute['Instrument_Attribute']['name'] == 'Geometry':
                inst_dict['geometry'] = attribute['value']
            elif attribute['Instrument_Attribute']['name'] == 'spectral-bands':
                inst_dict['wavebands'] = [attribute['value']]
        dataset.append(inst_dict)
        counter += 1
    return dataset


def get_instruments_info(vassar_client: VASSARClient, problem_id: int):
    instruments_data = get_instrument_dataset(problem_id)
    instrument_infos = ["<b>Instrument name: Instrument type, Instrument technology, Geometry, Bands</b>"]
    for instrument_data in instruments_data:
        instrument_info = ""
        instrument_info += f'{instrument_data["name"]}: '
        instrument_info += f'{instrument_data["type"]}, '
        instrument_info += f'{instrument_data["technology"]}, '
        instrument_info += f'{instrument_data["geometry"]}, '
        instrument_info += f'{"/".join(instrument_data["wavebands"])}'
        instrument_infos.append(instrument_info)
    return instrument_infos


def get_instruments_parameters(vassar_client: VASSARClient, group_id: int):
    instruments_parameters = vassar_client.dbClient.get_instrument_attributes(group_id)
    return [attr["name"] for attr in instruments_parameters]


def get_problem_measurements(vassar_client: VASSARClient, problem_id: int):
    problem_measurements = vassar_client.dbClient.get_problem_measurements(problem_id)
    return [meas["Measurement"]["name"] for meas in problem_measurements]


def get_stakeholders_list(vassar_client: VASSARClient, problem_id: int):
    stakeholders = vassar_client.dbClient.get_stakeholders_list(problem_id)
    return [stakeholder["name"] for stakeholder in stakeholders]


def get_objectives_list(vassar_client: VASSARClient, problem_id: int):
    objectives = vassar_client.dbClient.get_objectives_list(problem_id)
    return [objective["name"] for objective in objectives]


def get_subobjectives_list(vassar_client: VASSARClient, problem_id: int):
    subobjectives = vassar_client.dbClient.get_subobjectives_list(problem_id)
    return [subobjective["name"] for subobjective in subobjectives]





# TODO: Remove all usage of these functions from code
cc_capabilities_sheet = pandas.read_excel('EOSS/data/problems/ClimateCentric/xls/Instrument Capability Definition.xls',
                                       sheet_name='CHARACTERISTICS')
smap_capabilities_sheet = pandas.read_excel('EOSS/data/problems/SMAP/xls/Instrument Capability Definition.xls', sheet_name='CHARACTERISTICS')
def get_capabilities_sheet(problem):
    if problem == "ClimateCentric":
        return cc_capabilities_sheet
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_capabilities_sheet

cc_instrument_sheet = lambda vassar_instrument: pandas.read_excel('EOSS/data/problems/ClimateCentric/xls/Instrument Capability Definition.xls',
                                        sheet_name=vassar_instrument, header=None)
smap_instrument_sheet = lambda vassar_instrument: pandas.read_excel('EOSS/data/problems/SMAP/xls/Instrument Capability Definition.xls', sheet_name=vassar_instrument, header=None)
def get_instrument_sheet(problem, instrument):
    if problem == "ClimateCentric":
        return cc_instrument_sheet(instrument)
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_instrument_sheet(instrument)

cc_requirements_sheet = pandas.read_excel('EOSS/data/problems/ClimateCentric/xls/Requirement Rules.xls',
                                           sheet_name='Attributes')
smap_requirements_sheet = pandas.read_excel('EOSS/data/problems/SMAP/xls/Requirement Rules.xls', sheet_name='Attributes')
def get_requirements_sheet(problem):
    if problem == "ClimateCentric":
        return cc_requirements_sheet
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_requirements_sheet
