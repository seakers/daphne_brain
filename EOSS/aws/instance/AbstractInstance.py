import os
import boto3
import copy
import json
import asyncio
import random
import string
from EOSS.aws.utils import call_boto3_client_async, find_obj_value, _linear_sleep_async, exponential_backoff_async
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
         ---- If instance dne: call _initialize()
         - If instance exists: call scan_container()
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
        self.ping_request_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-request-queue' + self.identifier
        )
        self.ping_response_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-response-queue' + self.identifier
        )

    async def initialize_private_queues(self):
        self.private_request_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-request-queue' + self.identifier
        )
        self.private_response_url = await SqsClient.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-response-queue' + self.identifier
        )

    async def scan_container(self):
        print('--> SCANNING CONTAINER')
        tags = self.instance['Tags']
        self.private_request_url = await find_obj_value(tags, 'Key', 'PRIVATE_REQUEST_URL', 'Value')
        self.private_response_url = await find_obj_value(tags, 'Key', 'PRIVATE_RESPONSE_URL', 'Value')
        self.ping_request_url = await find_obj_value(tags, 'Key', 'PING_REQUEST_URL', 'Value')
        self.ping_response_url = await find_obj_value(tags, 'Key', 'PING_RESPONSE_URL', 'Value')
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

        # --> 1. Ensure instance either stopping or stopped
        curr_state = await self.instance_state
        if curr_state not in ['stopping', 'stopped']:
            print('--> COULD NOT START INSTANCE, NOT STOPPED OR STOPPING:', self.identifier, curr_state)
            return None

        # --> 2. If current state is stopping, wait until stopped
        if await self.wait_on_state('stopped', seconds=120) is False:
            print('--> COULD NOT START INSTANCE, NEVER REACHED STOPPED STATE:', self.identifier, curr_state)
            return None

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

        # --> 1. Ensure instance either pending or running
        curr_state = await self.instance_state
        if curr_state not in ['pending', 'running']:
            print('--> COULD NOT STOP INSTANCE, NOT RUNNING OR PENDING:', self.identifier, curr_state)
            return None

        # --> 2. If current state is pending, wait until running
        if await self.wait_on_state('running', seconds=120) is False:
            print('--> COULD NOT STOP INSTANCE, NEVER REACHED RUNNING STATE:', self.identifier, curr_state)
            return None

        # --> 3. Stop instance
        response = await call_boto3_client_async('ec2', 'stop_instances', {
            'InstanceIds': [await self.instance_id],
            'Hibernate': True
        })
        if response is None:
            response = await call_boto3_client_async('ec2', 'stop_instances', {
                'InstanceIds': [await self.instance_id],
                'Hibernate': False
            })
        if response is None or 'StoppingInstances' not in response:
            print('--> ERROR STARTING INSTANCE, BAD RESPONSE:', json.dumps(response, indent=4, default=str))
        elif len(response['StoppingInstances']) == 0:
            print('--> ERROR NO INSTANCES WERE STARTED')
        else:
            temp = response['StoppingInstances'][0]
            print('--> STOPPING INSTANCE:', self.identifier, temp['PreviousState']['Name'], '-->',
                  temp['CurrentState']['Name'])


    async def hibernate(self, blocking=True):
        parameters = {
            'InstanceIds': [await self.instance_id],
            'Hibernate': True
        }
        if blocking:
            await exponential_backoff_async()

        exponential_backoff_async()
        count = 0
        while await call_boto3_client_async('ec2', 'stop_instances', {
            'InstanceIds': [await self.instance_id],
            'Hibernate': True
        }) is None:



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

        # --> 1. Ensure instance either pending or running
        curr_state = await self.instance_state
        if curr_state not in ['pending', 'running']:
            print('--> COULD NOT BUILD INSTANCE, NOT RUNNING OR PENDING:', self.identifier, curr_state)
            return False

        # --> 2. If current state is pending, wait until running
        if await self.wait_on_state('running', seconds=120) is False:
            print('--> COULD NOT BUILD INSTANCE, NEVER REACHED RUNNING STATE:', self.identifier, curr_state)
            return False

        await SqsClient.send_build_msg(self.private_request_url)

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
        response['IDENTIFIER'] = self.identifier
        return response


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

    # --> NOTE: can only be called every 60 seconds
    async def purge_queues(self):
        async_tasks = []
        async_tasks.append(asyncio.create_task(SqsClient.purge_queue_url(self.private_request_url)))
        async_tasks.append(asyncio.create_task(SqsClient.purge_queue_url(self.private_response_url)))
        async_tasks.append(asyncio.create_task(SqsClient.purge_queue_url(self.ping_response_url)))
        async_tasks.append(asyncio.create_task(SqsClient.purge_queue_url(self.ping_response_url)))
        for task in async_tasks:
            await task

    async def wait_on_state(self, target_state='running', seconds=60):
        iter = 0
        iter_max = int(seconds/3)
        curr_state = await self.instance_state
        while curr_state != target_state:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(3)
            curr_state = await self.instance_state
        return True

    async def wait_on_states(self, target_states=['pending', 'running'], seconds=60):
        iter = 0
        iter_max = int(seconds / 3)
        curr_state = await self.instance_state
        while curr_state not in target_states:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(3)
            curr_state = await self.instance_state
        return True

    async def get_instance(self, debug=False):
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
        }, debug=debug)
        if request is not None and 'Reservations' in request:
            if len(request['Reservations']) == 0:
                print('--> NO RESERVATIONS:', self.user_info.user, self.identifier)
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

    async def get_tag(self, tag):
        instance = await self.get_instance()
        return await find_obj_value(instance['Tags'], 'Key', tag, 'Value')

    async def set_tag(self, tag, value):
        result = await call_boto3_client_async('ec2', 'create_tags', {
            'Resources': [await self.instance_id],
            'Tags': [
                {
                    'Key': tag,
                    'Value': value
                }
            ]
        })



    """
       _____  _____  __  __ 
      / ____|/ ____||  \/  |
     | (___ | (___  | \  / |
      \___ \ \___ \ | |\/| |
      ____) |____) || |  | |
     |_____/|_____/ |_|  |_|
                            
    """

    async def ssm_command(self, command):

        async def wait_for_output(command_id):
            await _linear_sleep_async(1)
            response = await call_boto3_client_async('ssm', 'list_command_invocations', {
                'CommandId': command_id,
                'Details': True
            })
            count = 0
            while len(response['CommandInvocations']) == 0:
                await _linear_sleep_async(2)
                response = await call_boto3_client_async('ssm', 'list_command_invocations', {
                    'CommandId': command_id,
                    'Details': True
                })
                count += 1
                if count > 10:
                    return ''
            output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
            return output

        # --> 1. Send command
        response = await call_boto3_client_async('ssm', 'send_command', {
            'InstanceIds': [await self.instance_id],
            'DocumentName': 'AWS-RunShellScript',
            'Parameters': {
                'commands': [command]
            }
        })
        command_id = response['Command']['CommandId']

        # --> 2. Get output and strip
        output = await wait_for_output(command_id)
        return output.strip()


    async def container_running(self):
        command = 'docker ps -q | xargs'
        output = await self.ssm_command(command)
        if output == '':
            return False
        else:
            return True



