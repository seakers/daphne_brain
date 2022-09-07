from EOSS.aws.utils import get_boto3_client
import json
import random
import botocore
import asyncio
from EOSS.aws.utils import _save_eosscontext, sync_to_async_mt, call_boto3_client_async


class SqsClient:

    def __init__(self, user_info):
        print('--> CREATING SQS CLIENT')
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.eoss_context = user_info.eoss_context
        self.sqs_client = get_boto3_client('sqs')

        # --> Queue Info: user eval queues
        self.design_evaluator_request_queue_name = self.eoss_context.design_evaluator_request_queue_name
        self.design_evaluator_request_queue_url = self.eoss_context.design_evaluator_request_queue_url
        self.design_evaluator_request_queue_arn = self.eoss_context.design_evaluator_request_queue_arn

        self.design_evaluator_response_queue_name = self.eoss_context.design_evaluator_response_queue_name
        self.design_evaluator_response_queue_url = self.eoss_context.design_evaluator_response_queue_url
        self.design_evaluator_response_queue_arn = self.eoss_context.design_evaluator_response_queue_arn

        """ -- User Specific --> Instance Specific Queues -- 
        
            Eval Container - Instance Specific Queues (user_id: 1) (instance: 1)
            1. user-1-design-evaluator-1-private-request-queue
            2. user-1-design-evaluator-1-private-response-queue
            
            GA Container - Instance Specific Queues (user_id: 1) (instance: 1)
            3. user-1-genetic-algorithm-1-request-queue
            4. user-1-genetic-algorithm-1-response-queue
        """

    # --> This is called to ensure all user-specific queues are created
    async def initialize(self):

        # --> Initialize Queues
        if self.design_evaluator_request_queue_name is None:
            self.design_evaluator_request_queue_name = 'user-' + str(self.user_id) + '-design-evaluator-request-queue'
        if self.design_evaluator_request_queue_url is None:
            self.design_evaluator_request_queue_url = await self.create_queue_name(
                self.design_evaluator_request_queue_name)
        self.design_evaluator_request_queue_arn = await self.get_queue_arn(self.design_evaluator_request_queue_url)

        if self.design_evaluator_response_queue_name is None:
            self.design_evaluator_response_queue_name = 'user-' + str(self.user_id) + '-design-evaluator-response-queue'
        if self.design_evaluator_response_queue_url is None:
            self.design_evaluator_response_queue_url = await self.create_queue_name(
                self.design_evaluator_response_queue_name)
        self.design_evaluator_response_queue_arn = await self.get_queue_arn(self.design_evaluator_response_queue_url)

        return await self.commit_db()
    async def commit_db(self):
        self.eoss_context.design_evaluator_request_queue_name = self.design_evaluator_request_queue_name
        self.eoss_context.design_evaluator_request_queue_url = self.design_evaluator_request_queue_url
        self.eoss_context.design_evaluator_request_queue_arn = self.design_evaluator_request_queue_arn

        self.eoss_context.design_evaluator_response_queue_name = self.design_evaluator_response_queue_name
        self.eoss_context.design_evaluator_response_queue_url = self.design_evaluator_response_queue_url
        self.eoss_context.design_evaluator_response_queue_arn = self.design_evaluator_response_queue_arn

        await _save_eosscontext(self.eoss_context)

    ####################
    ### Queue Exists ###
    ####################

    async def queue_exists_name(self, queue_name):
        list_response = await call_boto3_client_async('sqs', 'list_queues')
        if 'QueueUrls' in list_response:
            queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
            if queue_name in queue_names:
                return True
        return False

    async def queue_exists_url(self, queue_url):
        list_response = await call_boto3_client_async('sqs', 'list_queues')
        if 'QueueUrls' in list_response:
            queue_urls = list_response['QueueUrls']
            if queue_url in queue_urls:
                return True
        return False


    ####################
    ### Create Queue ###
    ####################


    async def create_queue_name_unique(self, queue_name):
        salt_name = ""
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # --> 1. Find unique queue name
        name_in_use = True
        while name_in_use is True:
            salt = "".join([random.choice(alphabet) for i in range(16)])
            salt_name = queue_name + '-' + salt
            name_in_use = await self.queue_exists_name(salt_name)

        # --> 2. Create queue and return url
        try:
            response = await call_boto3_client_async('sqs', 'create_queue', {
                "QueueName": salt_name
            })
            return response['QueueUrl']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None


    async def create_queue_name(self, queue_name):
        if not await self.queue_exists_name(queue_name):
            response = await call_boto3_client_async('sqs', 'create_queue', {
                "QueueName": queue_name
            })
            queue_url = response['QueueUrl']
            return queue_url
        else:
            return await self.get_queue_url(queue_name)

    async def create_queue_url(self, queue_url):
        if not await self.queue_exists_url(queue_url):
            queue_name = SqsClient.get_queue_name_from_url(queue_url)
            response = await call_boto3_client_async('sqs', 'create_queue', {
                "QueueName": queue_name
            })
            return response['QueueUrl']
        else:
            return queue_url


    ####################
    ### Delete Queue ###
    ####################


    async def delete_queue_url(self, queue_url):
        try:
            await call_boto3_client_async('sqs', 'delete_queue', {
                "QueueUrl": queue_url
            })
        except botocore.exceptions.ClientError as error:
            print('--> ERROR DELETING QUEUE', error)
            return None


    ###################
    ### Queue Facts ###
    ###################


    async def get_queue_url(self, queue_name):
        try:
            response = await sync_to_async_mt(self.sqs_client.get_queue_url)(QueueName=queue_name)
            response = await call_boto3_client_async('sqs', 'get_queue_url', {
                "QueueName": queue_name
            })
            return response["QueueUrl"]
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    async def get_queue_arn(self, queue_url):
        try:
            response = await call_boto3_client_async('sqs', 'get_queue_attributes', {
                "QueueUrl": queue_url,
                "AttributeNames": ["QueueArn"]
            })
            return response["Attributes"]["QueueArn"]
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None


    ###############
    ### Helpers ###
    ###############

    @staticmethod
    async def get_queue_name_from_url(queue_url):
        return queue_url.split("/")[-1]


