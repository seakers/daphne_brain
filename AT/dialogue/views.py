from dialogue.views import Command


class ATCommand(Command):
    daphne_version = "AT"
    command_options = ['Detection', 'Diagnosis', 'Recommendation']
    condition_names = ['detection', 'diagnosis', 'recommandation']
