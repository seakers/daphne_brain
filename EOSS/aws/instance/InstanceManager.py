import asyncio
import json

from functools import wraps
from types import FunctionType

from EOSS.aws.instance.DesignEvaluatorInstance import DesignEvaluatorInstance
from EOSS.aws.clients.InstanceClient import InstanceClient
from EOSS.aws.utils import _save_eosscontext



""" InstanceManager

    Purpose
    - Manage / regulate user ec2 instances for a specific service
    
    Services
    - design-evaluator
    - genetic-algorithm
        
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
    async def max_instances(self):
        if self.resource_type == 'design-evaluator':
            return 1
        elif self.resource_type == 'genetic-algorithm':
            return 1
        return 1

    @property
    async def can_start_instance(self):
        daphne_instance_limit = 300
        total_instances = len(await InstanceClient.get_daphne_instances())
        if total_instances > daphne_instance_limit:
            return False
        return True




    async def initialize(self):

        # --> 1. Gather current ec2 instances
        await self.gather_instances()

        # --> 2. Enforce 10 ec2 instances (only called once)
        await self.init_instances()

    async def gather_instances(self):
        self.instances = []

        # instance_list = await InstanceClient.get_user_active_instances(self.user_id, self.resource_type)
        instance_list, instance_status_info, instance_info = await InstanceClient.get_user_active_instances_all(self.user_id, self.resource_type)
        print('--> GATHERED INSTANCES', len(instance_list), len(instance_status_info), len(instance_info))

        for idx, instance in enumerate(instance_list):
            if self.resource_type == 'design-evaluator':
                self.instances.append(await self.create_instance(instance=instance_list[idx], instance_status_info=instance_status_info[idx], instance_info=instance_info[idx]))

        async_tasks = []
        for instance in self.instances:
            async_tasks.append(asyncio.create_task(instance.initialize()))

        for task in async_tasks:
            await task

    async def init_instances(self):
        print('--> init_instances')
        user_instance_limit = await self.max_instances
        current_count = len(self.instances)

        if current_count < user_instance_limit:
            # if (await self.can_start_instance) is False:
            #     print('--> CANNOT REGULATE INSTANCES, OVER GLOBAL INSTANCE LIMIT', self.resource_type)
            #     return None
            async_tasks = []
            for itr in range(current_count, user_instance_limit):
                instance = await self.create_instance()
                print(instance)
                async_tasks.append(asyncio.create_task(instance.initialize()))
                self.instances.append(instance)
            for task in async_tasks:
                await task

    async def create_instance(self, instance=None, instance_status_info=None, instance_info=None):
        if self.resource_type == 'design-evaluator':
            return DesignEvaluatorInstance(self.user_info, instance=instance, instance_status_info=instance_status_info, instance_info=instance_info)



    """
      _____                      _         _          _____              _                                
     |  __ \                    | |       | |        |_   _|            | |                               
     | |__) | ___   __ _  _   _ | |  __ _ | |_  ___    | |   _ __   ___ | |_  __ _  _ __    ___  ___  ___ 
     |  _  / / _ \ / _` || | | || | / _` || __|/ _ \   | |  | '_ \ / __|| __|/ _` || '_ \  / __|/ _ \/ __|
     | | \ \|  __/| (_| || |_| || || (_| || |_|  __/  _| |_ | | | |\__ \| |_| (_| || | | || (__|  __/\__ \
     |_|  \_\\___| \__, | \__,_||_| \__,_| \__|\___| |_____||_| |_||___/ \__|\__,_||_| |_| \___|\___||___/
                    __/ |                                                                                 
                   |___/                    
    - DEPRECATED
    """

    @property
    async def desired_running_count(self):
        desired_count = 0
        if self.resource_type == 'design-evaluator':
            desired_count = self.eosscontext.design_evaluator_task_count
        elif self.resource_type == 'genetic-algorithm':
            desired_count = self.eosscontext.genetic_algorithm_task_count
        else:
            print('--> INSTANCE TYPE NOT RECOGNIZED')
        return desired_count

    async def regulate_instances(self):
        if self.lock is True:
            print('--> COULD NOT REGULATE INSTANCES, SERVICE LOCKED:', self.resource_type)
            return None

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
            if (await instance_check.get_instance_state) == state_check:
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
            state = await instance_check.get_instance_state
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

    async def build_instances(self, blocking=True):
        running_instances = await self.get_instances_by_states(['pending', 'running'])

        async_tasks = []
        for instance in running_instances:
            async_tasks.append(asyncio.create_task(instance.build()))
        if blocking:
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

        print('--> INSTANCE MANAGER PINGING INSTANCES')

        async def ping_instance(local_instance, local_survey):
            instance_ping = await local_instance.ping()
            if instance_ping is not None:
                local_survey.append(instance_ping)

        survey = []
        async_tasks = []
        for instance in self.instances:
            async_tasks.append(asyncio.create_task(ping_instance(instance, survey)))
        for task in async_tasks:
            await task

        return survey






    #####################
    ### CONTROL PANEL ###
    #####################


    async def resource_msg(self, instance_ids, command):
        target_instances = [await self.get_instance_by_identifier(identifier) for identifier in instance_ids]
        async_tasks = []
        for instance in target_instances:
            if command == 'stop_instance':
                async_tasks.append(asyncio.create_task(instance.stop_instance()))
            elif command == 'start_instance':
                async_tasks.append(asyncio.create_task(instance.start_instance()))
            elif command == 'stop_container':
                async_tasks.append(asyncio.create_task(instance.stop_container()))
            elif command == 'start_container':
                async_tasks.append(asyncio.create_task(instance.start_container()))
            elif command == 'pull_container':
                async_tasks.append(asyncio.create_task(instance.pull_container()))
            elif command == 'build_container':
                async_tasks.append(asyncio.create_task(instance.build_container()))

    """
     _                   _    
    | |                 | |   
    | |      ___    ___ | | __
    | |     / _ \  / __|| |/ /
    | |____| (_) || (__ |   < 
    |______|\___/  \___||_|\_\  

    """

    @property
    async def lock(self):
        if self.resource_type == 'design-evaluator':
            return self.eosscontext.design_evaluator_service_lock
        elif self.resource_type == 'genetic-algorithm':
            return self.eosscontext.genetic_algorithm_service_lock
        return True

    async def lock_service(self):
        print('\n\n-------- LOCKING SERVICE', self.resource_type, '--------')
        if self.resource_type == 'design-evaluator':
            self.eosscontext.design_evaluator_service_lock = True
        elif self.resource_type == 'genetic-algorithm':
            self.eosscontext.genetic_algorithm_service_lock = True
        await _save_eosscontext(self.eosscontext)
        print('--> FINISHED LOCKING')

    async def unlock_service(self):
        print('-------- UNLOCKING SERVICE', self.resource_type, '--------\n\n')
        if self.resource_type == 'design-evaluator':
            self.eosscontext.design_evaluator_service_lock = False
        elif self.resource_type == 'genetic-algorithm':
            self.eosscontext.genetic_algorithm_service_lock = False
        await _save_eosscontext(self.eosscontext)
        print('--> FINISHED UNLOCKING')
