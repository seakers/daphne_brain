import os
import boto3
import copy
import time
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
    """


    ####################
    ### New Instance ###
    ####################
    # parameter (definition) is supplied by the child class calling this function
    async def _new_resources(self):
        # --> 1. Create instance identifier
        self.identifier = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))

        # --> 2. Create queues
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.initialize_private_queues()))
        async_tasks.append(asyncio.create_task(self.initialize_ping_queues()))
        for task in async_tasks:
            await task

    async def _new_instance(self, definition):
        start_time = time.time()

        # --> 1. Create instance (no userdata)
        run_call = await call_boto3_client_async('ec2', 'run_instances', definition)
        if run_call is None:
            return

        # --> 2. Wait until instance is running (~32s)
        running = await self.wait_on_states(['running'], seconds=120)
        if running is not True:
            print('--> INSTANCE NEVER REACHED RUNNING STATE:', self.identifier)
        else:
            print('-->', self.identifier, 'RUNNING', time.time() - start_time, 'seconds')

        # --> 3. Wait until SSM has finished booting
        ssm_running = await self.wait_on_ssm_status('Online', seconds=120)
        if ssm_running is not True:
            print('--> INSTANCE SSM MANAGER NEVER ONLINE:', self.identifier)
        else:
            print('-->', self.identifier, 'SSM ONLINE', time.time() - start_time, 'seconds')

        # --> 4. Run evaluator container (retry)
        await self.ssm_command([
            '. /home/ec2-user/pull.sh',
            '. /home/ec2-user/run.sh'
        ])
        # await self.ssm_command('. /home/ec2-user/pull.sh')
        # await self.ssm_command('. /home/ec2-user/run.sh')

        # --> 5. Wait on container running
        result = await self.wait_on_container_running()
        print('-->', self.identifier, 'CONTAINER ONLINE', time.time() - start_time, 'seconds')

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


    #########################
    ### Existing Instance ###
    #########################

    async def _existing_instance(self):
        tags = self.instance['Tags']
        self.private_request_url = await find_obj_value(tags, 'Key', 'PRIVATE_REQUEST_URL', 'Value')
        self.private_response_url = await find_obj_value(tags, 'Key', 'PRIVATE_RESPONSE_URL', 'Value')
        self.ping_request_url = await find_obj_value(tags, 'Key', 'PING_REQUEST_URL', 'Value')
        self.ping_response_url = await find_obj_value(tags, 'Key', 'PING_RESPONSE_URL', 'Value')
        self.identifier = await find_obj_value(tags, 'Key', 'IDENTIFIER', 'Value')







    """
         _____                                 _    _            
        |  __ \                               | |  (_)           
        | |__) |_ __  ___   _ __    ___  _ __ | |_  _   ___  ___ 
        |  ___/| '__|/ _ \ | '_ \  / _ \| '__|| __|| | / _ \/ __|
        | |    | |  | (_) || |_) ||  __/| |   | |_ | ||  __/\__ \
        |_|    |_|   \___/ | .__/  \___||_|    \__||_| \___||___/
                           | |                                   
                           |_|          
    """

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

    async def get_instance_status(self):
        request = await call_boto3_client_async('ec2', 'describe_instance_status', {
            "InstanceIds": [await self.instance_id]
        }, False)
        if request is None or 'InstanceStatuses' not in request:
            return None
        if len(request['InstanceStatuses']) == 0:
            return None
        curr_status = request['InstanceStatuses'][0]
        return curr_status

    async def get_instance_ssm_info(self):
        request = await call_boto3_client_async('ssm', 'describe_instance_information', {
            "Filters": [
                {
                    'Key': 'InstanceIds',
                    'Values': [await self.instance_id]
                }
            ]
        }, False)
        if request is None or 'InstanceInformationList' not in request or len(request['InstanceInformationList']) == 0:
            return None
        return request['InstanceInformationList'][0]


    @property
    async def instance_id(self):
        instance = await self.get_instance()
        return instance['InstanceId']

    @property
    async def instance_state(self):
        instance = await self.get_instance()
        return instance['State']['Name']

    @property
    async def instance_status(self):
        instance = await self.get_instance_status()
        if instance is None:
            return instance
        return instance['InstanceStatus']['Status']

    @property
    async def system_status(self):
        instance = await self.get_instance_status()
        if instance is None:
            return instance
        return instance['SystemStatus']['Status']

    @property
    async def instance_ssm_status(self):
        instance = await self.get_instance_ssm_info()
        if instance is None:
            return instance
        return instance['PingStatus']



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
        if curr_state not in ['running']:
            print('--> COULD NOT STOP INSTANCE, NOT RUNNING:', self.identifier, curr_state)
            return None

        # --> 2. Stop instance
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

        async def wait_func(parameters, seconds=30):
            sleep_time = 5
            counter = 0
            attempts = int(seconds / sleep_time)
            result = await call_boto3_client_async('ec2', 'stop_instances', parameters)
            while result is None:
                await _linear_sleep_async(sleep_time)
                result = await call_boto3_client_async('ec2', 'stop_instances', parameters)
                counter += 1
                if counter > attempts:
                    return None
            return result
        parameters = {
            'InstanceIds': [await self.instance_id],
            'Hibernate': True
        }
        task = asyncio.create_task(wait_func(parameters))
        if blocking:
            await task


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
        ping_response = dict()
        ping_response['container'] = {}
        ping_response['instance'] = {}

        # --> 1. Get instance: tags, state, status, ssm status
        instance = await self.get_instance()
        if instance is not None:
            ping_response['instance']['Tags'] = instance['Tags']
            ping_response['instance']['State'] = instance['State']['Name']
        else:
            ping_response['instance']['Tags'] = None
            ping_response['instance']['State'] = None
        ping_response['instance']['Status'] = await self.instance_status
        ping_response['instance']['SSMStatus'] = await self.instance_ssm_status
        ping_response['instance']['IDENTIFIER'] = self.identifier

        # --> 2. Get container info if instance and container both running
        if ping_response['instance']['Status'] == 'running' and await self.container_running() is True:
            ping_response['container'] = await SqsClient.send_ping_msg(self.ping_request_url, self.ping_response_url)
        else:
            ping_response['container'] = 'empty'

        return ping_response


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
        request_interval = 3
        iter = 0
        iter_max = int(seconds / request_interval)
        curr_state = await self.instance_state
        while curr_state not in target_states:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(request_interval)
            curr_state = await self.instance_state
        return True

    async def wait_on_status(self, target_status='ok', seconds=60):

        # --> 1. Wait for instance to be in running state
        curr_state = await self.instance_state
        if curr_state != 'running':
            if curr_state != 'pending':
                print('--> (ERROR) CANT WAIT ON STATUS WHILE INSTANCE NOT RUNNING OR PENDING:', self.identifier)
                return False
            else:
                t_start = time.time()
                result = await self.wait_on_state('running', seconds=seconds)
                if result is False:
                    return False
                t_run = time.time() - t_start
                seconds = seconds - t_run

        # --> 2. Now wait on status
        sleep_time = 10
        iter = 0
        iter_max = int(seconds / sleep_time)
        curr_status = await self.instance_status
        while curr_status != target_status:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(sleep_time)
            curr_status = await self.instance_status
        return True

    async def wait_on_ssm_status(self, target_status='Online', seconds=60):
        request_interval = 3
        iter = 0
        iter_max = int(seconds / request_interval)
        curr_status = await self.instance_ssm_status
        while curr_status != target_status:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(request_interval)
            curr_status = await self.instance_ssm_status
        return True

    async def wait_on_container_running(self, seconds=60):
        request_interval = 3
        iter = 0
        iter_max = int(seconds / request_interval)
        curr_status = await self.container_running()
        while curr_status is False:
            iter += 1
            if iter >= iter_max:
                return False
            await asyncio.sleep(request_interval)
            curr_status = await self.container_running()
        return True








    """
       _____  _____  __  __ 
      / ____|/ ____||  \/  |
     | (___ | (___  | \  / |
      \___ \ \___ \ | |\/| |
      ____) |____) || |  | |
     |_____/|_____/ |_|  |_|
    
    Constraints
    - Only possible when instance in running state
    
    """
    async def _ssm(self, parameters, attempts=1):

        async def validate(parameters):
            response = await call_boto3_client_async('ssm', 'send_command', parameters, True)
            if response is None or 'Command' not in response or 'CommandId' not in response['Command']:
                return None
            return response

        response = await validate(parameters)
        counter = 1
        while response is None and counter < attempts:
            await asyncio.sleep(5)
            response = await validate(parameters)
            counter += 1

        if response is None:
            return None
        else:
            return response['Command']['CommandId']


    async def ssm_command(self, commands):

        async def wait_for_output(command_id):
            await _linear_sleep_async(1)
            response = await call_boto3_client_async('ssm', 'list_command_invocations', {
                'CommandId': command_id,
                'Details': True
            }, False)
            count = 0
            while response is None or 'CommandInvocations' not in response or len(response['CommandInvocations']) == 0:
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

        # --> 1. Validate instance is in running state
        if await self.instance_state != 'running':
            print('--> (ERROR) CANT EXECUTE SSM COMMAND UNLESS INSTANCE IN RUNNING STATE:', self.identifier)
            return None

        # --> 2. Validate SSM service is online
        if await self.instance_ssm_status != 'Online':
            print('--> (ERROR) CANT EXECUTE SSM COMMAND UNLESS INSTANCE SSM AGENT IS ONLINE:', self.identifier)
            return None

        # --> 3. Send command, get command_id
        if not isinstance(commands, list):
            commands = [commands]
        command_parameters = {
            'InstanceIds': [await self.instance_id],
            'DocumentName': 'AWS-RunShellScript',
            'Parameters': {
                'commands': commands
            }
        }
        command_id = await self._ssm(command_parameters)
        if command_id is None:
            print('--> (ERROR) SSM COMMAND WAS NOT ABLE TO BE SENT:', self.identifier, commands)
            return None

        # --> 4. Get output and strip
        output = await wait_for_output(command_id)
        return output.strip()

    async def container_running(self):
        command = 'docker ps -q | xargs'
        output = await self.ssm_command(command)
        if output is None or output == '':
            return False
        else:
            return True


    async def restart_container(self):
        return 0




