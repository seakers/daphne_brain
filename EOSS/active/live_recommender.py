import datetime
import json
import math
from string import Template
import sys
import traceback
import random

from asgiref.sync import async_to_sync
from EOSS.analyst.helpers import feature_expression_to_string

from EOSS.critic.critic import Critic
from EOSS.data_mining.api import DataMiningClient
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture
from daphne_context.models import UserInformation, DialogueHistory

from EOSS.vassar.api import VASSARClient


def active_engineer_response(user_info: UserInformation, inputs, session_key):
    vassar_client = VASSARClient(user_information=user_info)

    # Check Vassar Status
    vassar_status = async_to_sync(vassar_client.check_status)(user_info.eosscontext.vassar_request_queue_url, user_info.eosscontext.vassar_response_queue_url)
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


def generate_engineer_message(user_info: UserInformation, genome, session_key):
    message = {}
    if user_info.eosscontext.activecontext.show_engineer_suggestions:
        suggestion_list = active_engineer_response(user_info, genome, session_key)
        if len(suggestion_list) == 0:
            return {}
        suggestion_list = parse_suggestions_list(suggestion_list)
        message = {
            'voice_message': 'The Engineer has the following suggestions for your modified '
                             'architecture.',
            'visual_message_type': ['list'],
            'visual_message': [
                {
                    'begin': 'The Engineer has the following suggestions for your modified '
                             'architecture: ',
                    'list': suggestion_list
                }
            ],
            "writer": "daphne",
        }
    else:
        message = {
            'voice_message': 'The Engineer has some suggestions for your modified architecture, '
                             'but you have chosen to not show them. Do you want to see them now?',
            'visual_message_type': ['active_message'],
            'visual_message': [
                {
                    'message': 'The Engineer has some suggestions for your modified architecture, '
                               'but you have chosen to not show them. Do you want to see them now?',
                    'setting': 'show_engineer_suggestions'
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


def generate_historian_message(user_info: UserInformation, genome, session_key):
    message = {}
    if user_info.eosscontext.activecontext.show_historian_suggestions:
        suggestion_list = active_historian_response(user_info, genome, session_key)
        if len(suggestion_list) == 0:
            return {}
        suggestion_list = parse_suggestions_list(suggestion_list)
        message = {
            'voice_message': 'The Historian has the following suggestions for your modified '
                             'architecture.',
            'visual_message_type': ['list'],
            'visual_message': [
                {
                    'begin': 'The Historian has the following suggestions for your modified '
                             'architecture: ',
                    'list': suggestion_list
                }
            ],
            "writer": "daphne",
        }
    else:
        message = {
           'voice_message': 'The Historian has some suggestions for your modified architecture, '
                            'but you have chosen to not show them. Do you want to see them now?',
           'visual_message_type': ['active_message'],
           'visual_message': [
               {
                   'message': 'The Historian has some suggestions for your modified architecture, '
                              'but you have chosen to not show them. Do you want to see them now?',
                   'setting': 'show_historian_suggestions'
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


def active_analyst_response(user_info: UserInformation, session_key):
    result = []
    dm_client = DataMiningClient()
    vassar_client = VASSARClient(user_information=user_info)

    problem_id = user_info.eosscontext.problem_id
    problem_type = vassar_client.get_problem_type(problem_id)

    try:
        # Start connection with data_mining
        dm_client.startConnection()

        behavioral = []
        non_behavioral = []

        dataset = vassar_client.get_dataset_architectures(problem_id, user_info.eosscontext.dataset_id)

        if len(dataset) < 10:
            raise ValueError("Could not run data mining: the number of samples is less than 10")
        else:
            utopiaPoint = [1, 0]
            temp = []
            maxObjectives = [0, 0]
            # Find the maximum values of all objectives for normalization
            for design in dataset:
                outputs = design["outputs"]
                for index, output in enumerate(outputs):
                    maxObjectives[index] = max(maxObjectives[index], output)
            # Select the top N% archs based on the distance to the utopia point
            for design in dataset:
                outputs = design["outputs"]
                id = design["id"]
                dist = math.sqrt(((outputs[0] - utopiaPoint[0])/(maxObjectives[0] - utopiaPoint[0])) ** 2 + ((outputs[1] - utopiaPoint[1])/(maxObjectives[1] - utopiaPoint[1])) ** 2)
                temp.append((id, dist))

            # Sort the list based on the distance to the utopia point
            temp = sorted(temp, key=lambda x: x[1])
            for i in range(len(temp)):
                if i <= len(temp) // 10:  # Label the top 10% architectures as behavioral
                    behavioral.append(temp[i][0])
                else:
                    non_behavioral.append(temp[i][0])

        # Extract feature
        _archs = []
        if problem_type == "assignation":
            for arch in dataset:
                _archs.append(BinaryInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
            _features = dm_client.client.getDrivingFeaturesEpsilonMOEABinary(session_key, problem_id, problem_type, 
                                                                                behavioral, non_behavioral, _archs)

        elif problem_type == "discrete":
            for arch in dataset:
                _archs.append(DiscreteInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
            _features = dm_client.client.getDrivingFeaturesEpsilonMOEADiscrete(session_key, problem_id, problem_type,
                                                                                behavioral, non_behavioral, _archs)
        else:
            raise ValueError("Problem type not implemented")


        features = []
        for df in _features:
            features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics, 'complexity': df.complexity})

        # Bias features by complexity and generality
        features.sort(key=lambda f: f["metrics"][0], reverse=True) # Sort features by their support (how many archs have it)
        features.sort(key=lambda f: f["complexity"]) # And then by how simple they are

        advices = []
        for feature in features:
            if feature["expression"] == "":
                continue
            advices.append(feature_expression_to_string(feature["expression"], is_critique=False, context=user_info.eosscontext))

        # End the connection before return statement
        dm_client.endConnection()

        for i in range(len(advices)):
            advice = advices[i]
            result.append({
                "type": "Analyst",
                "advice": advice
            })
    except Exception as e:
        print("Exc in generating critic from data mining: " + str(e))
        traceback.print_exc(file=sys.stdout)
        dm_client.endConnection()

    return result


def generate_analyst_message(user_info: UserInformation, session_key):
    message = {}
    if user_info.eosscontext.activecontext.show_analyst_suggestions:
        features_list = active_analyst_response(user_info, session_key)[:20]
        random.shuffle(features_list)
        features_list = features_list[:3]
        if len(features_list) == 0:
            return {}
        features_list = [feature["advice"] for feature in features_list]
        message = {
            'voice_message': 'According to the Analyst, designs on the Pareto front consistently show these features.',
            'visual_message_type': ['list'],
            'visual_message': [
                {
                    'begin': 'According to the Analyst, designs on the Pareto front consistently show these features:',
                    'list': features_list
                }
            ],
            "writer": "daphne",
        }
    else:
        message = {
           'voice_message': 'The Analyst has some suggestions for your modified architecture, '
                            'but you have chosen to not show them. Do you want to see them now?',
           'visual_message_type': ['active_message'],
           'visual_message': [
               {
                   'message': 'The Analyst has some suggestions for your modified architecture, '
                              'but you have chosen to not show them. Do you want to see them now?',
                   'setting': 'show_analyst_suggestions'
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
