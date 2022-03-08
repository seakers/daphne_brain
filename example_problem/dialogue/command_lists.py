from django.conf import settings


general_commands = [
    ('0000', 'Stop')
]

engineer_commands = [
]

analyst_commands = [
    ('1000', 'What are the driving features?'),
]

explorer_commands = [
]

historian_commands = [
]

critic_commands = [
    ('3000', 'What do you think of design ${design_id}?'),
    #'What does agent ${agent} think of design ${design_id}?'
]


def commands_list(command_list, restricted_list=None):
    if restricted_list is not None:
        return [command[1] for command in command_list if command[0] in restricted_list]
    else:
        return [command[1] for command in command_list]


def general_commands_list(restricted_list=None):
    return commands_list(general_commands, restricted_list)


def engineer_commands_list(restricted_list=None):
    return commands_list(engineer_commands, restricted_list)


def analyst_commands_list(restricted_list=None):
    return commands_list(analyst_commands, restricted_list)


def explorer_commands_list(restricted_list=None):
    return commands_list(explorer_commands, restricted_list)


def historian_commands_list(restricted_list=None):
    return commands_list(historian_commands, restricted_list)


def critic_commands_list(restricted_list=None):
    return commands_list(critic_commands, restricted_list)
