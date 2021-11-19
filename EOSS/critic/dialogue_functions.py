import logging
import concurrent.futures

from EOSS.critic.critic import Critic
from EOSS.models import EOSSContext

logger = logging.getLogger('EOSS.critic')


def general_call(design_id, designs, session_key, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    critic = Critic(eosscontext.user_information, session_key)
    print("Critizing arch ", design_id,"in",designs)

    try:
        this_design = find_design_by_id(designs, design_id)

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))

        critic_results = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Criticize architecture (based on rules)
            expert_results = executor.submit(critic.expert_critic, this_design)
            # Criticize architecture (based on explorer)
            explorer_results = executor.submit(critic.explorer_critic, this_design)
            # Criticize architecture (based on database)
            # TODO: Fix issues with new Database system matching the inputs to historian (NLP work)
            # historian_results = executor.submit(critic.historian_critic, this_design)
            # Criticize architecture (based on data mining)
            analyst_results = executor.submit(critic.analyst_critic, this_design)

            critic_results.extend(expert_results.result())
            critic_results.extend(explorer_results.result())
            #critic_results.extend(historian_results.result())
            critic_results.extend(analyst_results.result())

        # Send response
        return critic_results

    except Exception:
        logger.exception('Exception in criticizing the architecture')
        return None


def find_design_by_id(design_set, design_id):
    for design in design_set:
        if design["id"] == design_id:
            return design


def specific_call(design_id, agent, designs, session_key, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    critic = Critic(eosscontext, session_key)
    try:
        result = []
        result_arr = []

        this_design = designs.get(id=design_id)

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))

        if agent == 'expert':
            # Criticize architecture (based on rules)
            result_arr = critic.expert_critic(this_design)
        elif agent == 'historian':
            # Criticize architecture (based on database)
            result_arr = critic.historian_critic(this_design)
        elif agent == 'analyst':
            # Criticize architecture (based on database)
            result_arr = critic.analyst_critic(this_design)
        elif agent == 'explorer':
            # Criticize architecture (based on database)
            result_arr = critic.explorer_critic(this_design)
        # Send response
        return result_arr

    except Exception:
        logger.exception('Exception in using a single agent to criticize the architecture')
        return None
