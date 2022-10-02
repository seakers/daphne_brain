import os
import boto3
import asyncio

from EOSS.aws.instance.InstanceManager import InstanceManager
from EOSS.aws.utils import call_boto3_client_async, _save_eosscontext
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


    async def initialize(self, blocking=True):

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

        # --> Initialize
        async_tasks = []
        # async_tasks.append(asyncio.create_task(self.de_manager.initialize()))
        async_tasks.append(asyncio.create_task(self.de_manager.init_instances()))
        if blocking:
            for task in async_tasks:
                await task
        return True

    async def gather(self, blocking=True):
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.de_manager.gather_instances()))
        if blocking:
            for task in async_tasks:
                await task
        return True

    # --> Deprecated
    async def regulate_services(self):
        await self.de_manager.regulate_instances()



    async def build_vassar(self):
        await self.de_manager.build_instances(blocking=False)


    ############
    ### PING ###
    ############

    async def ping_services(self):

        async def add_to_survey(instance_manager, internal_survey, key):
            ping_result = await instance_manager.ping_instances()
            internal_survey[key] = ping_result

        survey = {
            'vassar_containers': [],
            'ga_containers': []
        }
        async_tasks = []
        async_tasks.append(asyncio.create_task(add_to_survey(self.de_manager, survey, 'vassar_containers')))
        for task in async_tasks:
            await task

        return survey



    #####################
    ### CONTROL PANEL ###
    #####################
    async def resource_msg(self, instance_ids, command, blocking=False):
        async_tasks = []
        async_tasks.append(asyncio.create_task(self.de_manager.resource_msg(instance_ids['vassar'], command)))
        if blocking:
            for task in async_tasks:
                await task



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
        return self.eosscontext.service_lock

    async def lock_services(self):
        print('\n\n-------- LOCKING SERVICES --------')
        self.eosscontext.service_lock = True
        await _save_eosscontext(self.eosscontext)

    async def unlock_services(self):
        print('-------- UNLOCKING SERVICES --------\n\n')
        self.eosscontext.service_lock = False
        await _save_eosscontext(self.eosscontext)




