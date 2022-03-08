import os

from sqlalchemy.orm import sessionmaker
import pandas

import EOSS.historian.models as earth_models
from EOSS.data import problem_specific
from EOSS.models import EOSSContext
from EOSS.vassar.api import VASSARClient
from daphne_context.models import UserInformation
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index, crop_list


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
    vassar_client = VASSARClient(user_information=user_information)
    problem_id = user_information.eosscontext.problem_id
    dataset_id = user_information.eosscontext.dataset_id
    design_ids = ['d' + str(design["id"]) for design in vassar_client.get_dataset_architectures(problem_id, dataset_id)]
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
    vassar_client = VASSARClient(user_information=user_information)
    group_id = user_information.eosscontext.group_id
    instrument_parameters = vassar_client.dbClient.get_instrument_attributes(group_id)
    instrument_parameters = [attr["name"] for attr in instrument_parameters]
    return sorted_list_of_features_by_index(processed_question, instrument_parameters, number_of_features)


def extract_vassar_instrument(processed_question, number_of_features, user_information: UserInformation):
    problem_id = user_information.eosscontext.problem_id
    options = [instr["name"] for instr in problem_specific.get_instrument_dataset(problem_id)]
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_measurement(processed_question, number_of_features, user_information: UserInformation):
    vassar_client = VASSARClient(user_information=user_information)
    problem_id = user_information.eosscontext.problem_id
    param_names = problem_specific.get_problem_measurements(vassar_client, problem_id)
    return sorted_list_of_features_by_index(processed_question, param_names, number_of_features)


def extract_vassar_stakeholder(processed_question, number_of_features, user_information: UserInformation):
    vassar_client = VASSARClient(user_information=user_information)
    problem_id = user_information.eosscontext.problem_id
    options = problem_specific.get_stakeholders_list(vassar_client, problem_id)
    return sorted_list_of_features_by_index(processed_question, options, number_of_features)


def extract_vassar_objective(processed_question, number_of_features, user_information: UserInformation):
    vassar_client = VASSARClient(user_information=user_information)
    problem_id = user_information.eosscontext.problem_id
    objectives = problem_specific.get_objectives_list(vassar_client, problem_id)
    objectives = [objective.lower() for objective in objectives]
    return sorted_list_of_features_by_index(processed_question, objectives, number_of_features)


def extract_vassar_subobjective(processed_question, number_of_features, user_information: UserInformation):
    vassar_client = VASSARClient(user_information=user_information)
    problem_id = user_information.eosscontext.problem_id
    subobjectives = problem_specific.get_subobjectives_list(vassar_client, problem_id)
    subobjectives = [subobjective.lower() for subobjective in subobjectives]
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
