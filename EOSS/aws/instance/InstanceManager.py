import os
import boto3
import asyncio

from EOSS.aws.instance.DesignEvaluatorInstance import DesignEvaluatorInstance
from EOSS.aws.clients.InstanceClient import InstanceClient
from EOSS.aws.utils import call_boto3_client_async
from EOSS.aws.clients.SqsClient import SqsClient


""" InstanceManager
- Purpose of this class is to manage / regulate user ec2 instances for hosting containerized services

Services
- design-evaluator
- genetic-algorithm
    
AWS Functions
    1. run_instances()
    
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()
    
    
    
"""


class InstanceManager:

    def __init__(self, user_info, resource_type='design-evaluator'):
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext
        self.resource_type = resource_type

        # --> List of (AbstractInstance) objects
        self.instances = []


    @property
    async def desired_running_count(self):
        if self.resource_type == 'design-evaluator':
            return self.eosscontext.design_evaluator_task_count
        else:
            print('--> INSTANCE TYPE NOT RECOGNIZED')
        return 0

    @property
    async def user_instance_limit(self):
        if self.resource_type == 'design-evaluator':
            return 3
        return 1

    @property
    async def can_start_instance(self):
        daphne_instance_limit = 100
        total_instances = len(await InstanceClient.get_daphne_instances())
        if total_instances > daphne_instance_limit:
            return False
        return True



    async def initialize(self):

        # --> Gather the user's ec2 instances, regardless of state
        await self.gather_instances()

        # --> Enforce 10 ec2 instances, with the appropriate num running tasks
        await self.create_instances()

    async def gather_instances(self):
        self.instances = []

        instance_list = await InstanceClient.get_user_active_instances(self.user_id, self.resource_type)
        for instance in instance_list:
            if self.resource_type == 'design-evaluator':
                self.instances.append(DesignEvaluatorInstance(self.user_info, instance))

        async_tasks = []
        for instance in self.instances:
            async_tasks.append(
                asyncio.create_task(instance.initialize())
            )

        for task in async_tasks:
            await task

    async def create_instances(self):
        user_instance_limit = await self.user_instance_limit
        current_count = len(self.instances)

        if current_count < user_instance_limit:
            if (await self.can_start_instance) is False:
                raise Exception('--> CANNOT START INSTANCE, OVER INSTANCE LIMIT')
            async_tasks = []
            for itr in range(current_count, user_instance_limit):
                if self.resource_type == 'design-evaluator':
                    instance = DesignEvaluatorInstance(self.user_info, instance=None)
                    async_tasks.append(asyncio.create_task(instance.initialize()))
                    self.instances.append(instance)
            for task in async_tasks:
                await task


    """
      _____                      _         _          _____              _                                
     |  __ \                    | |       | |        |_   _|            | |                               
     | |__) | ___   __ _  _   _ | |  __ _ | |_  ___    | |   _ __   ___ | |_  __ _  _ __    ___  ___  ___ 
     |  _  / / _ \ / _` || | | || | / _` || __|/ _ \   | |  | '_ \ / __|| __|/ _` || '_ \  / __|/ _ \/ __|
     | | \ \|  __/| (_| || |_| || || (_| || |_|  __/  _| |_ | | | |\__ \| |_| (_| || | | || (__|  __/\__ \
     |_|  \_\\___| \__, | \__,_||_| \__,_| \__|\___| |_____||_| |_||___/ \__|\__,_||_| |_| \___|\___||___/
                    __/ |                                                                                 
                   |___/                    
    """


    async def regulate_instances(self):
        req_running = await self.desired_running_count

        stopped_instances = await self.get_instances_by_states(['stopped'])
        curr_stopped = len(stopped_instances)

        running_instances = await self.get_instances_by_states(['pending', 'running'])
        curr_running = len(running_instances)

        print('--> REGULATE INSTANCES:', curr_stopped, curr_running, req_running)


        async_tasks = []
        diff = abs(req_running - curr_running)
        if curr_running < req_running:
            print('--> STARTING', diff, 'INSTANCES')
            if curr_stopped >= diff:
                for idx in range(diff):
                    async_tasks.append(asyncio.create_task(stopped_instances[idx].start()))
            else:
                print('--> ERROR, NOT ENOUGH STOPPED INSTANCES', stopped_instances, diff)
        elif curr_running > req_running:
            print('--> STOPPING', diff, 'INSTANCES')
            if curr_running >= diff:
                for idx in range(diff):
                    async_tasks.append(asyncio.create_task(running_instances[idx].stop()))
            else:
                print('--> ERROR, NOT ENOUGH RUNNING INSTANCES', running_instances, diff)

        for task in async_tasks:
            await task

    async def get_instance_by_identifier(self, identifier):
        for instance in self.instances:
            if instance.identifier == identifier:
                return instance
        print('--> COULD NOT FIND INSTANCE BY IDENTIFIER:', identifier)
        return None

    async def get_instances_by_state(self, state):
        async def add_if_correct_state(instance_check, state_check, instance_list):
            if (await instance_check.instance_state) == state_check:
                instance_list.append(instance_check)

        search_instances = []
        async_tasks = []
        for instance in self.instances:
            async_tasks.append(
                asyncio.create_task(add_if_correct_state(instance, state, search_instances))
            )
        for task in async_tasks:
            await task
        return search_instances

    async def get_instances_by_states(self, states):
        async def add_if_correct_state(instance_check, state_check, instance_list):
            state = await instance_check.instance_state
            if state in state_check:
                instance_list.append(instance_check)

        search_instances = []
        async_tasks = []
        for instance in self.instances:
            async_tasks.append(
                asyncio.create_task(add_if_correct_state(instance, states, search_instances))
            )
        for task in async_tasks:
            await task
        return search_instances




    """
      ____        _ _     _ 
     |  _ \      (_) |   | |
     | |_) |_   _ _| | __| |
     |  _ <| | | | | |/ _` |
     | |_) | |_| | | | (_| |
     |____/ \__,_|_|_|\__,_|                 
    """

    async def build_instances(self):
        running_instances = await self.get_instances_by_states(['pending', 'running'])

        async_tasks = []
        for instance in running_instances:
            async_tasks.append(asyncio.create_task(instance.build()))
        for task in async_tasks:
            await task

    async def build_instance(self, identifier):
        instance = await self.get_instance_by_identifier(identifier)
        await instance.build()


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


    async def ping_instances(self):

        async def ping_instance(instance, survey):
            survey.append(await instance.ping())

        survey = []
        async_tasks = []
        running_instances = await self.get_instances_by_states(['running'])
        for instance in running_instances:
            async_tasks.append(asyncio.create_task(ping_instance(instance, survey)))
        for task in async_tasks:
            await task

        return survey

