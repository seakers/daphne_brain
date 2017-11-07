import logging
from VASSAR_API.api import VASSARClient

logger = logging.getLogger('VASSAR')

def VASSAR_load_objectives_information(design_id, designs):
    client = VASSARClient()

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id[1:])
        list = client.client.getScoreExplanation(designs[num_design_id]['inputs'])

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in getting the orbit list')
        client.endConnection()
        return None