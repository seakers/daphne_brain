from sqlalchemy.orm import sessionmaker

from daphne_context.models import UserInformation
from AT.diagnosis.models import ECLSSAnomalies
from AT.diagnosis import models
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index
from AT.neo4j_queries.query_functions import retrieve_all_measurements, retrieve_all_anomalies, retrieve_all_procedures, \
    retrieve_all_measurements_parameter_groups, retrieve_all_components, retrieve_all_procedure_numbers, \
    retrieve_all_step_numbers


def extract_anomaly_ids(entity_value, number_of_features, context: UserInformation):
    # Get a list of anomaly ids
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    anomaly_ids = [str(id[0]) for id in session.query(ECLSSAnomalies.id).all()]
    return sorted_list_of_features_by_index(entity_value, anomaly_ids, number_of_features)


def extract_procedures(entity_value, number_of_features, context: UserInformation):
    # Get a list of procedures
    procedures = retrieve_all_procedures()
    return sorted_list_of_features_by_index(entity_value, procedures, number_of_features)


def extract_measurements(entity_value, number_of_features, context: UserInformation):
    # Get a list of measurements
    measurements = retrieve_all_measurements()
    return sorted_list_of_features_by_index(entity_value, measurements, number_of_features)


def extract_measurements_parameter_groups(entity_value, number_of_features, context: UserInformation):
    # Get a list of measurements
    measurements = retrieve_all_measurements_parameter_groups()
    return sorted_list_of_features_by_index(entity_value, measurements, number_of_features)


def extract_anomalies(entity_value, number_of_features, context: UserInformation):
    # Get a list of anomalies
    measurements = retrieve_all_anomalies()
    return sorted_list_of_features_by_index(entity_value, measurements, number_of_features)


def extract_components(entity_value, number_of_features, context: UserInformation):
    # Get a list of components
    components = retrieve_all_components()
    return sorted_list_of_features_by_index(entity_value, components, number_of_features)


def extract_procedure_number(entity_value, number_of_features, context: UserInformation):
    # Get a list of procedure_number
    procedure_number = retrieve_all_procedure_numbers()
    return sorted_list_of_features_by_index(entity_value, procedure_number, number_of_features)


def extract_step_number(entity_value, number_of_features, context: UserInformation):
    # Get a list of procedure_number
    step_number = retrieve_all_step_numbers()
    return sorted_list_of_features_by_index(entity_value, step_number, number_of_features)


extract_function = {}

extract_function["ANOMALYID"] = extract_anomaly_ids
extract_function["PROCEDURE"] = extract_procedures
extract_function["MEASUREMENT"] = extract_measurements
extract_function["ANOMALY"] = extract_anomalies
extract_function["PARAMETERGROUP"] = extract_measurements_parameter_groups
extract_function["COMPONENT"] = extract_components
extract_function["PROCEDURENUMBER"] = extract_procedure_number
extract_function["STEPNUMBER"] = extract_step_number
