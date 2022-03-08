from dialogue.views import Command


class EDLCommand(Command):
    daphne_version = "EDL"
    command_options = ['EDL']
    condition_names = ['edl']
