import asyncio
import json
import time
import random
import string

from EOSS.aws.utils import call_boto3_client_async, find_obj_value, _linear_sleep_async
from EOSS.aws.clients.SqsClient import SqsClient







class AbstractInstance:

    def __init__(self, user_info, instance, instance_status_info, instance_ssm_info):
        if user_info.user is None:
            raise Exception("--> (error) AbstractInstance: User is not registered!")
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext

        # --> Local verion of instance
        self.instance = instance
        self.instance_status_info = instance_status_info
        self.instance_ssm_info = instance_ssm_info


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

        # --> 1. Create instance
        run_call = await call_boto3_client_async('ec2', 'run_instances', definition)

        # --> 2. Call wait in separate async thread
        print('--> WAITING ON CONTAINER RUNNING')
        result = await self.wait_on_container_running(attempts=10)
        await self.set_tag('RESOURCE_STATE', 'READY')
        print('--> CONTAINER READY:', self.identifier)


    async def initialize_ping_queues(self):
        self.ping_request_url = await SqsClient.create_queue_name(
            'user-' + str(self.user_id) + '-'+self.instance_type+'-ping-request-queue-' + self.identifier
        )
        self.ping_response_url = await SqsClient.create_queue_name(
            'user-' + str(self.user_id) + '-'+self.instance_type+'-ping-response-queue-' + self.identifier
        )

    async def initialize_private_queues(self):
        self.private_request_url = await SqsClient.create_queue_name(
            'user-' + str(self.user_id) + '-'+self.instance_type+'-private-request-queue-' + self.identifier
        )
        self.private_response_url = await SqsClient.create_queue_name(
            'user-' + str(self.user_id) + '-'+self.instance_type+'-private-response-queue-' + self.identifier
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

    async def get_instance_obj(self, debug=False):
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
                self.instance = None
            else:
                if len(request['Reservations'][0]['Instances']) == 0:
                    print('--> NO INSTANCES IN RESERVATION:', self.user_info.user, self.identifier)
                    self.instance = None
                else:
                    self.instance = request['Reservations'][0]['Instances'][0]
        return self.instance

    async def get_instance_status_obj(self):
        request = await call_boto3_client_async('ec2', 'describe_instance_status', {
            "InstanceIds": [await self.get_instance_id()]
        }, False)
        if request is None or 'InstanceStatuses' not in request or len(request['InstanceStatuses']) == 0:
            self.instance_status_info = None
        else:
            self.instance_status_info = request['InstanceStatuses'][0]
        return self.instance_status_info

    async def get_instance_ssm_info_obj(self):
        request = await call_boto3_client_async('ssm', 'describe_instance_information', {
            "Filters": [
                {
                    'Key': 'InstanceIds',
                    'Values': [await self.get_instance_id()]
                }
            ]
        }, True)
        if request is None or 'InstanceInformationList' not in request or len(request['InstanceInformationList']) == 0:
            self.instance_ssm_info = None
        else:
            self.instance_ssm_info = request['InstanceInformationList'][0]
        return self.instance_ssm_info

    async def get_resource_state(self, fetch=False):
        return await self.get_tag('RESOURCE_STATE', fetch=fetch)

    async def get_instance_id(self, fetch=False):
        if fetch or self.instance is None:
            await self.get_instance_obj()
        return self.instance['InstanceId']

    async def get_instance_state(self, fetch=False):
        if fetch or self.instance is None:
            await self.get_instance_obj()
        if self.instance is None:
            return 'Offline'
        else:
            return self.instance['State']['Name']

    async def get_instance_ipv4(self, fetch=False):
        if fetch or self.instance is None:
            await self.get_instance_obj()
        if self.instance is None:
            return 'Networking Off'
        if self.instance['State']['Name'] == 'running' and 'PublicIpAddress' in self.instance:
            return self.instance['PublicIpAddress']
        return 'Networking Off'

    async def get_instance_tags(self, fetch=False):
        if fetch or self.instance is None:
            await self.get_instance_obj()
        if self.instance is None:
            return []
        else:
            return self.instance['Tags']

    async def get_instance_status(self, fetch=False):
        if fetch or self.instance_status_info is None:
            await self.get_instance_status_obj()
        if self.instance_status_info is None:
            return 'Offline'
        else:
            return self.instance_status_info['InstanceStatus']['Status']

    async def get_system_status(self, fetch=False):
        if fetch or self.instance_status_info is None:
            await self.get_instance_status_obj()
        if self.instance_status_info is None:
            return 'Offline'
        else:
            return self.instance_status_info['SystemStatus']['Status']

    async def get_instance_ssm_status(self, fetch=False):
        if await self.get_instance_state() != 'running':
            return 'Offline'
        if fetch or self.instance_ssm_info is None:
            await self.get_instance_ssm_info_obj()
        if self.instance_ssm_info is None:
            return 'Offline'
        else:
            return self.instance_ssm_info['PingStatus']

    async def get_tag(self, tag, fetch=False):
        if fetch or self.instance is None:
            await self.get_instance_obj()
        if self.instance is None:
            return 'error'
        else:
            return await find_obj_value(self.instance['Tags'], 'Key', tag, 'Value')

    async def set_tag(self, tag, value):
        result = await call_boto3_client_async('ec2', 'create_tags', {
            'Resources': [await self.get_instance_id()],
            'Tags': [
                {
                    'Key': tag,
                    'Value': value
                }
            ]
        })



    """
     _____  _               
    |  __ \(_)              
    | |__) |_  _ __    __ _ 
    |  ___/| || '_ \  / _` |
    | |    | || | | || (_| |
    |_|    |_||_| |_| \__, |
                       __/ |
                      |___/ 
    """

    async def ping(self):
        ping_response = dict()
        ping_response['instance'] = await self._ping_instance()
        ping_response['container'] = await self._ping_container()
        ping_response['init_status'] = await self.get_tag('RESOURCE_STATE')
        print('--> PING INIT STATE:', self.identifier, ping_response['init_status'])
        return ping_response

    async def _ping_instance(self):
        return {
            'IDENTIFIER': self.identifier,
            'State': await self.get_instance_state(),
            'Status': await self.get_instance_status(),
            'SSMStatus': await self.get_instance_ssm_status(),
            'Tags': await self.get_instance_tags(),
            'Ipv4': await self.get_instance_ipv4()
        }

    async def _ping_container(self):
        info = {
            'Status':       '-------',
            'ProblemID':    '-------',
            'VassarStatus': '-------'
        }

        # --> Populate info
        if await self.get_instance_ssm_status() == 'Online' and await self.container_running():
            info['Status'] = 'Running'
            query = await SqsClient.send_ping_msg(self.ping_request_url, self.ping_response_url)
            if query and 'PROBLEM_ID' in query and 'status' in query:
                info['VassarStatus'] = query['status']['StringValue']
                info['PROBLEM_ID'] = query['PROBLEM_ID']['StringValue']
            else:
                info['VassarStatus'] = 'Booting'
                info['PROBLEM_ID'] = 'Booting'
        else:
            info['Status'] = 'Stopped'
        return info


    """
      _____                           _       
     / ____|                         | |      
    | |      ___   _ __   ___   ___  | |  ___ 
    | |     / _ \ | '_ \ / __| / _ \ | | / _ \
    | |____| (_) || | | |\__ \| (_) || ||  __/
     \_____|\___/ |_| |_||___/ \___/ |_| \___|
     
    """

    ################
    ### INSTANCE ###
    ################

    async def start_instance(self):

        # --> 1. Check if instance stopped
        if await self.get_instance_state() != 'stopped':
            return False

        # --> 2. Start instance
        response = await call_boto3_client_async('ec2', 'start_instances', {
            'InstanceIds': [await self.get_instance_id()]
        })

        # --> 3. Validate Start
        if response is not None and 'StartingInstances' in response and len(response['StartingInstances']) > 0:
            print('--> INSTANCE STARTING:', self.identifier)
            return True
        else:
            return False

    async def stop_instance(self):
        # --> 0. Try to stop via vassar inside
        # if await self.container_running():
        #     await SqsClient.send_exit_msg(self.private_request_url)
        #     if await self.wait_on_state('stopping', seconds=30):
        #         return {'identifier': self.identifier, 'result': True}

        # --> 1. Ensure instance state is running
        if await self.get_instance_state() not in ['running']:
            return False

        # --> 2. Stop instance
        response = await call_boto3_client_async('ec2', 'stop_instances', {
            'InstanceIds': [await self.get_instance_id()],
            'Hibernate': False
        })

        # --> 3. Validate Stop
        if response is not None and 'StoppingInstances' in response and len(response['StoppingInstances']) > 0:
            print('--> INSTANCE STOPPING:', self.identifier)
            return True
        else:
            return False

    async def hibernate_instance(self):

        # --> 1. Ensure instance either pending or running
        if await self.get_instance_state() not in ['running']:
            return False

        # --> 2. Stop instance
        response = await call_boto3_client_async('ec2', 'stop_instances', {
            'InstanceIds': [await self.get_instance_id()],
            'Hibernate': True
        })

        # --> 3. Validate Stop
        if response is not None and 'StoppingInstances' in response and len(response['StoppingInstances']) > 0:
            print('--> INSTANCE STOPPING:', self.identifier)
            return True
        else:
            return False


    #################
    ### CONTAINER ###
    #################

    async def run_container(self):
        response = await self.ssm_command([
            '. /home/ec2-user/run.sh'
        ])
        return response is not None

    async def stop_container(self):
        response = await self.ssm_command([
            '. /home/ec2-user/stop.sh'
        ])
        return response is not None

    async def update_container(self):
        response = await self.ssm_command([
            '. /home/ec2-user/update.sh'
        ])
        return response is not None



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

    async def wait_on_state(self, target_state='running', seconds=60):
        iter = 0
        iter_max = int(seconds/3)
        curr_state = await self.get_instance_state(fetch=True)
        while curr_state != target_state:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(3)
            curr_state = await self.get_instance_state(fetch=True)
        return True

    async def wait_on_states(self, target_states=['pending', 'running'], seconds=60):
        request_interval = 3
        iter = 0
        iter_max = int(seconds / request_interval)
        curr_state = await self.get_instance_state(fetch=True)
        while curr_state not in target_states:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(request_interval)
            curr_state = await self.get_instance_state(fetch=True)
        return True

    async def wait_on_status(self, target_status='ok', seconds=60):

        # --> 1. Wait for instance to be in running state
        curr_state = await self.get_instance_state(fetch=True)
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
        curr_status = await self.get_instance_status(fetch=True)
        while curr_status != target_status:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(sleep_time)
            curr_status = await self.get_instance_status(fetch=True)
        return True

    async def wait_on_ssm_status(self, target_status='Online', seconds=60):
        request_interval = 3
        iter = 0
        iter_max = int(seconds / request_interval)
        curr_status = await self.get_instance_ssm_status(fetch=True)
        while curr_status != target_status:
            iter += 1
            if iter >= iter_max:
                return False
            await _linear_sleep_async(request_interval)
            curr_status = await self.get_instance_ssm_status(fetch=True)
        return True

    async def wait_on_container_running(self, attempts=5):
        request_interval = 5
        iter = 0
        iter_max = attempts
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
                await _linear_sleep_async(4)
                response = await call_boto3_client_async('ssm', 'list_command_invocations', {
                    'CommandId': command_id,
                    'Details': True
                })
                count += 1
                if count > 5:
                    return ''
            output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
            return output

        # --> 1. Validate instance is in running state
        if await self.get_instance_state() != 'running':
            return None

        # --> 2. Validate SSM service is online
        if await self.get_instance_ssm_status() != 'Online':
            return None

        # --> 3. Send command, get command_id
        if not isinstance(commands, list):
            commands = [commands]
        command_parameters = {
            'InstanceIds': [await self.get_instance_id()],
            'DocumentName': 'AWS-RunShellScript',
            'Parameters': {
                'commands': commands
            }
        }
        command_id = await self._ssm(command_parameters)
        if command_id is None:
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

