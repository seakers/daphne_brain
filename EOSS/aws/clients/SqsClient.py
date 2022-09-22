from EOSS.aws.utils import get_boto3_client
import json
import random
import botocore
import asyncio
import copy
from EOSS.aws.utils import _save_eosscontext, sync_to_async_mt, call_boto3_client_async


class SqsClient:

    def __init__(self, user_info):
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.eosscontext = user_info.eosscontext


    ####################
    ### Queue Exists ###
    ####################

    @staticmethod
    async def queue_exists_name(queue_name):
        list_response = await call_boto3_client_async('sqs', 'list_queues')
        if 'QueueUrls' in list_response:
            queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
            if queue_name in queue_names:
                return True
        return False

    @staticmethod
    async def queue_exists_url(queue_url):
        list_response = await call_boto3_client_async('sqs', 'list_queues')
        if 'QueueUrls' in list_response:
            queue_urls = list_response['QueueUrls']
            if queue_url in queue_urls:
                return True
        return False


    ####################
    ### Create Queue ###
    ####################

    @staticmethod
    async def create_queue_name_unique(queue_name):
        salt_name = ""
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # --> 1. Find unique queue name
        name_in_use = True
        while name_in_use is True:
            salt = "".join([random.choice(alphabet) for i in range(16)])
            salt_name = queue_name + '-' + salt
            name_in_use = await SqsClient.queue_exists_name(salt_name)

        # --> 2. Create queue and return url
        try:
            response = await call_boto3_client_async('sqs', 'create_queue', {
                "QueueName": salt_name,
                "tags": {
                    "ResourceGroup": "daphne-stack"
                }
            })
            return response['QueueUrl']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    @staticmethod
    async def create_queue_name(queue_name):
        if not await SqsClient.queue_exists_name(queue_name):
            response = await call_boto3_client_async('sqs', 'create_queue', {
                "QueueName": queue_name
            })
            queue_url = response['QueueUrl']
            return queue_url
        else:
            return await SqsClient.get_queue_url(queue_name)

    @staticmethod
    async def create_queue_url(queue_url):
        if not await SqsClient.queue_exists_url(queue_url):
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

    @staticmethod
    async def delete_queue_url(queue_url):
        try:
            await call_boto3_client_async('sqs', 'delete_queue', {
                "QueueUrl": queue_url
            })
        except botocore.exceptions.ClientError as error:
            print('--> ERROR DELETING QUEUE', error)
            return None

    ###################
    ### Purge Queue ###
    ###################

    @staticmethod
    async def purge_queue_url(queue_url):
        try:
            await call_boto3_client_async('sqs', 'purge_queue', {
                "QueueUrl": queue_url
            })
        except botocore.exceptions.ClientError as error:
            print('--> ERROR PURGING QUEUE', error)
            return None



    ###################
    ### Queue Facts ###
    ###################

    @staticmethod
    async def get_queue_url(queue_name):
        try:
            response = await call_boto3_client_async('sqs', 'get_queue_url', {
                "QueueName": queue_name
            })
            return response["QueueUrl"]
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    @staticmethod
    async def get_queue_arn(queue_url):
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



    #####################
    ### Send Messages ###
    #####################

    @staticmethod
    async def send_ping_msg(request_url, response_url=None):
        response = await call_boto3_client_async('sqs', 'send_message', {
            'QueueUrl': request_url,
            'MessageBody': 'boto3',
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'ping',
                    'DataType': 'String'
                },
            }
        })
        if response_url is not None:
            return await SqsClient.subscribe_to_message(response_url, 'statusAck')


    @staticmethod
    async def send_build_msg(request_url, response_url=None):
        response = await call_boto3_client_async('sqs', 'send_message', {
            'QueueUrl': request_url,
            'MessageBody': 'boto3',
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'build',
                    'DataType': 'String'
                }
            }
        })
        if response_url is not None:
            return await SqsClient.subscribe_to_message(response_url, 'build')

    @staticmethod
    async def send_exit_msg(request_url, response_url=None):
        response = await call_boto3_client_async('sqs', 'send_message', {
            'QueueUrl': request_url,
            'MessageBody': 'boto3',
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'exit',
                    'DataType': 'String'
                }
            }
        })
        if response_url is not None:
            return await SqsClient.subscribe_to_message(response_url, 'exit')


    @staticmethod
    async def send_eval_msg(request_url, design):
        response = await call_boto3_client_async('sqs', 'send_message', {
            'QueueUrl': request_url,
            'MessageBody': 'boto3',
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'build',
                    'DataType': 'String'
                }
            }
        })





    @staticmethod
    async def subscribe_to_message(response_queue, msg_type, attempts=5, attempt_time=5):
        subscription = {}
        break_switch = False
        for i in range(attempts):
            response = await call_boto3_client_async('sqs', 'receive_message', {
                'QueueUrl': response_queue,
                'MaxNumberOfMessages': 1,
                'WaitTimeSeconds': attempt_time,
                'MessageAttributeNames': ['All']
            })
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == msg_type:
                        subscription = copy.deepcopy(message["MessageAttributes"])
                        await call_boto3_client_async('sqs', 'delete_message', {
                            'QueueUrl': response_queue,
                            'ReceiptHandle': message["ReceiptHandle"]
                        })
                        break_switch = True
                if break_switch is True:
                    return subscription
        print('--> CONNECTION TIMEOUT ERROR')
        return {'msgType': 'timeout error'}




