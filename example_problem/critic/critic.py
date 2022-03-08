from example_problem.models import ExampleContext


class Critic:
    def __init__(self, context: ExampleContext, session_key):
        # Connect to the CEOS database
        self.context = context
        self.session_key = session_key

    def expert_critic(self, design):
        # Criticize architecture (based on rules)
        pass

    def explorer_critic(self, design):
        pass

    def historian_critic(self, design):
        pass

    def analyst_critic(self, design):
        pass