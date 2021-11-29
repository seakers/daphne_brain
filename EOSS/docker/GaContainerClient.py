import docker
import threading
import random
import copy
import string

from EOSS.docker.AbstractContainerClient import AbstractContainerClient
from EOSS.docker.helpers import get_or_create_queue, create_or_purge_queue
from EOSS.aws.utils import get_boto3_client






class GaContainerClient(AbstractContainerClient):
    def __init__(self, user_info, container=None):
        super().__init__(user_info, container)

        # --> Read container data
        self.container_type = 'ga'

        # --> Initialize container
        self.initialize()

    def shutdown(self):
        self._shutdown()

    """
           _____             __ _       
          / ____|           / _(_)      
         | |     ___  _ __ | |_ _  __ _ 
         | |    / _ \| '_ \|  _| |/ _` |
         | |___| (_) | | | | | | | (_| |
          \_____\___/|_| |_|_| |_|\__, |
                                   __/ |
                                  |___/ 
    """

    @property
    def container_config(self):
        return {
            'image': 'vassar:ga_experiment',
            'network': 'daphne_service',
            'detach': True,
            'labels': self.labels,
            'environment': {
                # --> QUEUE URLS
                'GA_REQUEST_URL': self.private_request_queue,
                'GA_RESPONSE_URL': self.private_response_queue,
                'PING_REQUEST_QUEUE': self.ping_request_queue,
                'PING_RESPONSE_QUEUE': self.ping_response_queue,
                'VASSAR_REQUEST_URL': self.eval_request_queue,
                'VASSAR_RESPONSE_URL': self.eval_response_queue,

                # --> SERVICE ADDRESSES
                'APOLLO_URL': 'http://172.12.0.13:8080/v1/graphql',
                'APOLLO_URL_WS': 'ws://172.12.0.13:8080/v1/graphql',
                'AWS_STACK_ENDPOINT': 'http://172.12.0.5:9324',

                # --> AWS CONFIGURATION
                'AWS_ACCESS_KEY_ID': 'AKIAJVM34C5MCCWRJCCQ',
                'AWS_SECRET_ACCESS_KEY': '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',
                'REGION': 'elasticmq',

                # --> OTHER
                'DEPLOYMENT_TYPE': 'local',
                'MESSAGE_RETRIEVAL_SIZE': '3',
                'MESSAGE_QUERY_TIMEOUT': '5'
            },
            'name': str('user-' + str(self.user_info.user.id) + '-container-' + self.identifier),
            'mem_limit': '2g',
            'cpu_period': 10000,
            'cpu_quota': 10000,
            # 'entrypoint': 'gradle run'
        }

    @property
    def labels(self):
        return {
            'USER_ID': str(self.user_info.user.id),
            'TYPE': str(self.container_type),
            'PRIVATE_REQUEST_QUEUE': self.private_request_queue,
            'PRIVATE_RESPONSE_QUEUE': self.private_response_queue,
            'PING_REQUEST_QUEUE': self.ping_request_queue,
            'PING_RESPONSE_QUEUE': self.ping_response_queue,
            'IDENTIFIER': self.identifier
        }

    """
          _____       _ _   _       _ _         
         |_   _|     (_) | (_)     | (_)        
           | |  _ __  _| |_ _  __ _| |_ _______ 
           | | | '_ \| | __| |/ _` | | |_  / _ \
          _| |_| | | | | |_| | (_| | | |/ /  __/
         |_____|_| |_|_|\__|_|\__,_|_|_/___\___|
    """

    def initialize(self):
        if self.container is None:
            self.initialize_container()
        else:
            self.scan_container()

    def initialize_container(self):

        # --> 1. Call Parent Initialization
        self._initialize()

        # --> 3. Create container
        self.container = self.docker_client.containers.run(
            image=self.container_config['image'],
            detach=self.container_config['detach'],
            network=self.container_config['network'],
            environment=self.container_config['environment'],
            name=self.container_config['name'],
            labels=self.container_config['labels'],
            mem_limit=self.container_config['mem_limit'],
            cpu_period=self.container_config['cpu_period'],
            cpu_quota=self.container_config['cpu_quota']
        )

    """
           _____ _             _         __   _____ _              
          / ____| |           | |       / /  / ____| |             
         | (___ | |_ __ _ _ __| |_     / /  | (___ | |_ ___  _ __  
          \___ \| __/ _` | '__| __|   / /    \___ \| __/ _ \| '_ \ 
          ____) | || (_| | |  | |_   / /     ____) | || (_) | |_) |
         |_____/ \__\__,_|_|   \__| /_/     |_____/ \__\___/| .__/ 
                                                            | |    
                                                            |_|    
    """

    def start_algorithm(self, objectives, crossover_prob=1, mutation_prob=0.01666):
        msg_attributes = {
            'msgType': {
                'StringValue': 'start_ga',
                'DataType': 'String'
            },
            'crossoverProbability': {
                'StringValue': str(crossover_prob),
                'DataType': 'String'
            },
            'mutationProbability': {
                'StringValue': str(float(mutation_prob)),
                'DataType': 'String'
            },
            'objectives': {
                'StringValue': str(objectives),
                'DataType': 'String'
            },
            'user_id': {
                'StringValue': str(self.user_info.user.id),
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': str(self.user_info.eosscontext.group_id),
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': str(self.user_info.eosscontext.problem_id),
                'DataType': 'String'
            },
            'VASSAR_REQUEST_QUEUE': {
                'StringValue': str(self.user_info.eosscontext.problem_id),
                'DataType': 'String'
            },
            'VASSAR_RESPONSE_QUEUE': {
                'StringValue': str(self.user_info.eosscontext.problem_id),
                'DataType': 'String'
            },
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.private_request_queue, MessageBody='boto3', MessageAttributes=msg_attributes)

    def stop_algorithm(self):
        msg_attributes = {
            'msgType': {
                'StringValue': 'stop_ga',
                'DataType': 'String'
            }
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.private_request_queue, MessageBody='boto3', MessageAttributes=msg_attributes)