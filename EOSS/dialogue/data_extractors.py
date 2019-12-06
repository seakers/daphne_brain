import os

from sqlalchemy.orm import sessionmaker
import pandas

import EOSS.historian.models as earth_models
from EOSS.data import problem_specific
from EOSS.models import EOSSContext
from EOSS.vassar.api import VASSARClient
from daphne_context.models import UserInformation
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index, crop_list

sheet_file = os.path.join(os.getcwd(), "EOSS", "data", "xls", "Climate-centric", "Climate-centric AttributeSet.xls")
instruments_sheet = pandas.read_excel(sheet_file, sheet_name='Instrument')
measurements_sheet = pandas.read_excel(sheet_file, sheet_name='Measurement')
param_names = []
for row in measurements_sheet.itertuples(index=True, name='Measurement'):
    if row[2] == 'Parameter':
        for i in range(6, len(row)):
            param_names.append(row[i])


def extract_mission(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of missions
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [' ' + mission.name.strip().lower() for mission in session.query(earth_models.Mission).all()]
    return sorted_list_of_features_by_index(processed_question, missions, number_of_features)


def extract_measurement(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of measurements
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip().lower() for measurement in session.query(earth_models.Measurement).all()]
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_technology(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of technologies and types
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in earth_models.technologies]
    technologies = technologies + [type.name.strip().lower() for type in session.query(earth_models.InstrumentType).all()]
    return sorted_list_of_features_by_index(processed_question, technologies, number_of_features)


def extract_space_agency(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of technologies and types
    engine = earth_models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [' ' + agency.name.strip() for agency in session.query(earth_models.Agency).all()]
    return sorted_list_of_features_by_index(processed_question, agencies, number_of_features, case_sensitive=True)


def extract_date(processed_question, number_of_features, user_information: UserInformation):
    # For now just pick the years
    extracted_list = []
    for word in processed_question:
        if len(word) == 4 and word.like_num:
            extracted_list.append(word.text)

    return crop_list(extracted_list, number_of_features)


def extract_design_id(processed_question, number_of_features, user_information: UserInformation):
    # Get a list of design ids
    design_ids = ['d' + str(design.id) for design in user_information.eosscontext.design_set.all()]
    extracted_list = []
    for word in processed_question:
        if word.lower_ in design_ids:
            extracted_list.append(word.text)
    return crop_list(extracted_list, number_of_features)


def extract_agent(processed_question, number_of_features, user_information: UserInformation):
    agents = ["expert", "historian", "analyst", "explorer"]
    extracted_list = []
    for word in processed_question:
        if word.lower_ in agents:
            extracted_list.append(word.lower_)
    return crop_list(extracted_list, number_of_features)


def extract_instrument_parameter(processed_question, number_of_features, user_information: UserInformation):
    instrument_parameters = \
        problem_specific.get_instruments_sheet(user_information.eosscontext.problem)['Attributes-for-object-Instrument']
    return sorted_list_of_features_by_index(processed_question, instrument_parameters, number_of_features)


def extract_vassar_instrument(processed_question, number_of_features, user_information: UserInformation):
    options = [instr["name"] for instr in problem_specific.get_instrument_dataset(user_information.eosscontext.problem)]
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_measurement(processed_question, number_of_features, user_information: UserInformation):
    param_names = problem_specific.get_param_names(user_information.eosscontext.problem)
    return sorted_list_of_features_by_index(processed_question, param_names, number_of_features)


def extract_vassar_stakeholder(processed_question, number_of_features, user_information: UserInformation):
    options = problem_specific.get_stakeholders_list(user_information.eosscontext.problem)
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_objective(processed_question, number_of_features, user_information: UserInformation):
    port = user_information.eosscontext.vassar_port
    vassar_client = VASSARClient(port)
    vassar_client.start_connection()
    objectives = vassar_client.get_objective_list(user_information.eosscontext.problem)
    objectives = [objective.lower() for objective in objectives]
    vassar_client.end_connection()
    return sorted_list_of_features_by_index(processed_question, objectives, number_of_features)


def extract_vassar_subobjective(processed_question, number_of_features, user_information: UserInformation):
    port = user_information.eosscontext.vassar_port
    vassar_client = VASSARClient(port)
    vassar_client.start_connection()
    subobjectives = vassar_client.get_subobjective_list(user_information.eosscontext.problem)
    subobjectives = [subobjective.lower() for subobjective in subobjectives]
    vassar_client.end_connection()
    return sorted_list_of_features_by_index(processed_question, subobjectives, number_of_features)


extract_function = {}
extract_function["mission"] = extract_mission
extract_function["measurement"] = extract_measurement
extract_function["technology"] = extract_technology
extract_function["space_agency"] = extract_space_agency
extract_function["year"] = extract_date
extract_function["design_id"] = extract_design_id
extract_function["agent"] = extract_agent
extract_function["instrument_parameter"] = extract_instrument_parameter
extract_function["vassar_instrument"] = extract_vassar_instrument
extract_function["vassar_measurement"] = extract_vassar_measurement
extract_function["vassar_stakeholder"] = extract_vassar_stakeholder
extract_function["objective"] = extract_vassar_objective
extract_function["subobjective"] = extract_vassar_subobjective
