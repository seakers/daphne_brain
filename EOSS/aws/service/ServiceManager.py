import asyncio
import json

from EOSS.aws.utils import _save_eosscontext
from EOSS.aws.instance.InstanceManager import InstanceManager
from EOSS.aws.clients.SqsClient import SqsClient

from daphne_context.models import UserInformation




class ServiceManager:


    def __init__(self, user_info: UserInformation):
        if user_info.user is None or user_info.eosscontext is None:
            raise Exception("--> ServiceManager requires a registered user!")
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.eosscontext = user_info.eosscontext

        # --> Instance Managers
        self.de_manager = InstanceManager(self.user_info, 'design-evaluator')
        self.ga_manager = InstanceManager(self.user_info, 'genetic-algorithm')


    async def initialize(self, blocking=True):

        # --> 1. Create user resources (queues, etc...)
        save = False
        if self.eosscontext.design_evaluator_request_queue_name is None:
            queue_name = 'user-' + str(self.user_id) + '-design-evaluator-request-queue'
            self.eosscontext.design_evaluator_request_queue_name = queue_name
            self.eosscontext.design_evaluator_request_queue_url = await SqsClient.create_queue_name(queue_name)
            save = True
        if self.eosscontext.design_evaluator_response_queue_name is None:
            queue_name = 'user-' + str(self.user_id) + '-design-evaluator-response-queue'
            self.eosscontext.design_evaluator_response_queue_name = queue_name
            self.eosscontext.design_evaluator_response_queue_url = await SqsClient.create_queue_name(queue_name)
            save = True
        if save:
            await _save_eosscontext(self.eosscontext)

        # --> 2. Initialize Managers
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.de_manager.initialize()))
        async_tasks.append(asyncio.create_task(self.ga_manager.initialize()))
        if blocking:
            for task in async_tasks:
                await task
        return True

    async def gather(self, blocking=True):

        # --> 1. Gather Managers
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.de_manager.gather()))
        async_tasks.append(asyncio.create_task(self.ga_manager.gather()))
        if blocking:
            for task in async_tasks:
                await task
        return True


    ############
    ### PING ###
    ############

    async def ping_services(self):

        async def add_to_survey(instance_manager, internal_survey, key):
            ping_result = await instance_manager.ping_instances()
            internal_survey[key] = ping_result

        survey = {
            'vassar': [],
            'ga': []
        }
        async_tasks = []
        async_tasks.append(asyncio.create_task(add_to_survey(self.de_manager, survey, 'vassar')))
        async_tasks.append(asyncio.create_task(add_to_survey(self.ga_manager, survey, 'ga')))
        for task in async_tasks:
            await task

        return survey



    #####################
    ### CONTROL PANEL ###
    #####################

    async def resource_msg(self, instance_ids, command, blocking=False):
        results = {
            'vassar': [],
            'ga': []
        }
        async_tasks = []
        async_tasks.append(
            asyncio.create_task(
                self._resource_msg(self.de_manager, instance_ids['vassar'], command, results, 'vassar')
            )
        )
        async_tasks.append(
            asyncio.create_task(
                self._resource_msg(self.ga_manager, instance_ids['ga'], command, results, 'ga')
            )
        )
        if blocking is False:
            return {}
        for task in async_tasks:
            await task
        return results

    async def _resource_msg(self, manager, instance_ids, command, results, key):
        result = await manager.resource_msg(instance_ids, command, blocking=True)
        results[key] = result



    ############
    ### LOCK ###
    ############

    @property
    async def lock(self):
        return self.eosscontext.service_lock

    async def lock_services(self):
        self.eosscontext.service_lock = True
        await _save_eosscontext(self.eosscontext)

    async def unlock_services(self):
        self.eosscontext.service_lock = False
        await _save_eosscontext(self.eosscontext)




