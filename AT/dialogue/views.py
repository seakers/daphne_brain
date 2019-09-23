from dialogue.views import Command


class ATCommand(Command):
    daphne_version = "AT"
    command_options = ['Detection', 'Diagnosis', 'Recommender']
    condition_names = ['detection', 'diagnosis', 'recommender']
