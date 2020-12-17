from sqlalchemy.orm import sessionmaker

from daphne_context.models import UserInformation
from AT.diagnosis.models import ECLSSAnomalies
from AT.diagnosis import models
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index
from AT.neo4j_queries.query_functions import retrieve_all_measurements, retrieve_all_anomalies, retrieve_all_procedures, \
    retrieve_all_measurements_parameter_groups, retrieve_all_components


def extract_anomaly_ids(processed_question, number_of_features, context: UserInformation):
    # Get a list of anomaly ids
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    anomaly_ids = [str(id[0]) for id in session.query(ECLSSAnomalies.id).all()]
    return sorted_list_of_features_by_index(processed_question, anomaly_ids, number_of_features)


def extract_procedures(processed_question, number_of_features, context: UserInformation):
    # Get a list of procedures
    procedures = retrieve_all_procedures()
    return sorted_list_of_features_by_index(processed_question, procedures, number_of_features)


def extract_measurements(processed_question, number_of_features, context: UserInformation):
    # Get a list of measurements
    measurements = retrieve_all_measurements()
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_measurements_parameter_groups(processed_question, number_of_features, context: UserInformation):
    # Get a list of measurements
    measurements = retrieve_all_measurements_parameter_groups()
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)


def extract_anomalies(processed_question, number_of_features, context: UserInformation):
    # Get a list of anomalies
    measurements = retrieve_all_anomalies()
    return sorted_list_of_features_by_index(processed_question, measurements, number_of_features)

def extract_components(processed_question, number_of_features, context: UserInformation):
    # Get a list of components
    components = retrieve_all_components()
    return sorted_list_of_features_by_index(processed_question, components, number_of_features)

extract_function = {}

extract_function["anomaly_id"] = extract_anomaly_ids
extract_function["procedure"] = extract_procedures
extract_function["measurement"] = extract_measurements
extract_function["anomaly"] = extract_anomalies
extract_function["parameter_group"] = extract_measurements_parameter_groups
extract_function["component"] = extract_components

