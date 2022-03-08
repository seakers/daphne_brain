from example_problem.critic.critic import Critic
from example_problem.models import ExampleContext


def general_call(design_id, designs, session_key, context):
    examplecontext = ExampleContext.objects.get(id=context["screen"]["id"])
    critic = Critic(examplecontext, session_key)

    try:
        this_design = designs.get(id=design_id)

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))

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
        return None


def specific_call(design_id, agent, designs, session_key, context):
    examplecontext = ExampleContext.objects.get(id=context["screen"]["id"])
    critic = Critic(examplecontext, session_key)
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
        return None
