import json
import os
import time
import boto3
import random

from django.conf import settings

from EOSS.models import EOSSContext

from EOSS.graphql.api import GraphqlClient
from EOSS.aws.utils import get_boto3_client
from EOSS.aws.EvalQueue import EvalQueue
from daphne_context.models import UserInformation


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


    def send_connect_message(self, url):
        # Send init message
        response = self.sqs_client.send_message(QueueUrl=url, MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'connectionRequest',
                'DataType': 'String'
            },
            'user_id': {
                'StringValue': str(self.user_id),
                'DataType': 'String'
            }
        })

    def connect_to_vassar(self, request_url, response_url, max_retries):
        # Send init message
        user_request_queue_url = ""
        user_response_queue_url = ""

        success = False
        retries = 0
        has_called_aws = False

        while not success and retries < max_retries:
            retries += 1
            user_request_queue_url, user_response_queue_url, container_uuid = self.vassar_connection_loop(response_url)

            if user_request_queue_url == "" and user_response_queue_url == "":
                # If it does not work, and we are on AWS, try increasing Service task limits
                if settings.DEPLOYMENT_TYPE == "aws" and not has_called_aws:
                    has_called_aws = True
                    ecs_client = get_boto3_client('ecs')
                    cluster_arn = os.environ["CLUSTER_ARN"]
                    service_arn = os.environ["VASSAR_SERVICE_ARN"]
                    current_count = ecs_client.describe_services(cluster=cluster_arn, services=[service_arn])["services"][0]["desiredCount"]
                    if current_count < 30:
                        ecs_client.update_service(cluster=cluster_arn, service=service_arn, desiredCount=current_count+1)
                        # Wait for a while for instance to start before trying to connect again
                        time.sleep(10)
            else:
                success = True
            
        return user_request_queue_url, user_response_queue_url, container_uuid, success
    
    def vassar_connection_loop(self, response_url):
        user_request_queue_url = ""
        user_response_queue_url = ""
        vassar_container_uuid = ""
        # Try at most 5 times
        for i in range(5):
            response = self.sqs_client.receive_message(QueueUrl=response_url, MaxNumberOfMessages=3, WaitTimeSeconds=2, MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "isAvailable" and message["MessageAttributes"]["user_id"]["StringValue"] == str(self.user_id):
                        print("Received message attributes:", message["MessageAttributes"])
                        # 1. Get queue URLs
                        user_request_queue_url = message["MessageAttributes"]["request_queue_url"]["StringValue"]
                        user_response_queue_url = message["MessageAttributes"]["response_queue_url"]["StringValue"]
                        vassar_container_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        # 2. Send ACK message
                        response = self.sqs_client.send_message(QueueUrl=user_request_queue_url, MessageBody='boto3', MessageAttributes={
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
                        self.user_information.eosscontext.vassar_request_queue_url = user_request_queue_url
                        self.user_information.eosscontext.vassar_response_queue_url = user_response_queue_url
                        self.user_information.eosscontext.vassar_information = { "containers": { vassar_container_uuid: { "ready": False } } }
                        self.user_information.eosscontext.save()
                        # 4. Delete Message from queue
                        self.sqs_client.delete_message(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        self.sqs_client.change_message_visibility(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if user_request_queue_url != "" and user_response_queue_url != "":
                break
        
        return user_request_queue_url, user_response_queue_url, vassar_container_uuid


    def connect_to_ga(self, request_url, response_url, vassar_request_url, max_retries):
        # Send init message
        user_request_queue_url = ""
        user_response_queue_url = ""

        success = False
        retries = 0
        has_called_aws = False

        while not success and retries < max_retries:
            retries += 1
            user_request_queue_url, user_response_queue_url = self.ga_connection_loop(response_url, vassar_request_url)

            # If it does not work, and we are on AWS, try increasing Service task limits
            if user_request_queue_url == "" and user_response_queue_url == "":
                if settings.DEPLOYMENT_TYPE == "aws" and not has_called_aws:
                    has_called_aws = True
                    ecs_client = get_boto3_client('ecs')
                    cluster_arn = os.environ["CLUSTER_ARN"]
                    service_arn = os.environ["GA_SERVICE_ARN"]
                    current_count = ecs_client.describe_services(cluster=cluster_arn, services=[service_arn])["services"][0]["desiredCount"]
                    if current_count < 30:
                        ecs_client.update_service(cluster=cluster_arn, service=service_arn, desiredCount=current_count+1)
                        # Wait for a while for instance to start before trying to connect again
                        time.sleep(10)
            else:
                success = True

            
        return user_request_queue_url, user_response_queue_url, success

    def ga_connection_loop(self, response_url, vassar_request_url):
        user_request_queue_url = ""
        user_response_queue_url = ""
        # Try at most 5 times
        for i in range(5):
            response = self.sqs_client.receive_message(QueueUrl=response_url, MaxNumberOfMessages=3, WaitTimeSeconds=2, MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "isAvailable" and message["MessageAttributes"]["user_id"]["StringValue"] == str(self.user_id):
                        print("Received message attributes:", message["MessageAttributes"])
                        # 1. Get queue URLs
                        user_request_queue_url = message["MessageAttributes"]["request_queue_url"]["StringValue"]
                        user_response_queue_url = message["MessageAttributes"]["response_queue_url"]["StringValue"]
                        container_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        # 2. Send ACK message
                        response = self.sqs_client.send_message(QueueUrl=user_request_queue_url, MessageBody='boto3', MessageAttributes={
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
                        self.user_information.eosscontext.ga_request_queue_url = user_request_queue_url
                        self.user_information.eosscontext.ga_response_queue_url = user_response_queue_url
                        self.user_information.eosscontext.ga_information = { "containers": { container_uuid: { "ready": False } } }
                        self.user_information.eosscontext.save()
                        # 4. Delete Message from queue
                        self.sqs_client.delete_message(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        self.sqs_client.change_message_visibility(QueueUrl=response_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if user_request_queue_url != "" and user_response_queue_url != "":
                break
        
        return user_request_queue_url, user_response_queue_url
    
    # working
    def send_initialize_message(self, url, group_id, problem_id):
        # Send init message
        response = self.sqs_client.send_message(QueueUrl=url, MessageBody='boto3', MessageAttributes={
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

    def receive_successful_build(self, url, container_uuid, max_retries):
        # Receive initialization complete message
        build_success = False
        retries = 0
        while not build_success and retries < max_retries:
            retries += 1
            for i in range(5):
                response = self.sqs_client.receive_message(QueueUrl=url, MaxNumberOfMessages=3, WaitTimeSeconds=2, MessageAttributeNames=["All"])
                if "Messages" in response:
                    for message in response["Messages"]:
                        if message["MessageAttributes"]["msgType"]["StringValue"] == "isReady":
                            # 1. Save information to database
                            self.user_information.eosscontext.vassar_information["containers"][container_uuid]["ready"] = True
                            self.user_information.eosscontext.save()
                            # 2. Delete Message from queue
                            self.sqs_client.delete_message(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])
                            build_success = True
                        else:
                            # Return message to queue
                            self.sqs_client.change_message_visibility(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
                if build_success:
                    break
        return build_success

    def check_status(self, request_queue, response_queue):
        # Send status check message
        response = self.sqs_client.send_message(QueueUrl=request_queue, MessageBody='boto3', MessageAttributes={
                            'msgType': {
                                'StringValue': 'statusCheck',
                                'DataType': 'String'
                            }
                        })
        # Try at most 10 times
        current_status = ""
        current_timestamp = 0
        for i in range(10):
            response = self.sqs_client.receive_message(QueueUrl=response_queue, MaxNumberOfMessages=3, WaitTimeSeconds=1, MessageAttributeNames=["All"], AttributeNames=["SentTimestamp"])
            if "Messages" in response:
                for message in response["Messages"]:
                    print (message["MessageAttributes"])
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "currentStatus":
                        # 1. Get current status
                        receive_time = int(message["Attributes"]["SentTimestamp"])
                        if receive_time > current_timestamp:
                            current_status = message["MessageAttributes"]["current_status"]["StringValue"]
                            current_timestamp = receive_time
                        # 4. Delete Message from queue
                        self.sqs_client.delete_message(QueueUrl=response_queue, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        # Return message to queue
                        self.sqs_client.change_message_visibility(QueueUrl=response_queue, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
        if current_status == "":
            current_status = "waiting_for_user"
        print("--------- Current status:", current_status)
        return current_status

    def create_dead_queue(self, queue_name):
        response = self.sqs_client.create_queue(
            QueueName=queue_name
        )
        print('---> CREATE QUEUE RESPONSE', response)
        queue_url = response['QueueUrl']
        arn_response = self.sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["QueueArn"]
        )
        queue_arn = arn_response["Attributes"]["QueueArn"]
        return queue_url, queue_arn

    def create_queue(self, queue_name, dead_letter_arn):
        attributes = {
            "MessageRetentionPeriod": str(60*5),
            "RedrivePolicy": json.dumps({
                "deadLetterTargetArn": dead_letter_arn,
                "maxReceiveCount": "3"
            })
        }
        response = self.sqs_client.create_queue(
            QueueName=queue_name,
            Attributes=attributes
        )
        print('---> CREATE QUEUE RESPONSE', response)
        queue_url = response['QueueUrl']
        self.sqs_client.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes=attributes
        )
        
        return queue_url

    def queue_exists(self, queue_url):
        list_response = self.sqs_client.list_queues()
        if 'QueueUrls' in list_response:
            queue_urls = list_response['QueueUrls']
            if queue_url in queue_urls:
                return True
        return False

    def queue_exists_by_name(self, queue_name):
        list_response = self.sqs_client.list_queues()
        if 'QueueUrls' in list_response:
            queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
            if queue_name in queue_names:
                return True
        return False

    def get_queue_url(self, queue_name):
        response = self.sqs_client.get_queue_url(QueueName=queue_name)
        return response["QueueUrl"]

    def get_queue_arn(self, queue_url):
        response = self.sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
        return response["Attributes"]["QueueArn"]

    def send_ping_message(self):
        vassar_request_url = self.user_information.eosscontext.vassar_request_queue_url
        vassar_response_url = self.user_information.eosscontext.vassar_response_queue_url
        vassar_information = self.user_information.eosscontext.vassar_information
        ga_request_url = self.user_information.eosscontext.ga_request_queue_url
        ga_response_url = self.user_information.eosscontext.ga_response_queue_url
        ga_information = self.user_information.eosscontext.ga_information

        if vassar_request_url is not None and self.queue_exists(vassar_request_url) and "containers" in vassar_information:
            print("Pinging VASSAR Containers")
            for container_uuid, container_info in vassar_information["containers"].items():
                response = self.sqs_client.send_message(QueueUrl=vassar_request_url, MessageBody='boto3', MessageAttributes={
                                    'msgType': {
                                        'StringValue': 'ping',
                                        'DataType': 'String'
                                    },
                                    'UUID': {
                                        'StringValue': container_uuid,
                                        'DataType': 'String'
                                    },
                                })
        
        if ga_request_url is not None and self.queue_exists(ga_request_url) and "containers" in ga_information:
            print("Pinging GA Containers")
            for container_uuid, container_info  in ga_information["containers"].items():
                response = self.sqs_client.send_message(QueueUrl=ga_request_url, MessageBody='boto3', MessageAttributes={
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
        if vassar_request_url is not None and self.queue_exists(vassar_request_url) and "containers" in vassar_information:
            for container_uuid, container_info in vassar_information["containers"].items():
                container_statuses["vassar"][container_uuid] = self.receive_ping(container_uuid, vassar_response_url)
        if ga_request_url is not None and self.queue_exists(ga_request_url) and "containers" in ga_information:
            for container_uuid, container_info in ga_information["containers"].items():
                container_statuses["ga"][container_uuid] = self.receive_ping(container_uuid, ga_response_url)
        return container_statuses

    def receive_ping(self, container_uuid, queue_url):
        # Try at most 5 times
        still_alive = False
        for i in range(5):
            response = self.sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=3, WaitTimeSeconds=2, MessageAttributeNames=["All"])
            if "Messages" in response:
                for message in response["Messages"]:
                    if message["MessageAttributes"]["msgType"]["StringValue"] == "pingAck":
                        # 1. Get uuid
                        received_uuid = message["MessageAttributes"]["UUID"]["StringValue"]
                        if received_uuid == container_uuid:
                            # Delete Message from queue
                            self.sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                            still_alive = True
                        else:
                            self.sqs_client.change_message_visibility(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
                    else:
                        # Return message to queue
                        self.sqs_client.change_message_visibility(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)
            if still_alive:
                break
        return still_alive

    # working
    def get_orbit_list(self, problem_id):
        query = self.dbClient.get_orbit_list(problem_id)
        orbits = [orbit['Orbit']['name'] for orbit in query['data']['Join__Problem_Orbit']]
        return orbits

    # working
    def get_instrument_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_instrument_list(group_id, self.problem_id)
        instruments = [instrument['Instrument']['name'] for instrument in query['data']['Join__Problem_Instrument']]
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
        query = self.dbClient.get_architectures(problem_id, dataset_id)

        def boolean_string_to_boolean_array(boolean_string):
            return [b == "1" for b in boolean_string]

        architectures_json = []
        counter = 0
        for arch in query['data']['Architecture']:
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

    def reevaluate_architecture(self, design, eval_queue_url):
        # Unevaluate architecture
        self.dbClient.unevaluate_architecture(design["db_id"])
        # Find arch in database
        arch_info = self.dbClient.get_architecture(design["db_id"])
        self.evaluate_architecture(design["inputs"], eval_queue_url, ga=arch_info["ga"], redo=True)


    # working
    def evaluate_architecture(self, input_str, eval_queue_url, fast=False, ga=False, redo=False):
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

        result = self.dbClient.subscribe_to_architecture(inputs, eosscontext.problem_id, eosscontext.dataset_id)
        
        if result == False:
            raise ValueError('---> Evaluation Timeout!!!!')

        result_formatted = result['data']['Architecture'][0]
        outputs = []
        outputs.append(result_formatted['science'])
        outputs.append(result_formatted['cost'])
        arch = {'id': result_formatted['id'], 'inputs': [b == "1" for b in result_formatted['input']], 'outputs': outputs}
        return arch
    
    def check_for_existing_arch(self, input_str):
        inputs = ''
        for x in input_str:
            if x:
                inputs = inputs + '1'
            else:
                inputs = inputs + '0'
        eosscontext: EOSSContext = self.user_information.eosscontext
        return self.dbClient.check_for_existing_arch(eosscontext.problem_id, eosscontext.dataset_id, inputs)

    def check_dataset_read_only(self) -> bool:
        eosscontext: EOSSContext = self.user_information.eosscontext
        return self.dbClient.check_dataset_read_only(eosscontext.dataset_id)


    # working
    def evaluate_false_architectures(self, problem_id, eval_queue_name='vassar_queue'):
        query_info = self.dbClient.get_false_architectures(self.problem_id)
        all_archs = query_info['data']['Architecture']
        evalQueue = self.sqs.get_queue_by_name(QueueName=eval_queue_name)
        for arch in all_archs:
            print("--> re-evaluate:", arch['input'])
            evalQueue.send_message(MessageBody='boto3', MessageAttributes={
                'msgType': {
                    'StringValue': 'evaluate',
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

        return 0

    # working: test  
    def run_local_search(self, inputs, problem_id=5, eval_queue_url=''):
        designs = []

        for x in range(4):
            new_inputs = self.random_local_change(inputs)
            print('---> NEW DESIGN ary: ', new_inputs)
            new_design_result = self.evaluate_architecture(new_inputs, eval_queue_url, fast=True, ga=True)
            print('---> RESULT: ', str(new_design_result))
            designs.append(new_design_result)

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
    def stop_ga(self):
        # Connect to queue
        ga_queue_url = self.user_information.eosscontext.ga_request_queue_url
        if ga_queue_url is not None and self.queue_exists(ga_queue_url):
            self.sqs_client.send_message(
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
    def start_ga(self):
        # Connect to queue
        ga_queue_url = self.user_information.eosscontext.ga_request_queue_url
        if ga_queue_url is not None and self.queue_exists(ga_queue_url):
            eosscontext: EOSSContext = self.user_information.eosscontext
            self.sqs_client.send_message(
                QueueUrl=ga_queue_url,
                MessageBody='boto3',
                MessageAttributes={
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
            )

    # working
    def get_instruments_for_objective(self, problem, objective):
        # return self.client.getInstrumentsForObjective(problem, objective)
        print("--> Getting instrument for objective:", objective)
        query = self.dbClient.get_instrument_from_objective(objective)
        insts = [inst['name'] for inst in query['data']['Instrument']]
        return insts

    # working
    def get_instruments_for_panel(self, problem, panel):
        # return self.client.getInstrumentsForPanel(problem, panel)
        print("--> Getting instrument for panel:", panel)
        query = self.dbClient.get_instrument_from_panel(panel)
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
    def get_panel_score_explanation(self, problem, arch, panel):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getPanelScoreExplanation(problem, thrift_arch, panel)
        print("--> get_panel_score_explanation:", arch.id, arch.inputs, arch.outputs, panel)
        arch_id = self.dbClient.get_arch_id(arch)
        query = self.dbClient.get_panel_score_explanation(arch_id, panel)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Objective']['name'], expla['satisfaction'], expla['Stakeholder_Needs_Objective']['weight']) for expla in query['data']['PanelScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working 
    def get_objective_score_explanation(self, problem, arch, objective):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getObjectiveScoreExplanation(problem, thrift_arch, objective)
        print("--> Getting objective score explanation for arch id:", arch)
        arch_id = arch["db_id"]
        query = self.dbClient.get_objective_score_explanation(arch_id, objective)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Subobjective']['name'],  expla['satisfaction'], expla['Stakeholder_Needs_Subobjective']['weight']) for expla in query['data']['ObjectiveScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working 
    def get_subobjective_score_explanation(self, arch, subobjective):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getObjectiveScoreExplanation(problem, thrift_arch, objective)
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
    def get_arch_science_information(self, problem, arch):
        print("\n\n----> get_arch_science_information", problem, arch)
        arch_id = self.dbClient.get_arch_id(arch)
        return self.dbClient.get_arch_science_information(arch_id)

    # working
    def get_arch_cost_information(self, problem_id, arch):
        print("\n\n----> get_arch_cost_information", problem_id, arch)
        arch_id = arch["db_id"]
        return self.dbClient.get_arch_cost_information(arch_id)

    def get_parameter_value_for_instrument(self, parameter, instrument):
        print("\n\n----> get_parameter_value_for_instrument", parameter, instrument)
        return self.dbClient.get_parameter_value_for_instrument(parameter, instrument)


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
    def get_subscore_details(self, problem, arch, subobjective):
        print("\n\n----> get_subscore_details", problem, arch, subobjective)
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getSubscoreDetailsBinaryInput(problem, thrift_arch, subobjective)
        elif problem in partition_problems:
            return self.client.getSubscoreDetailsDiscreteInput(problem, thrift_arch, subobjective)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    # rewrite
    def is_ga_running(self, ga_id):
        print("\n\n----> is_ga_running", ga_id)
        return self.client.isGARunning(ga_id)
