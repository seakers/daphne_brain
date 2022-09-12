import os
import boto3
from EOSS.utils import call_boto3_client_async
from EOSS.aws.clients.SqsClient import SqsClient




""" InstanceManager
- Purpose of this class is to manage / regulate user ec2 instances deployed on an ecs cluster (daphne-dev-cluster)
    
    
    
AWS Functions

    1. run_instances()
    
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()
    
    
    
"""






class InstanceManager:

    def __init__(self, user_info):
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext
        self.sqs_client = SqsClient(self.user_info)

        # --> Cluster Info: daphne-cluster
        self.cluster_name = self.eosscontext.cluster_name
        self.cluster_arn = self.eosscontext.cluster_arn

        # --> Initialization Data (async init)
        self.vassar_containers = []
        self.ga_containers = []


    async def initialize(self):

        # --> Init Queues (eval request)
        await self.sqs_client.initialize()

        # --> Gather the currently running containers
        await self.gather_resources()




    async def gather_resources(self):

        # --> 1. Gather existing instances
        de_instances = await self.gather_instances('design-evaluator')
        ga_instances = await self.gather_instances('genetic-algorithm')


        return 0


    async def gather_instances(self, instance_type):
        request = await call_boto3_client_async('ec2', 'describe_instances', {
            "Filters": [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        'vpc-0167d66edf8eebc3c',
                    ]
                },
                {
                    'Name': 'tag:USER_ID',
                    'Values': [
                        str(self.user_id),
                    ]
                },
                {
                    'Name': 'tag:RESOURCE_TYPE',
                    'Values': [
                        instance_type
                    ]
                },
            ]
        })
        if 'Reservations' in request:
            return [item['Instances'][0] for item in request['Reservations']]
        return []










