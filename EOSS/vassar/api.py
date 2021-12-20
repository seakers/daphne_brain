import asyncio
import concurrent.futures
import json
import os
from asgiref.sync import sync_to_async, async_to_sync
import boto3
import random
import threading
import EOSS

from django.conf import settings

from EOSS.models import EOSSContext

from EOSS.graphql.api import GraphqlClient
from EOSS.aws.utils import get_boto3_client
from EOSS.aws.EvalQueue import EvalQueue
from daphne_context.models import UserInformation
from daphne_ws.async_db_methods import sync_to_async_mt

from asgiref.sync import async_to_sync, sync_to_async
from EOSS.graphql.client.Dataset import DatasetGraphqlClient
from EOSS.graphql.client.Admin import AdminGraphqlClient
from EOSS.graphql.client.Problem import ProblemGraphqlClient

ACCESS_KEY = 'AKIAJVM34C5MCCWRJCCQ'
SECRET_KEY = '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'

def bool_list_to_string(bool_list_str):
    bool_list = json.loads(bool_list_str)
    print("--> bool_list_to_string", bool_list)
    return_str = ''
    for bool_pos in bool_list:
        if bool_pos:
            return_str = return_str + '1'
        else:
            return_str = return_str + '0'
    return return_str

def boolean_string_to_boolean_array(boolean_string):
    return [b == "1" for b in boolean_string]


class ObjectiveSatisfaction:
    def __init__(self, objective_name, satisfaction, weight):
        self.objective_name = objective_name
        self.satisfaction = satisfaction
        self.weight = weight



class VASSARClient:
    
    def __init__(self, user_information: UserInformation):
        self.user_id = user_information.user.id
        self.user_information = user_information

        self.dataset_client = DatasetGraphqlClient(self.user_information)
        self.problem_client = ProblemGraphqlClient(self.user_information)

        # Boto3
        self.queue_name = 'test_queue'
        self.region_name = 'us-east-2'

        # self.sqs = prod_client('sqs')
        self.sqs_client = get_boto3_client('sqs')

        self.sqs = boto3.resource('sqs', region_name=self.region_name)
        # self.sqs_client = boto3.client('sqs', endpoint_url='http://localstack:4576', region_name=self.region_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Graphql Client
        self.dbClient = GraphqlClient(user_info=user_information)

        # Queue Client
        self.queue_client = EvalQueue()


    async def send_connect_message(self, url, group_id=None, problem_id=None):
        msg_attributes = {
            'msgType': {
                'StringValue': 'connectionRequest',
                'DataType': 'String'
            },
            'user_id': {
                'StringValue': str(self.user_id),
                'DataType': 'String'
            },
        }
        if group_id is not None:
            msg_attributes['group_id'] = {
                    'StringValue': str(group_id),
                    'DataType': 'String'
                }
        if problem_id is not None:
            msg_attributes['problem_id'] = {
                    'StringValue': str(problem_id),
                    'DataType': 'String'
                }
        # Send init message
        response = await sync_to_async_mt(self.sqs_client.send_message)(
            QueueUrl=url,
            MessageBody='boto3',
            MessageAttributes=msg_attributes)

    async def connect_to_vassar(self, request_url, response_url, max_retries):
        # Send init message
        user_request_queue_url = ""
        user_response_queue_url = ""

        success = False
        retries = 0
        has_called_aws = False

        while not success and retries < max_retries:
            retries += 1
            user_request_queue_url, user_response_queue_url, container_uuid = await self.vassar_connection_loop(response_url)

            if user_request_queue_url == "" and user_response_queue_url == "":
                # If it does not work, and we are on AWS, try increasing Service task limits
                if settings.DEPLOYMENT_TYPE == "aws" and not has_called_aws:
                    has_called_aws = True
                    ecs_client = get_boto3_client('ecs')
                    cluster_arn = os.environ["CLUSTER_ARN"]
                    service_arn = os.environ["VASSAR_SERVICE_ARN"]
                    current_count = await sync_to_async_mt(ecs_client.describe_services)(cluster=cluster_arn, services=[service_arn])["services"][0]["desiredCount"]
                    if current_count < 30:
                        await sync_to_async_mt(ecs_client.update_service)(cluster=cluster_arn, service=service_arn, desiredCount=current_count+1)
                        # Wait for a while for instance to start before trying to connect again
                        asyncio.sleep(10)
            else:
                success = True
            
        return user_request_queue_url, user_response_queue_url, container_uuid, success
    
    async def vassar_connection_loop(self, response_url):
        user_request_queue_url = ""
        user_response_queue_url = ""
        vassar_container_uuid = ""
        # Try at most 5 times
        for i in range(5):
            response = await sync_to_async_mt(self.sqs_client.receive_message)(
                QueueUrl=response_url,
                MaxNumberOfMessages=3,
                WaitTimeSeconds=2,
                MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "isAvailable" and message["MessageAttributes"]["user_id"]["StringValue"] == str(self.user_id):
                        print("Received message attributes:", message["MessageAttributes"])
                        # 1. Get queue URLs
                        user_request_queue_url = message["MessageAttributes"]["request_queue_url"]["StringValue"]
                        user_response_queue_url = message["MessageAttributes"]["response_queue_url"]["StringValue"]
                        vassar_container_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        # 2. Send ACK message
                        response = await sync_to_async_mt(self.sqs_client.send_message)(
                            QueueUrl=user_request_queue_url,
                            MessageBody='boto3',
                            MessageAttributes=
                            {
                                'msgType': {
                                    'StringValue': 'connectionAck',
                                    'DataType': 'String'
                                },
                                'UUID': {
                                    'StringValue': vassar_container_uuid,
                                    'DataType': 'String'
                                }
                            })
                        # 3. Save information to database 
                        await sync_to_async(self._initialize_vassar)(user_request_queue_url, user_response_queue_url, vassar_container_uuid)
                        # 4. Delete Message from queue
                        await sync_to_async_mt(self.sqs_client.delete_message)(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if user_request_queue_url != "" and user_response_queue_url != "":
                break
        
        return user_request_queue_url, user_response_queue_url, vassar_container_uuid

    def _uninitialize_vassar(self):
        self.user_information.eosscontext.vassar_information = {}
        self.user_information.eosscontext.save()

    def _initialize_vassar(self, vassar_request_queue_url, vassar_response_queue_url, vassar_container_uuid):
        self.user_information.eosscontext.vassar_request_queue_url = vassar_request_queue_url
        self.user_information.eosscontext.vassar_response_queue_url = vassar_response_queue_url
        self.user_information.eosscontext.vassar_information = { "containers": { vassar_container_uuid: { "ready": True } } }
        self.user_information.eosscontext.save()

    def _mark_vassar_as_ready(self, vassar_container_uuid):
        self.user_information.eosscontext.vassar_information["containers"][vassar_container_uuid]["ready"] = True
        self.user_information.eosscontext.save()

    def _update_problem_info(self, problem_id, group_id, dataset_id):
        self.user_information.eosscontext.problem_id = problem_id
        self.user_information.eosscontext.group_id = group_id
        self.user_information.eosscontext.dataset_id = dataset_id
        self.user_information.eosscontext.save()


    async def rebuild_vassar(self, group_id, problem_id, dataset_id):
        await sync_to_async(self._update_problem_info)(problem_id, group_id, dataset_id)
        msg_attributes = {
            'msgType': {
                'StringValue': 'build',
                'DataType': 'String'
            },
            'user_id': {
                'StringValue': str(self.user_id),
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': str(group_id),
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': str(problem_id),
                'DataType': 'String'
            }
        }
        # Send rebuild message
        await sync_to_async_mt(self.sqs_client.send_message)(
            QueueUrl=self.user_information.eosscontext.vassar_request_queue_url,
            MessageBody='boto3',
            MessageAttributes=msg_attributes)
        # Wait for rebuild message response
        # Try at most 20 times
        for i in range(20):
            response = await sync_to_async_mt(self.sqs_client.receive_message)(
                QueueUrl=self.user_information.eosscontext.vassar_response_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=1,
                MessageAttributeNames=["All"])
            response_received = False
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "buildDone":
                        print("Received message attributes:", message["MessageAttributes"])
                        response_received = True
                    else:
                        # Return message to queue
                        await sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=self.user_information.eosscontext.vassar_response_queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if response_received:
                break
        return response_received

    async def connect_to_ga(self, request_url, response_url, vassar_request_url, max_retries):
        # Send init message
        user_request_queue_url = ""
        user_response_queue_url = ""

        success = False
        retries = 0
        has_called_aws = False

        while not success and retries < max_retries:
            retries += 1
            user_request_queue_url, user_response_queue_url = await self.ga_connection_loop(response_url, vassar_request_url)

            # If it does not work, and we are on AWS, try increasing Service task limits
            if user_request_queue_url == "" and user_response_queue_url == "":
                if settings.DEPLOYMENT_TYPE == "aws" and not has_called_aws:
                    has_called_aws = True
                    ecs_client = get_boto3_client('ecs')
                    cluster_arn = os.environ["CLUSTER_ARN"]
                    service_arn = os.environ["GA_SERVICE_ARN"]
                    current_count = await sync_to_async_mt(ecs_client.describe_services)(cluster=cluster_arn, services=[service_arn])["services"][0]["desiredCount"]
                    if current_count < 30:
                        await sync_to_async_mt(ecs_client.update_service)(cluster=cluster_arn, service=service_arn, desiredCount=current_count+1)
                        # Wait for a while for instance to start before trying to connect again
                        asyncio.sleep(10)
            else:
                success = True

            
        return user_request_queue_url, user_response_queue_url, success

    async def ga_connection_loop(self, response_url, vassar_request_url):
        user_request_queue_url = ""
        user_response_queue_url = ""
        # Try at most 5 times
        for i in range(5):
            response = await sync_to_async_mt(self.sqs_client.receive_message)(
                QueueUrl=response_url,
                MaxNumberOfMessages=3,
                WaitTimeSeconds=2,
                MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "isAvailable" and message["MessageAttributes"]["user_id"]["StringValue"] == str(self.user_id):
                        print("Received message attributes:", message["MessageAttributes"])
                        # 1. Get queue URLs
                        user_request_queue_url = message["MessageAttributes"]["request_queue_url"]["StringValue"]
                        user_response_queue_url = message["MessageAttributes"]["response_queue_url"]["StringValue"]
                        container_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        # 2. Send ACK message
                        response = await sync_to_async_mt(self.sqs_client.send_message)(
                            QueueUrl=user_request_queue_url, 
                            MessageBody='boto3',
                            MessageAttributes=
                            {
                                'msgType': {
                                    'StringValue': 'connectionAck',
                                    'DataType': 'String'
                                },
                                'UUID': {
                                    'StringValue': container_uuid,
                                    'DataType': 'String'
                                },
                                'vassar_url': {
                                    'StringValue': vassar_request_url,
                                    'DataType': 'String'
                                }
                            })
                        # 3. Save information to database 
                        await sync_to_async(self._initialize_ga)(user_request_queue_url, user_response_queue_url, container_uuid)
                        # 4. Delete Message from queue
                        await sync_to_async_mt(self.sqs_client.delete_message)(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        await sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if user_request_queue_url != "" and user_response_queue_url != "":
                break
        
        return user_request_queue_url, user_response_queue_url

    def _uninitialize_ga(self):
        self.user_information.eosscontext.ga_information = {}
        self.user_information.eosscontext.save()

    def _initialize_ga(self, ga_request_queue_url, ga_response_queue_url, ga_container_uuid):
        self.user_information.eosscontext.ga_request_queue_url = ga_request_queue_url
        self.user_information.eosscontext.ga_response_queue_url = ga_response_queue_url
        self.user_information.eosscontext.ga_information = { "containers": { ga_container_uuid: { "ready": True } } }
        self.user_information.eosscontext.save()
    
    # working
    async def send_initialize_message(self, url, group_id, problem_id):
        # Send init message
        response = await sync_to_async_mt(self.sqs_client.send_message)(
            QueueUrl=url,
            MessageBody='boto3',
            MessageAttributes={
                'msgType': {
                    'StringValue': 'build',
                    'DataType': 'String'
                },
                'group_id': {
                    'StringValue': str(group_id),
                    'DataType': 'String'
                },
                'problem_id': {
                    'StringValue': str(problem_id),
                    'DataType': 'String'
                }
            })
        print(response)

    async def receive_successful_build(self, url, container_uuid, max_retries):
        # Receive initialization complete message
        build_success = False
        retries = 0
        while not build_success and retries < max_retries:
            retries += 1
            for i in range(5):
                response = await sync_to_async_mt(self.sqs_client.receive_message)(
                    QueueUrl=url,
                    MaxNumberOfMessages=3,
                    WaitTimeSeconds=2,
                    MessageAttributeNames=["All"])
                if "Messages" in response:
                    for message in response["Messages"]:
                        if message["MessageAttributes"]["msgType"]["StringValue"] == "isReady":
                            # 1. Save information to database
                            await sync_to_async(self._mark_vassar_as_ready)(container_uuid)
                            # 2. Delete Message from queue
                            await sync_to_async_mt(self.sqs_client.delete_message)(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])
                            build_success = True
                        else:
                            # Return message to queue
                            await sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
                if build_success:
                    break
        return build_success

    async def check_status(self, request_queue, response_queue):
        # Send status check message
        response = await sync_to_async_mt(self.sqs_client.send_message)(
            QueueUrl=request_queue,
            MessageBody='boto3',
            MessageAttributes={
                'msgType': {
                    'StringValue': 'statusCheck',
                    'DataType': 'String'
                }
            })
        # Try at most 10 times
        current_status = ""
        current_timestamp = 0
        current_uuid = None
        for i in range(10):
            response = await sync_to_async_mt(self.sqs_client.receive_message)(
                QueueUrl=response_queue,
                MaxNumberOfMessages=3,
                WaitTimeSeconds=1,
                MessageAttributeNames=["All"],
                AttributeNames=["SentTimestamp"])
            if "Messages" in response:
                for message in response["Messages"]:
                    print (message["MessageAttributes"])
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "currentStatus":
                        # 1. Get current status
                        receive_time = int(message["Attributes"]["SentTimestamp"])
                        if receive_time > current_timestamp:
                            current_status = message["MessageAttributes"]["current_status"]["StringValue"]
                            current_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                            current_timestamp = receive_time
                        # 4. Delete Message from queue
                        await sync_to_async_mt(self.sqs_client.delete_message)(
                            QueueUrl=response_queue,
                            ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        await sync_to_async_mt(self.sqs_client.change_message_visibility)(
                            QueueUrl=response_queue,
                            ReceiptHandle=message["ReceiptHandle"],
                            VisibilityTimeout=1)
        if current_status == "":
            current_status = "waiting_for_user"
        print("--------- Current status:", current_status)
        return current_status, current_uuid

    async def create_dead_queue(self, queue_name):
        response = await sync_to_async_mt(self.sqs_client.create_queue)(
            QueueName=queue_name
        )
        print('---> CREATE QUEUE RESPONSE', response)
        queue_url = response['QueueUrl']
        arn_response = await sync_to_async_mt(self.sqs_client.get_queue_attributes)(
            QueueUrl=queue_url,
            AttributeNames=["QueueArn"]
        )
        queue_arn = arn_response["Attributes"]["QueueArn"]
        return queue_url, queue_arn

    async def create_queue(self, queue_name, dead_letter_arn):
        attributes = {
            "MessageRetentionPeriod": str(60*5),
            "RedrivePolicy": json.dumps({
                "deadLetterTargetArn": dead_letter_arn,
                "maxReceiveCount": "3"
            })
        }
        response = await sync_to_async_mt(self.sqs_client.create_queue)(
            QueueName=queue_name,
            Attributes=attributes
        )
        print('---> CREATE QUEUE RESPONSE', response)
        queue_url = response['QueueUrl']
        await sync_to_async_mt(self.sqs_client.set_queue_attributes)(
            QueueUrl=queue_url,
            Attributes=attributes
        )
        
        return queue_url

    async def queue_exists(self, queue_url):
        list_response = await sync_to_async_mt(self.sqs_client.list_queues)()
        if 'QueueUrls' in list_response:
            queue_urls = list_response['QueueUrls']
            if queue_url in queue_urls:
                return True
        return False

    async def queue_exists_by_name(self, queue_name):
        list_response = await sync_to_async_mt(self.sqs_client.list_queues)()
        if 'QueueUrls' in list_response:
            queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
            if queue_name in queue_names:
                return True
        return False

    async def get_queue_url(self, queue_name):
        response = await sync_to_async_mt(self.sqs_client.get_queue_url)(QueueName=queue_name)
        return response["QueueUrl"]

    async def get_queue_arn(self, queue_url):
        response = await sync_to_async_mt(self.sqs_client.get_queue_attributes)(QueueUrl=queue_url, AttributeNames=["QueueArn"])
        return response["Attributes"]["QueueArn"]

    async def send_ping_message(self):
        vassar_request_url = self.user_information.eosscontext.vassar_request_queue_url
        vassar_response_url = self.user_information.eosscontext.vassar_response_queue_url
        vassar_information = self.user_information.eosscontext.vassar_information
        ga_request_url = self.user_information.eosscontext.ga_request_queue_url
        ga_response_url = self.user_information.eosscontext.ga_response_queue_url
        ga_information = self.user_information.eosscontext.ga_information

        if vassar_request_url is not None and await self.queue_exists(vassar_request_url) and "containers" in vassar_information:
            print("Pinging VASSAR Containers")
            for container_uuid, container_info in vassar_information["containers"].items():
                response = await sync_to_async_mt(self.sqs_client.send_message)(QueueUrl=vassar_request_url, MessageBody='boto3', MessageAttributes={
                                    'msgType': {
                                        'StringValue': 'ping',
                                        'DataType': 'String'
                                    },
                                    'UUID': {
                                        'StringValue': container_uuid,
                                        'DataType': 'String'
                                    },
                                })
        
        if ga_request_url is not None and await self.queue_exists(ga_request_url) and "containers" in ga_information:
            print("Pinging GA Containers")
            for container_uuid, container_info  in ga_information["containers"].items():
                response = await sync_to_async_mt(self.sqs_client.send_message)(QueueUrl=ga_request_url, MessageBody='boto3', MessageAttributes={
                                    'msgType': {
                                        'StringValue': 'ping',
                                        'DataType': 'String'
                                    },
                                    'UUID': {
                                        'StringValue': container_uuid,
                                        'DataType': 'String'
                                    },
                                })

        print("Receiving Ping Responses")
        container_statuses = {"vassar": {}, "ga": {}}
        if vassar_request_url is not None and await self.queue_exists(vassar_request_url) and "containers" in vassar_information:
            for container_uuid, container_info in vassar_information["containers"].items():
                container_statuses["vassar"][container_uuid] = asyncio.create_task(self.receive_ping(container_uuid, vassar_response_url))
        if ga_request_url is not None and await self.queue_exists(ga_request_url) and "containers" in ga_information:
            for container_uuid, container_info in ga_information["containers"].items():
                container_statuses["ga"][container_uuid] = asyncio.create_task(self.receive_ping(container_uuid, ga_response_url))
        if vassar_request_url is not None and await self.queue_exists(vassar_request_url) and "containers" in vassar_information:
            for container_uuid, container_info in vassar_information["containers"].items():
                container_statuses["vassar"][container_uuid] = await container_statuses["vassar"][container_uuid]
        if ga_request_url is not None and await self.queue_exists(ga_request_url) and "containers" in ga_information:
            for container_uuid, container_info in ga_information["containers"].items():
                container_statuses["ga"][container_uuid] = await container_statuses["ga"][container_uuid]
        return container_statuses

    async def receive_ping(self, container_uuid, queue_url):
        # Try at most 5 times
        still_alive = False
        for i in range(5):
            response = await sync_to_async_mt(self.sqs_client.receive_message)(QueueUrl=queue_url, MaxNumberOfMessages=3, WaitTimeSeconds=2, MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "pingAck":
                        # 1. Get uuid
                        received_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        if received_uuid == container_uuid:
                            # Delete Message from queue
                            await sync_to_async_mt(self.sqs_client.delete_message)(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                            still_alive = True
                        else:
                            await sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
                    else:
                        # Return message to queue
                        await sync_to_async_mt(self.sqs_client.change_message_visibility)(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if still_alive:
                break
        return still_alive

    # working
    def get_orbit_list(self, problem_id):
        query = async_to_sync(self.problem_client.get_orbits)(problem_id)
        orbits = [orbit['name'] for orbit in query]
        # query = self.dbClient.get_orbit_list(problem_id)
        return orbits

    # working
    def get_instrument_list(self, problem, group_id=1, problem_id=5):
        # query = self.dbClient.get_instrument_list(group_id, self.problem_id)
        query = async_to_sync(self.problem_client.get_instruments)(self.problem_id)
        instruments = [instrument['name'] for instrument in query]
        # hardcode = ['SMAP_RAD', 'SMAP_MWR', 'VIIRS', 'CMIS', 'BIOMASS']
        # return hardcode
        return instruments

    # working
    def get_objective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_objective_list(group_id, self.problem_id)
        print([obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']])
        return [obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']]

    # working
    def get_subobjective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_subobjective_list(group_id, self.problem_id)
        print([subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']])
        return [subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']]

    def get_dataset_architectures(self, problem_id, dataset_id):
        query = async_to_sync(self.dataset_client.get_architectures)(dataset_id, problem_id)
        # query = self.dbClient.get_architectures(problem_id, dataset_id)


        def boolean_string_to_boolean_array(boolean_string):
            return [b == "1" for b in boolean_string]

        architectures_json = []
        counter = 0
        for arch in query:
            # If the arch needs to be re-evaluated due to a problem definition change, do not add
            if not arch['eval_status']:
                continue

            # Arch: inputs / outputs
            inputs = boolean_string_to_boolean_array(arch['input'])
            outputs = [float(arch['science']), float(arch['cost'])]

            # Append design object and front-end design object
            architectures_json.append({'id': counter, 'db_id': arch['id'], 'inputs': inputs, 'outputs': outputs})
            counter = counter + 1
        return architectures_json

    def get_architecture_from_id(self, arch_id):
        # result_arch = self.dbClient.get_architecture_from_id(arch_id)
        result_arch = async_to_sync(self.dataset_client.get_architecture_pk)(arch_id)
        outputs = [result_arch['science'], result_arch['cost']]
        arch = {'id': result_arch['id'], 'inputs': [b == "1" for b in result_arch['input']], 'outputs': outputs}

        return arch

    def reevaluate_architecture(self, design, eval_queue_url):
        # Unevaluate architecture
        self.dbClient.unevaluate_architecture(design["db_id"])
        # Find arch in database
        arch_info = self.dbClient.get_architecture(design["db_id"])
        self.evaluate_architecture(design["inputs"], eval_queue_url, ga=arch_info["ga"], redo=True)


    # working
    def evaluate_architecture(self, input_str, eval_queue_url, fast=False, ga=False, redo=False, block=True, user=None, session=None):
        inputs = ''
        for x in input_str:
            if x:
                inputs = inputs + '1'
            else:
                inputs = inputs + '0'
        
        # Connect to queue
        print("----------> Evaluating architecture ", inputs)
        eosscontext: EOSSContext = self.user_information.eosscontext

        self.sqs_client.send_message(QueueUrl=eval_queue_url, MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'evaluate',
                'DataType': 'String'
            },
            'input': {
                'StringValue': str(inputs),
                'DataType': 'String'
            },
            'dataset_id': {
                'StringValue': str(eosscontext.dataset_id),
                'DataType': 'String'
            },
            'fast': {
                'StringValue': str(fast),
                'DataType': 'String'
            },
            'ga': {
                'StringValue': str(ga),
                'DataType': 'String'
            },
            'redo': {
                'StringValue': str(redo),
                'DataType': 'String'
            }
        })

        arch = {}
        if block:
            # --> OLD CODE, FOR THE BLOCKING BLOCKHEAD
            result = self.dbClient.subscribe_to_architecture(inputs, eosscontext.problem_id, eosscontext.dataset_id)
            if not result:
                raise ValueError('---> Evaluation Timeout!!!!')
            result_formatted = result['data']['Architecture'][0]
            outputs = [result_formatted['science'], result_formatted['cost']]
            arch = {'id': result_formatted['id'], 'inputs': [b == "1" for b in result_formatted['input']], 'outputs': outputs}
        else:
            # --> NEW CODE, FOR THE CASUAL THREADING ENJOYER
            if not user and not session:
                raise ValueError('---> User and Session objs must be passed to place subscription in thread')
            t1 = threading.Thread(target=self.subscribe_and_add, args=(inputs, eosscontext.problem_id, eosscontext.dataset_id, user, session))
            t1.start()

        return arch

    def subscribe_and_add(self, inputs, problem_id, dataset_id, user, session):
        result = self.dbClient.subscribe_to_architecture(inputs, problem_id, dataset_id)
        if result:
            EOSS.data.design_helpers.add_design(session, user)
        return


    def check_for_existing_arch(self, input_str):
        inputs = ''
        for x in input_str:
            if x:
                inputs = inputs + '1'
            else:
                inputs = inputs + '0'
        eosscontext: EOSSContext = self.user_information.eosscontext
        return async_to_sync(self.dataset_client.check_existing_architecture_2)(inputs, eosscontext.dataset_id, eosscontext.problem_id)
        # return self.dbClient.check_for_existing_arch(eosscontext.problem_id, eosscontext.dataset_id, inputs)

    # working
    def evaluate_false_architectures(self, problem_id, dataset_id, eval_queue_url):
        query_info = self.dbClient.get_false_architectures(problem_id, dataset_id)
        all_archs = query_info['data']['Architecture']
        for arch in all_archs:
            print("--> re-evaluate:", arch['input'])
            self.sqs_client.send_message(QueueUrl=eval_queue_url, MessageBody='boto3', MessageAttributes={
                'msgType': {
                    'StringValue': 'evaluate',
                    'DataType': 'String'
                },
                'dataset_id': {
                    'StringValue': str(dataset_id),
                    'DataType': 'String'
                },
                'input': {
                    'StringValue': str(arch['input']),
                    'DataType': 'String'
                },
                'redo': {
                    'StringValue': 'true',
                    'DataType': 'String'
                },
                'fast': {
                    'StringValue': 'true',
                    'DataType': 'String'
                }
            })

    # working: test  
    def run_local_search(self, inputs, problem_id=5, eval_queue_url=''):
        designs = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            design_futures = []
            designs = []
            for _ in range(4):
                new_inputs = self.random_local_change(inputs)
                print('---> NEW DESIGN ary: ', new_inputs)
                # Check if the architecture already exists in DB before adding it again
                # is_same, arch_id = self.check_for_existing_arch(new_inputs)
                is_same, arch_id = async_to_sync(self.dataset_client.check_existing_architecture_2)(new_inputs)
                if not is_same:
                    design_futures.append(executor.submit(self.evaluate_architecture, new_inputs, eval_queue_url, fast=True, ga=False))
                else:
                    design_futures.append(executor.submit(self.get_architecture_from_id, arch_id))
            for design_future in design_futures:
                new_design = design_future.result()
                print('---> RESULT: ', str(new_design))
                designs.append(new_design)

        return designs

    # working
    def random_local_change(self, input_list):
        index = random.randint(0, len(input_list)-1)
        new_bit = True
        if input_list[index] == True:
            new_bit = False
        new_input_list = input_list[:]
        new_input_list[index] = new_bit
        return new_input_list

    # working
    async def stop_ga(self):
        # Connect to queue
        ga_queue_url = self.user_information.eosscontext.ga_request_queue_url
        if ga_queue_url is not None and await self.queue_exists(ga_queue_url):
            await sync_to_async_mt(self.sqs_client.send_message)(
                QueueUrl=ga_queue_url,
                MessageBody='boto3',
                MessageAttributes={
                    'msgType': {
                        'StringValue': 'stop_ga',
                        'DataType': 'String'
                    }
                }
            )
        return 1

    # working
    async def start_ga(self, algorithm_url, tested_feature=None):
        # Connect to queue
        ga_queue_url = self.user_information.eosscontext.ga_request_queue_url
        print(ga_queue_url)
        if ga_queue_url is not None and await self.queue_exists(ga_queue_url):
            eosscontext: EOSSContext = self.user_information.eosscontext
            message_attributes = {
                    'msgType': {
                        'StringValue': 'start_ga',
                        'DataType': 'String'
                    },
                    'maxEvals': {
                        'StringValue': '3000',
                        'DataType': 'String'
                    },
                    'crossoverProbability': {
                        'StringValue': '1',
                        'DataType': 'String'
                    },
                    'mutationProbability': {
                        'StringValue': '0.016666',
                        'DataType': 'String'
                    },
                    'algorithmUrl': {
                        'StringValue': algorithm_url,
                        'DataType': 'String'
                    },
                    'group_id': {
                        'StringValue': str(eosscontext.group_id),
                        'DataType': 'String'
                    },
                    'problem_id': {
                        'StringValue': str(eosscontext.problem_id),
                        'DataType': 'String'
                    },
                    'dataset_id': {
                        'StringValue': str(eosscontext.dataset_id),
                        'DataType': 'String'
                    }
                }
            if tested_feature is not None:
                message_attributes["tested_feature"] = {
                    'StringValue': tested_feature,
                    'DataType': 'String'
                }
            await sync_to_async_mt(self.sqs_client.send_message)(
                QueueUrl=ga_queue_url,
                MessageBody='boto3',
                MessageAttributes=message_attributes
            )

    # working
    def get_instruments_for_objective(self, problem_id, objective):
        # return self.client.getInstrumentsForObjective(problem, objective)
        print("--> Getting instrument for objective:", objective)
        query = self.dbClient.get_instrument_from_objective(problem_id, objective)
        insts = [inst['name'] for inst in query['data']['Instrument']]
        return insts

    # working
    def get_instruments_for_panel(self, problem_id, panel):
        # return self.client.getInstrumentsForPanel(problem, panel)
        print("--> Getting instrument for panel:", panel)
        query = self.dbClient.get_instrument_from_panel(problem_id, panel)
        insts = [inst['name'] for inst in query['data']['Instrument']]
        return insts
    
    # working
    def get_architecture_score_explanation(self, problem_id, arch):
        print("--> Getting architecture score explanation for arch id:", arch)
        arch_id = arch["db_id"]
        query = self.dbClient.get_architecture_score_explanation(problem_id, arch_id)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Panel']['index_id'], expla['satisfaction'], expla['Stakeholder_Needs_Panel']['weight']) for expla in query['data']['ArchitectureScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working
    def get_panel_score_explanation(self, problem_id, arch, panel):
        print("--> get_panel_score_explanation:", arch["id"], arch["inputs"], arch["outputs"], panel)
        arch_id = arch["db_id"]
        query = self.dbClient.get_panel_score_explanation(problem_id, arch_id, panel)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Objective']['name'], expla['satisfaction'], expla['Stakeholder_Needs_Objective']['weight']) for expla in query['data']['PanelScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working 
    def get_objective_score_explanation(self, problem_id, arch, objective):
        print("--> Getting objective score explanation for arch id:", arch)
        arch_id = arch["db_id"]
        query = self.dbClient.get_objective_score_explanation(problem_id, arch_id, objective)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Subobjective']['name'],  expla['satisfaction'], expla['Stakeholder_Needs_Subobjective']['weight']) for expla in query['data']['ObjectiveScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working 
    def get_subobjective_score_explanation(self, arch, subobjective):
        print("--> Getting subobjective score explanation for arch id:", arch)
        arch_id = arch["db_id"]
        query = self.dbClient.get_subobjective_score_explanation(arch_id, subobjective)
        explanations = [ {
            "attribute_values": expla["measurement_attribute_values"],
            "score": expla["score"],
            "taken_by": expla["taken_by"],
            "justifications": expla["justifications"],
        } 
        for expla in query['data']['SubobjectiveScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working
    def get_arch_science_information(self, problem_id, arch):
        print("\n\n----> get_arch_science_information", problem_id, arch)
        arch_id = arch["db_id"]
        return self.dbClient.get_arch_science_information(problem_id, arch_id)

    # working
    def get_arch_cost_information(self, problem_id, arch):
        print("\n\n----> get_arch_cost_information", problem_id, arch)
        arch_id = arch["db_id"]
        return self.dbClient.get_arch_cost_information(problem_id, arch_id)

    # working
    def get_parameter_value_for_instrument(self, problem_id, parameter, instrument):
        print("\n\n----> get_parameter_value_for_instrument", parameter, instrument)
        return async_to_sync(self.problem_client.get_instrument_attribute_value)(problem_id, instrument, parameter)
        # return self.dbClient.get_instrument_attribute_value(problem_id, instrument, parameter)

    # working
    def get_capability_value_for_instrument(self, group_id, parameter, instrument, measurement=None):
        print("\n\n----> get_parameter_value_for_instrument", parameter, instrument)
        return async_to_sync(self.problem_client.get_instrument_capability_values)(group_id, instrument, parameter, measurement)
        # return self.dbClient.get_instrument_capability_values(group_id, instrument, parameter, measurement)

    # working
    def get_measurement_requirements(self, problem_id, measurement_name, measurement_attribute, subobjective=None):
        print("\n\n----> get_measurement_requirements", measurement_name, measurement_attribute, subobjective)
        return async_to_sync(self.problem_client.get_measurement_requirements)(problem_id, measurement_name, measurement_attribute, subobjective)
        # return self.dbClient.get_measurement_requirements(problem_id, measurement_name, measurement_attribute, subobjective)

    def get_measurement_for_subobjective(self, problem_id, subobjective):
        return async_to_sync(self.problem_client.get_requirement_rule_attribute)(problem_id, None, None, subobjective)
        # return self.dbClient.get_measurement_for_subobjective(problem_id, subobjective)


    # working
    def critique_architecture(self, problem_id, arch):
        print("\n\n----> critique_architecture", problem_id, arch)
        arch_id = arch['db_id']
        print("---> architecture id", arch_id)
        critique = self.dbClient.get_arch_critique(arch_id)
        if critique == []:
            print("---> Re-evaluating architecture ")
            queue_url = self.user_information.eosscontext.vassar_request_queue_url
            self.evaluate_architecture(arch["inputs"], queue_url, redo=True)
            critique = self.dbClient.wait_for_critique(arch_id)
        print("--> FINAL CRITIQUE ", critique)
        return critique
    
    def get_problem_type(self, problem_id):
        # TODO: When generic problems are added, improve this
        return "assignation"

    # rewrite
    def is_ga_running(self, ga_id):
        print("\n\n----> is_ga_running", ga_id)
        return self.client.isGARunning(ga_id)
