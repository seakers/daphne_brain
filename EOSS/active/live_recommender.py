import datetime
import json
from string import Template

from EOSS.critic.critic import Critic
from daphne_context.models import UserInformation, DialogueHistory

from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient


def active_engineer_response(user_info: UserInformation, inputs, session_key):
    vassar_client = VASSARClient(user_information=user_info)

    # Check Vassar Status
    vassar_status = vassar_client.check_status(user_info.eosscontext.vassar_request_queue_url, user_info.eosscontext.vassar_response_queue_url)
    if vassar_status != 'ready':
        print('--> INVALID VASSAR STATUS:', vassar_status)
        return []

    # Evaluate Mutated Architecture
    arch = vassar_client.evaluate_architecture(inputs, user_info.eosscontext.vassar_request_queue_url)
    arch['db_id'] = arch['id']

    # Pass evaluated arch to critic
    critic = Critic(user_info, session_key)
    suggestion_list = critic.expert_critic(arch)
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
                                   dwriter="daphne",
                                   date=datetime.datetime.utcnow())
    return message


def active_historian_response(user_info: UserInformation, inputs, session_key):
    input_str = boolean_array_2_boolean_string(inputs)
    design = {'inputs': input_str}
    critic = Critic(user_info, session_key)
    suggestion_list = critic.historian_critic(design)
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
                                   dwriter="daphne",
                                   date=datetime.datetime.utcnow())
    return message


def parse_suggestions_list(raw_list):
    parsed_list = []
    element_template = Template("<b>${type}</b>: ${advice}")
    for element in raw_list:
        parsed_list.append(element_template.substitute(element))
    return parsed_list

def boolean_array_2_boolean_string(boolean_array):
    leng = len(boolean_array)
    bool_string = ''
    for i in range(leng):
        if boolean_array[i]:
            bool_string += '1'
        else:
            bool_string += '0'
    return bool_string
