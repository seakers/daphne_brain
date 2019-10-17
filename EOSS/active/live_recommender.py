import json
from string import Template

from EOSS.critic.critic import Critic
from EOSS.models import Design
from daphne_context.models import UserInformation


def active_engineer_response(user_info: UserInformation, inputs, session_key):
    modified_design = Design(inputs=json.dumps(inputs), outputs="[]")
    critic = Critic(user_info.eosscontext, session_key)
    suggestion_list = critic.expert_critic(modified_design)
    return suggestion_list


def active_historian_response(user_info: UserInformation, inputs, session_key):
    modified_design = Design(inputs=json.dumps(inputs), outputs="[]")
    critic = Critic(user_info.eosscontext, session_key)
    suggestion_list = critic.historian_critic(modified_design)
    return suggestion_list


def parse_suggestions_list(raw_list):
    parsed_list = []
    element_template = Template("<b>${type}</b>: ${advice}")
    for element in raw_list:
        parsed_list.append(element_template.substitute(element))
    return parsed_list
