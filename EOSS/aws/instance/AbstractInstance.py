import os
import boto3
import copy
import json
import asyncio
import random
import string
from EOSS.aws.utils import call_boto3_client_async, find_obj_value, _linear_sleep_async
from EOSS.aws.clients.SqsClient import SqsClient




""" AbstractInstance
- The purpose of this class is to model a single ec2 instance (bottlerocket AMI) deployed on an ecs cluster (daphne-dev-cluster) 

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

    EC2
    1. run_instances()   - used to create a new ec2 instance user resources are being initialized
    2. start_instances() - starts a stopped ec2 instance when user requests more resources
    3. stop_instances()  - stops a running ec2 instance when user requests less resources / timeout
    
    SSM
    1. send_command()     - used to start container service inside ec2
    
    
    async_tasks = []
    async_tasks.append(asyncio.create_task())
    
    for task in async_tasks:
        await task
    

"""


class AbstractInstance:

    def __init__(self, user_info, instance):
        if user_info.user is None:
            raise Exception("--> (error) AbstractInstance: User is not registered!")
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext

        # --> Local verion of instance
        self.instance = instance


        # --> Container Data
        self.identifier = None
        self.instance_type = None
        self.private_request_url = None
        self.private_response_url = None
        self.ping_request_url = None
        self.ping_response_url = None


    """
          _____       _ _   _       _ _         
         |_   _|     (_) | (_)     | (_)        
           | |  _ __  _| |_ _  __ _| |_ _______ 
           | | | '_ \| | __| |/ _` | | |_  / _ \
          _| |_| | | | | |_| | (_| | | |/ /  __/
         |_____|_| |_|_|\__|_|\__,_|_|_/___\___|
    """

    async def _initialize(self):

        # --> 1. Create instance identifier
        self.identifier = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))

        # --> 2. Create queues
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.initialize_private_queues()))
        async_tasks.append(asyncio.create_task(self.initialize_ping_queues()))
        for task in async_tasks:
            await task

    async def initialize_ping_queues(self):
        print('--> INITIALIZING PRIVATE PING QUEUES')
        self.ping_request_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-request-queue' + self.identifier
        )
        self.ping_response_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-response-queue' + self.identifier
        )

    async def initialize_private_queues(self):
        print('--> INITIALIZING PRIVATE REQUEST QUEUES')
        self.private_request_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-request-queue' + self.identifier
        )
        self.private_response_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-response-queue' + self.identifier
        )

    async def scan_container(self):
        tags = self.instance['Tags']
        self.private_request_url = await find_obj_value(tags, 'Key', 'PRIVATE_REQUEST_QUEUE', 'Value')
        self.private_response_url = await find_obj_value(tags, 'Key', 'PRIVATE_RESPONSE_QUEUE', 'Value')
        self.ping_request_url = await find_obj_value(tags, 'Key', 'PING_REQUEST_QUEUE', 'Value')
        self.ping_response_url = await find_obj_value(tags, 'Key', 'PING_RESPONSE_QUEUE', 'Value')
        self.identifier = await find_obj_value(tags, 'Key', 'IDENTIFIER', 'Value')




    """
       _____  _                _   
      / ____|| |              | |  
     | (___  | |_  __ _  _ __ | |_ 
      \___ \ | __|/ _` || '__|| __|
      ____) || |_| (_| || |   | |_ 
     |_____/  \__|\__,_||_|    \__|
    """

    async def start(self):
        response = await call_boto3_client_async('ec2', 'start_instances', {
            'InstanceIds': [await self.instance_id]
        })
        if response is None or 'StartingInstances' not in response:
            print('--> ERROR STARTING INSTANCE, BAD RESPONSE:', json.dumps(response, indent=4, default=str))
        elif len(response['StartingInstances']) == 0:
            print('--> ERROR NO INSTANCES WERE STARTED')
        else:
            temp = response['StartingInstances'][0]
            print('--> STARTING INSTANCE:', self.identifier, temp['CurrentState']['Name'], temp['PreviousState']['Name'])


    """
       _____  _                
      / ____|| |               
     | (___  | |_  ___   _ __  
      \___ \ | __|/ _ \ | '_ \ 
      ____) || |_| (_) || |_) |
     |_____/  \__|\___/ | .__/ 
                        | |    
                        |_|    
    """

    async def stop(self):
        response = await call_boto3_client_async('ec2', 'stop_instances', {
            'InstanceIds': [await self.instance_id]
        })
        if response is None or 'StoppingInstances' not in response:
            print('--> ERROR STARTING INSTANCE, BAD RESPONSE:', json.dumps(response, indent=4, default=str))
        elif len(response['StoppingInstances']) == 0:
            print('--> ERROR NO INSTANCES WERE STARTED')
        else:
            temp = response['StoppingInstances'][0]
            print('--> STOPPING INSTANCE:', self.identifier, temp['CurrentState']['Name'],
                  temp['PreviousState']['Name'])



    """
     _____                                    
    |  __ \                                   
    | |__) | ___  _ __ ___    ___ __   __ ___ 
    |  _  / / _ \| '_ ` _ \  / _ \\ \ / // _ \
    | | \ \|  __/| | | | | || (_) |\ V /|  __/
    |_|  \_\\___||_| |_| |_| \___/  \_/  \___|

    """

    async def remove(self):

        # --> 1. Terminate Instances
        response = await call_boto3_client_async('ec2', 'terminate_instances', {
            'InstanceIds': [await self.instance_id]
        })
        if response is None or 'TerminatingInstances' not in response:
            print('--> ERROR STARTING INSTANCE, BAD RESPONSE:', json.dumps(response, indent=4, default=str))
        elif len(response['TerminatingInstances']) == 0:
            print('--> ERROR NO INSTANCES WERE STARTED')
        else:
            temp = response['TerminatingInstances'][0]
            print('--> TERMINATING INSTANCE:', self.identifier, temp['CurrentState']['Name'],
                  temp['PreviousState']['Name'])

        # --> 2. Delete queues
        await self.delete_instance_queues()

    async def delete_instance_queues(self):
        async_tasks = []

        if self.ping_request_url:
            async_tasks.append(
                asyncio.create_task(SqsClient.delete_queue_url(self.ping_request_url))
            )
        if self.ping_response_url:
            async_tasks.append(
                asyncio.create_task(SqsClient.delete_queue_url(self.ping_response_url))
            )
        if self.private_request_url:
            async_tasks.append(
                asyncio.create_task(SqsClient.delete_queue_url(self.private_request_url))
            )
        if self.private_response_url:
            async_tasks.append(
                asyncio.create_task(SqsClient.delete_queue_url(self.private_response_url))
            )

        for task in async_tasks:
            await task



    """
      ____        _ _     _ 
     |  _ \      (_) |   | |
     | |_) |_   _ _| | __| |
     |  _ <| | | | | |/ _` |
     | |_) | |_| | | | (_| |
     |____/ \__,_|_|_|\__,_|                 
    """

    async def build(self):
        return 0

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

    async def ping(self):

        # --> 1. Send ping message, get response
        response = await SqsClient.send_ping_msg(self.ping_request_url, self.ping_response_url)
        response['instance_tags'] = await self._tags  # From child class
        return response

    def send_ping_message(self):
        request = await call_boto3_client_async('sqs', 'send_message', {
            'QueueUrl': self.ping_request_url,
            'MessageBody': 'boto3',
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'ping',
                    'DataType': 'String'
                },
            }
        })

    """
      _    _        _                         
     | |  | |      | |                        
     | |__| |  ___ | | _ __    ___  _ __  ___ 
     |  __  | / _ \| || '_ \  / _ \| '__|/ __|
     | |  | ||  __/| || |_) ||  __/| |   \__ \
     |_|  |_| \___||_|| .__/  \___||_|   |___/
                      | |                     
                      |_|               
    """

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
        if request is not None and 'Reservations' in request:
            self.instance = request['Reservations'][0]['Instances'][0]
        return self.instance

    @property
    async def instance_id(self):
        instance = await self.get_instance()
        return instance['InstanceId']

    @property
    async def instance_state(self):
        instance = await self.get_instance()
        return instance['State']['Name']

    async def wait_on_state(self, target_state='running', seconds=60):
        iter = 0
        iter_max = int(seconds/2)
        curr_state = await self.instance_state
        while curr_state != target_state:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(2)
            curr_state = await self.instance_state
        return True



