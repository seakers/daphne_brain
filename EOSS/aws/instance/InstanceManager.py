import asyncio
import json

from EOSS.aws.instance.DesignEvaluatorInstance import DesignEvaluatorInstance
from EOSS.aws.clients.InstanceClient import InstanceClient
from EOSS.aws.utils import _save_eosscontext




class InstanceManager:

    def __init__(self, user_info, resource_type='design-evaluator'):
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext
        self.resource_type = resource_type

        # --> List of (AbstractInstance) objects
        self.instances = []

    @property
    async def instance_limit(self):
        if self.resource_type == 'design-evaluator':
            return int(self.eosscontext.design_evaluator_instance_count)
        elif self.resource_type == 'genetic-algorithm':
            return int(self.eosscontext.genetic_algorithm_instance_count)
        return 1

    async def initialize(self):

        # --> 1. Find num instances to create
        user_instance_limit = await self.instance_limit
        current_count = len(self.instances)

        # --> 2. Check instances to be created
        if current_count >= user_instance_limit:
            return

        # --> 3. Create instances
        async_tasks = []
        for itr in range(current_count, user_instance_limit):

            # --> Create Instance
            instance = None
            if self.resource_type == 'design-evaluator':
                instance = DesignEvaluatorInstance(self.user_info)

            # --> Initialize Instance, add
            async_tasks.append(asyncio.create_task(instance.initialize()))
            self.instances.append(instance)
        for task in async_tasks:
            await task

    async def gather(self):

        async def create_instance(instance, instance_status_info, instance_ssm_info):
            if self.resource_type == 'design-evaluator':
                return DesignEvaluatorInstance(self.user_info, instance=instance,
                                               instance_status_info=instance_status_info,
                                               instance_ssm_info=instance_ssm_info)

        self.instances = []

        # --> 1. Get user instances
        user_instances, instance_status_info_list, instance_ssm_info_list = await InstanceClient.get_user_active_instances_all(self.user_id, self.resource_type)

        # --> 2. Instantiate each user instance
        for idx, instance in enumerate(user_instances):
            instance_status_info = instance_status_info_list[idx]
            instance_ssm_info = instance_ssm_info_list[idx]
            self.instances.append(await create_instance(instance, instance_status_info, instance_ssm_info))

        # --> 3. Initialize each user instance
        async_tasks = []
        for instance in self.instances:
            async_tasks.append(asyncio.create_task(instance.initialize()))
        for task in async_tasks:
            await task


    ########################
    ### INSTANCE GETTERS ###
    ########################

    async def get_instance_by_identifier(self, identifier):
        for instance in self.instances:
            if instance.identifier == identifier:
                return instance
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



    ############
    ### PING ###
    ############

    async def ping_instances(self):
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

    async def resource_msg(self, instance_ids, command, blocking=False):
        target_instances = [await self.get_instance_by_identifier(identifier) for identifier in instance_ids]
        results = []
        async_tasks = []
        for instance in target_instances:
            async_tasks.append(asyncio.create_task(self._resource_msg(instance, command, results)))
        if blocking is False:
            return []
        for task in async_tasks:
            await task
        return results

    async def _resource_msg(self, instance, command, results):
        func = getattr(instance, command)
        result = await func()
        results.append(result)





    ############
    ### LOCK ###
    ############

    @property
    async def lock(self):
        if self.resource_type == 'design-evaluator':
            return self.eosscontext.design_evaluator_service_lock
        elif self.resource_type == 'genetic-algorithm':
            return self.eosscontext.genetic_algorithm_service_lock
        return True

    async def lock_service(self):
        if self.resource_type == 'design-evaluator':
            self.eosscontext.design_evaluator_service_lock = True
        elif self.resource_type == 'genetic-algorithm':
            self.eosscontext.genetic_algorithm_service_lock = True
        await _save_eosscontext(self.eosscontext)

    async def unlock_service(self):
        if self.resource_type == 'design-evaluator':
            self.eosscontext.design_evaluator_service_lock = False
        elif self.resource_type == 'genetic-algorithm':
            self.eosscontext.genetic_algorithm_service_lock = False
        await _save_eosscontext(self.eosscontext)

