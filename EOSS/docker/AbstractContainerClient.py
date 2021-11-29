import docker

from EOSS.aws.utils import get_boto3_client

from EOSS.docker.helpers import get_or_create_queue
import copy

import random
import string




class AbstractContainerClient:
    def __init__(self, user_info, container):
        self.docker_client = docker.from_env()
        self.user_info = user_info
        self.eval_request_queue = self.user_info.eval_request_queue
        self.eval_response_queue = self.user_info.eval_response_queue
        self.container = container

        # --> 1. Initialize scan data
        self.container_type = None
        self.private_request_queue = None
        self.private_response_queue = None
        self.ping_request_queue = None
        self.ping_response_queue = None
        self.identifier = None

    def _initialize(self):

        # --> 1. Create container identifier
        self.identifier = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))

        # --> 2. Create or purge private and public queues if they exist
        self.initialize_private_queues()
        self.initialize_ping_queues()

    def _shutdown(self):
        self.container.remove()
        self.delete_private_queues()

    def initialize_ping_queues(self):
        queue_name_request = 'user-' + str(self.user_info.user.id) + '-ping-request-' + self.identifier
        queue_name_response = 'user-' + str(self.user_info.user.id) + '-ping-response-' + self.identifier
        self.ping_request_queue = get_or_create_queue(queue_name_request)
        self.ping_response_queue = get_or_create_queue(queue_name_response)

    def initialize_private_queues(self):
        queue_name_request = 'user-' + str(self.user_info.user.id) + '-private-request-' + self.identifier
        queue_name_response = 'user-' + str(self.user_info.user.id) + '-private-response-' + self.identifier
        self.private_request_queue = get_or_create_queue(queue_name_request)
        self.private_response_queue = get_or_create_queue(queue_name_response)

    def delete_private_queues(self):
        sqs_client = get_boto3_client('sqs')
        if self.private_request_queue:
            sqs_client.delete_queue(QueueUrl=self.private_request_queue)
        if self.private_response_queue:
            sqs_client.delete_queue(QueueUrl=self.private_response_queue)
        if self.ping_request_queue:
            sqs_client.delete_queue(QueueUrl=self.ping_request_queue)
        if self.ping_response_queue:
            sqs_client.delete_queue(QueueUrl=self.ping_response_queue)

    def scan_container(self):
        self.private_request_queue = self.container.labels['PRIVATE_REQUEST_QUEUE']
        self.private_response_queue = self.container.labels['PRIVATE_RESPONSE_QUEUE']
        self.ping_request_queue = self.container.labels['PING_REQUEST_QUEUE']
        self.ping_response_queue = self.container.labels['PING_RESPONSE_QUEUE']
        self.identifier = self.container.labels['IDENTIFIER']
        return 0

    def subscribe_to_message(self, queue, msg_type, attempts=5, attempt_time=5):
        sqs_client = get_boto3_client('sqs')
        subscription = {}
        for i in range(attempts):
            response = sqs_client.receive_message(
                QueueUrl=queue,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=attempt_time,
                MessageAttributeNames=["All"]
            )
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == msg_type:
                        subscription = copy.deepcopy(message["MessageAttributes"])
                        sqs_client.delete_message(QueueUrl=self.private_response_queue, ReceiptHandle=message["ReceiptHandle"])
                        break_switch = True
                if break_switch is True:
                    return subscription
        print('--> CONNECTION TIMEOUT ERROR')
        return {'msgType': 'timeout error'}

    """
          _____ _             
         |  __ (_)            
         | |__) | _ __   __ _ 
         |  ___/ | '_ \ / _` |
         | |   | | | | | (_| |
         |_|   |_|_| |_|\__, |
                         __/ |
                        |___/ 
     """

    def ping(self):
        # --> 1. Send ping message
        self.send_ping_message()

        # --> 2. Wait for ping response
        return self.subscribe_to_message(self.ping_response_queue, 'statusAck')

    def send_ping_message(self):
        msg_attributes = {
            'msgType': {
                'StringValue': 'ping',
                'DataType': 'String'
            },
        }
        sqs_client = get_boto3_client('sqs')
        sqs_client.send_message(QueueUrl=self.ping_request_queue, MessageBody='boto3', MessageAttributes=msg_attributes)
