import os
import boto3

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


    async def initialize(self):

        # --> Service: design-evaluator
        if self.eosscontext.design_evaluator_request_queue_name is None:
            queue_name = 'user-' + str(self.user_id) + '-design-evaluator-request-queue'
            self.eosscontext.design_evaluator_request_queue_name = queue_name
            self.eosscontext.design_evaluator_request_queue_url = await SqsClient.create_queue_name(queue_name)
        if self.eosscontext.design_evaluator_response_queue_name is None:
            queue_name = 'user-' + str(self.user_id) + '-design-evaluator-response-queue'
            self.eosscontext.design_evaluator_response_queue_name = queue_name
            self.eosscontext.design_evaluator_response_queue_url = await SqsClient.create_queue_name(queue_name)

        # --> Service: genetic-algorithm
        # --> Save
        await _save_eosscontext(self.eosscontext)

        # --> Initialize Managers
        await self.de_manager.initialize()




