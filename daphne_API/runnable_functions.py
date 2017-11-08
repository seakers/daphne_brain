import logging
from VASSAR_API.api import VASSARClient
from daphne_API.critic.critic import CRITIC

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
        logger.exception('Exception in loading objective information')
        client.endConnection()
        return None

def Critic_general_call(design_id, designs):
    client = VASSARClient()
    critic = CRITIC()

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id[1:])
        # Criticize architecture (based on rules)
        result1 = client.client.getCritique(designs[num_design_id]['inputs'])
        client.endConnection()
        result = []
        for advice in result1:
            result.append({
                "type": "Expert",
                "advice": advice
            })
        # Criticize architecture (based on database)
        result2 = critic.criticize_arch(designs[num_design_id]['inputs'])
        result.extend(result2)
        # Send response

        return result

    except Exception:
        logger.exception('Exception in loading objective information')
        client.endConnection()
        return None
