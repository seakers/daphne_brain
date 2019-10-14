from daphne_context.models import UserInformation

from sqlalchemy.orm import sessionmaker
from AT.models import ECLSSAnomalies

def extract_anomaly_ids(processed_question, number_of_features, context: UserInformation):
    # Get a list of anomaly ids
    engine = ECLSSAnomalies.db_connect()
    session = sessionmaker(bind=engine)()

extract_function = {}

extract_function["anomaly_id"] = extract_anomaly_id
