import datetime
import json
from string import Template

from EOSS.critic.critic import Critic
from EOSS.models import Design
from daphne_context.models import UserInformation, DialogueHistory


def active_engineer_response(user_info: UserInformation, inputs, session_key):
    modified_design = Design(inputs=json.dumps(inputs), outputs="[]")
    critic = Critic(user_info.eosscontext, session_key)
    suggestion_list = critic.expert_critic(modified_design)
    return suggestion_list


def generate_engineer_message(user_info, genome, session_key):
    message = {}
    if user_info.eosscontext.activecontext.show_arch_suggestions:
        suggestion_list = active_engineer_response(user_info, genome, session_key)
        if len(suggestion_list) == 0:
            return {}
        suggestion_list = parse_suggestions_list(suggestion_list)
        message = {
            'voice_message': 'The Live Recommender System has the following suggestions for your modified '
                             'architecture.',
            'visual_message_type': ['list'],
            'visual_message': [
                {
                    'begin': 'The Live Recommender System has the following suggestions for your modified '
                             'architecture: ',
                    'list': suggestion_list
                }
            ],
            "writer": "daphne",
        }
    else:
        message = {
            'voice_message': 'The Live Recommender System has some suggestions for your modified architecture, '
                             'but you have chosen to not show them. Do you want to see them now?',
            'visual_message_type': ['active_message'],
            'visual_message': [
                {
                    'message': 'The Live Recommender System has some suggestions for your modified architecture, '
                               'but you have chosen to not show them. Do you want to see them now?',
                    'setting': 'show_arch_suggestions'
                }
            ],
            "writer": "daphne",
        }
    DialogueHistory.objects.create(user_information=user_info,
                                   voice_message=message["voice_message"],
                                   visual_message_type=json.dumps(message["visual_message_type"]),
                                   visual_message=json.dumps(message["visual_message"]),
                                   writer="daphne",
                                   date=datetime.datetime.utcnow())
    return message


def active_historian_response(user_info: UserInformation, inputs, session_key):
    modified_design = Design(inputs=json.dumps(inputs), outputs="[]")
    critic = Critic(user_info.eosscontext, session_key)
    suggestion_list = critic.historian_critic(modified_design)
    return suggestion_list


def generate_historian_message(user_info, genome, session_key):
    message = {}
    if user_info.eosscontext.activecontext.show_arch_suggestions:
        suggestion_list = active_historian_response(user_info, genome, session_key)
        if len(suggestion_list) == 0:
            return {}
        suggestion_list = parse_suggestions_list(suggestion_list)
        message = {
            'voice_message': 'The Live Recommender System has the following suggestions for your modified '
                             'architecture.',
            'visual_message_type': ['list'],
            'visual_message': [
                {
                    'begin': 'The Live Recommender System has the following suggestions for your modified '
                             'architecture: ',
                    'list': suggestion_list
                }
            ],
            "writer": "daphne",
        }
    else:
       message = {
           'voice_message': 'The Live Recommender System has some suggestions for your modified architecture, '
                            'but you have chosen to not show them. Do you want to see them now?',
           'visual_message_type': ['active_message'],
           'visual_message': [
               {
                   'message': 'The Live Recommender System has some suggestions for your modified architecture, '
                              'but you have chosen to not show them. Do you want to see them now?',
                   'setting': 'show_arch_suggestions'
               }
           ],
           "writer": "daphne",
        }

    DialogueHistory.objects.create(user_information=user_info,
                                   voice_message=message["voice_message"],
                                   visual_message_type=json.dumps(message["visual_message_type"]),
                                   visual_message=json.dumps(message["visual_message"]),
                                   writer="daphne",
                                   date=datetime.datetime.utcnow())
    return message


def parse_suggestions_list(raw_list):
    parsed_list = []
    element_template = Template("<b>${type}</b>: ${advice}")
    for element in raw_list:
        parsed_list.append(element_template.substitute(element))
    return parsed_list
