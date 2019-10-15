import logging

from EOSS.critic.critic import Critic
from EOSS.models import EOSSContext
from daphne_context.models import UserInformation

logger = logging.getLogger('EOSS.critic')


def general_call(design_id, designs, context):
    eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])
    critic = Critic(eosscontext)

    try:
        this_design = None
        num_design_id = int(design_id)

        for design in designs:
            if num_design_id == design.id:
                this_design = design
                break

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))
        else:
            pass

        critic_results = []

        # Criticize architecture (based on rules)
        critic_results.extend(critic.expert_critic(this_design))

        # Criticize architecture (based on explorer)
        critic_results.extend(critic.explorer_critic(this_design))

        # Criticize architecture (based on database)
        critic_results.extend(critic.historian_critic(this_design))

        # Criticize architecture (based on data mining)
        critic_results.extend(critic.analyst_critic(this_design))

        # Send response
        return critic_results

    except Exception:
        logger.exception('Exception in criticizing the architecture')
        return None


def specific_call(design_id, agent, designs, context: UserInformation):
    critic = Critic(context)
    try:
        result = []
        result_arr = []
        num_design_id = int(design_id[1:])
        if agent == 'expert':
            # Criticize architecture (based on rules)
            result_arr = critic.expert_critic(designs[num_design_id])
        elif agent == 'historian':
            # Criticize architecture (based on database)
            result_arr = critic.historian_critic(designs[num_design_id])
        elif agent == 'analyst':
            # Criticize architecture (based on database)
            result_arr = critic.analyst_critic(designs[num_design_id])
        elif agent == 'explorer':
            # Criticize architecture (based on database)
            result_arr = critic.explorer_critic(designs[num_design_id])
        # Send response
        return result_arr

    except Exception:
        logger.exception('Exception in using a single agent to criticize the architecture')
        return None
