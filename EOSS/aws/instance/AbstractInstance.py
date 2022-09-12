import os
import boto3
import random
import string
from EOSS.aws.utils import call_boto3_client_async, find_obj_value, _linear_sleep_async
from EOSS.aws.clients.SqsClient import SqsClient




""" AbstractInstance
- The purpose of this class is to model a single ec2 instance (bottlerocket AMI) deployed on an ecs cluster (daphne-dev-cluster) 

AWS Functions
    1. run_instances()
    
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()
    
    
Software Architecture Design Decisions

    1. Decision (down-selecting) ~ at what level do we scale the design evaluator functionality?
    
        - A. At the docker container level
            - Description: each daphne user gets one ec2 instance capable of launching up to 10 task instances
            - Pros: very fast scalability
            - Cons: pay extra for unused resources... may as well always have 10 running
            
        - B. At the ec2 instance level
            - Description: each daphne user gets up to 10 ec2 instances, each capable of launching one task instance
            - Pros: cost effective, as it scales at the ec2 level
            - Cons: more overhead while scaling
    
        Decision Choice: B
    

AWS Functions
    1. run_instances()
    
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()
    

"""


class AbstractInstance:

    def __init__(self, user_info, instance):
        if user_info.user is None:
            raise Exception("--> (error) AbstractInstance: User is not registered!")
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext
        self.instance = instance


        # --> Container Data
        self.identifier = None
        self.instance_type = None
        self.private_request_queue = None
        self.private_response_queue = None
        self.ping_request_queue = None
        self.ping_response_queue = None

    async def _initialize(self):

        # --> 1. Create instance identifier
        self.identifier = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))

        # --> 2. Create queues
        await self.initialize_private_queues()
        await self.initialize_ping_queues()

    async def _shutdown(self):
        return 0

    async def _remove(self):
        return 0





    async def initialize_ping_queues(self):
        print('--> INITIALIZING PRIVATE PING QUEUES')
        self.ping_request_queue = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-request-queue' + self.identifier
        )
        self.ping_response_queue = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-response-queue' + self.identifier
        )

    async def initialize_private_queues(self):
        print('--> INITIALIZING PRIVATE REQUEST QUEUES')
        self.private_request_queue = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-request-queue' + self.identifier
        )
        self.private_response_queue = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-response-queue' + self.identifier
        )

    async def delete_private_queues(self):
        if self.ping_request_queue:
            await SqsClient.delete_queue_url(self.ping_request_queue)
        if self.ping_response_queue:
            await SqsClient.delete_queue_url(self.ping_response_queue)
        if self.private_request_queue:
            await SqsClient.delete_queue_url(self.private_request_queue)
        if self.private_response_queue:
            await SqsClient.delete_queue_url(self.private_response_queue)


    async def scan_container(self):
        tags = self.instance['Tags']
        self.private_request_queue = await find_obj_value(tags, 'Key', 'PRIVATE_REQUEST_QUEUE', 'Value')
        self.private_response_queue = await find_obj_value(tags, 'Key', 'PRIVATE_RESPONSE_QUEUE', 'Value')
        self.ping_request_queue = await find_obj_value(tags, 'Key', 'PING_REQUEST_QUEUE', 'Value')
        self.ping_response_queue = await find_obj_value(tags, 'Key', 'PING_RESPONSE_QUEUE', 'Value')
        self.identifier = await find_obj_value(tags, 'Key', 'IDENTIFIER', 'Value')





    async def get_instance(self):
        request = await call_boto3_client_async('ec2', 'describe_instances', {
            "Filters": [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        'vpc-0167d66edf8eebc3c',
                    ]
                },
                {
                    'Name': 'tag:USER_ID',
                    'Values': [
                        str(self.user_id),
                    ]
                },
                {
                    'Name': 'tag:IDENTIFIER',
                    'Values': [
                        self.identifier
                    ]
                },
            ]
        })
        if 'Reservations' in request:
            self.instance = request['Reservations'][0]['Instances'][0]
        return self.instance




    async def wait_on_state(self, target_state='running', seconds=60):
        iter = 0
        iter_max = int(seconds/2)
        curr_state = None
        while curr_state != target_state:
            instance = await self.get_instance()
            if instance is not None:
                curr_state = instance['State']['Name']
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(2)
        return True






        instance = self.get_instance()





        # -->
        request = await call_boto3_client_async('ec2', 'describe_instances', {
            "Filters": [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        'vpc-0167d66edf8eebc3c',
                    ]
                },
                {
                    'Name': 'tag:USER_ID',
                    'Values': [
                        str(self.user_id),
                    ]
                },
                {
                    'Name': 'tag:IDENTIFIER',
                    'Values': [
                        self.identifier
                    ]
                },
            ]
        })


        return 0









