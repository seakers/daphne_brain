from AT.diagnosis import models
from daphne_context.models import UserInformation

from sqlalchemy.orm import sessionmaker
from AT.diagnosis.models import ECLSSAnomalies
from dialogue.param_extraction_helpers import sorted_list_of_features_by_index


def extract_anomaly_ids(processed_question, number_of_features, context: UserInformation):
    # Get a list of anomaly ids
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    anomaly_ids = [str(id[0]) for id in session.query(ECLSSAnomalies.id).all()]
    return sorted_list_of_features_by_index(processed_question, anomaly_ids, number_of_features)

extract_function = {}

extract_function["anomaly_id"] = extract_anomaly_ids
