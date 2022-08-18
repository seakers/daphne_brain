from EOSS.docker.clients.AbstractContainerClient import AbstractContainerClient
from EOSS.aws.utils import get_boto3_client





class VassarContainerClient(AbstractContainerClient):
    def __init__(self, user_info, container=None):
        super().__init__(user_info, container)

        # --> Read container data
        self.container_type = 'eval'

        # --> Initialize container
        self.initialize()

    def shutdown(self):
        self.exit()
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
            'network': 'daphne_service',
            'detach': True,
            'labels': self.labels,
            'name': str('user-' + str(self.user_info.user.id) + '-container-' + self.identifier),
            'image': 'apazagab/vassar:experiment',
            'environment': {
                # --> QUEUE URLS
                'VASSAR_REQUEST_URL': self.eval_request_queue,
                'VASSAR_RESPONSE_URL': self.eval_response_queue,
                'PING_REQUEST_QUEUE': self.ping_request_queue,
                'PING_RESPONSE_QUEUE': self.ping_response_queue,
                'PRIVATE_QUEUE_REQUEST': self.private_request_queue,
                'PRIVATE_QUEUE_RESPONSE': self.private_response_queue,

                # --> SERVICE ADDRESSES
                'APOLLO_URL': 'http://172.12.0.13:8080/v1/graphql',
                'APOLLO_URL_WS': 'ws://172.12.0.13:8080/v1/graphql',
                'AWS_STACK_ENDPOINT': 'http://172.12.0.5:9324',

                # --> AWS CONFIGURATION
                'AWS_ACCESS_KEY_ID': 'AKIAJVM34C5MCCWRJCCQ',
                'AWS_SECRET_ACCESS_KEY': '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',
                'REGION': 'elasticmq',

                # --> OTHER
                'REQUEST_MODE': 'CRISP-ATTRIBUTES',
                'DEPLOYMENT_TYPE': 'local',
                'JAVA_OPTS': '-"Dcom.sun.management.jmxremote.rmi.port=10000 -Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10000 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.local.only=false -Djava.rmi.server.hostname=localhost"',
                'REQUEST_KEY': 'NONE',
                'MAXEVAL': 5,
            },
            'mem_limit': '2g',
            'cpu_period': 100000,
            'cpu_quota': 100000,
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
            'VASSAR_REQUEST_URL': self.eval_request_queue,
            'VASSAR_RESPONSE_URL': self.eval_response_queue,
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

        # --> 2. Create container
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

        # --> 4. Connect to container
        connection = self.connect()

    """
            _____                            _   
          / ____|                          | |  
         | |     ___  _ __  _ __   ___  ___| |_ 
         | |    / _ \| '_ \| '_ \ / _ \/ __| __|
         | |___| (_) | | | | | | |  __/ (__| |_ 
          \_____\___/|_| |_|_| |_|\___|\___|\__|
    """

    def connect(self):
        # --> Send connection message
        self.send_connection_message()

        # --> Await connection validation
        response = self.subscribe_to_message(self.private_response_queue, 'isAvailable')
        if response['msgType'] == 'timeout error':
            return False
        return True

    def send_connection_message(self):
        msg_attributes = {
            'msgType': {
                'StringValue': 'connectionRequest',
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
            }
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.private_request_queue, MessageBody='boto3', MessageAttributes=msg_attributes)

    """
      ____        _ _     _ 
     |  _ \      (_) |   | |
     | |_) |_   _ _| | __| |
     |  _ <| | | | | |/ _` |
     | |_) | |_| | | | (_| |
     |____/ \__,_|_|_|\__,_|              
    """

    def build(self):
        # --> Send build message
        self.send_build_message()

        # --> Await connection validation
        response = self.subscribe_to_message(self.private_response_queue, 'isReady')
        if response['msgType'] == 'timeout error':
            return False
        return True

    def send_build_message(self):
        msg_attributes = {
            'msgType': {
                'StringValue': 'build',
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': str(self.user_info.eosscontext.group_id),
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': str(self.user_info.eosscontext.problem_id),
                'DataType': 'String'
            }
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.private_request_queue, MessageBody='boto3', MessageAttributes=msg_attributes)

    """
      ______      _ _   
     |  ____|    (_) |  
     | |__  __  ___| |_ 
     |  __| \ \/ / | __|
     | |____ >  <| | |_ 
     |______/_/\_\_|\__|
    """

    def exit(self):
        # --> Send exit message
        self.send_exit_message()

        # --> Await connection validation
        response = self.subscribe_to_message(self.private_response_queue, 'exit')
        if response['msgType'] == 'timeout error':
            return False
        return True

    def send_exit_message(self):
        msg_attributes = {
            'msgType': {
                'StringValue': 'exit',
                'DataType': 'String'
            }
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.private_request_queue, MessageBody='boto3',
                                MessageAttributes=msg_attributes)











