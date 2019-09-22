import logging

from EOSS.analyst.helpers import feature_expression_to_string
from EOSS.data_mining.api import DataMiningClient

logger = logging.getLogger('EOSS.analyst')


def data_mining_run(designs, behavioral, non_behavioral, context):
    client = DataMiningClient()
    try:
        # Start connection with data_mining
        client.startConnection()

        support_threshold = 0.002
        confidence_threshold = 0.2
        lift_threshold = 1

        # features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
        features = client.runAutomatedLocalSearch(behavioral, non_behavioral, designs, support_threshold,
                                                  confidence_threshold, lift_threshold)

        # End the connection before return statement
        client.endConnection()

        result = []
        max_features = 3
        if len(features) > 3:
            pass
        else:
            max_features = len(features)

        for i in range(max_features):  # Generate answers for the first 3 features
            advice = feature_expression_to_string(features[i]['name'], context)
            result.append({
                "type": "Analyzer",
                "advice": advice
            })
        return result

    except Exception:
        logger.exception('Exception in running data mining')
        client.endConnection()
        return None