import os
import boto3
from EOSS.aws.utils import call_boto3_client_async, find_obj_value
from EOSS.aws.clients.SqsClient import SqsClient
from EOSS.aws.instance.AbstractInstance import AbstractInstance



"""
AWS Functions
    1. run_instances()
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    4. start_session()

"""


class DesignEvaluatorInstance(AbstractInstance):

    def __init__(self, user_info, instance=None):
        super().__init__(user_info, instance)
        self.container_type = 'design-evaluator'

    async def initialize(self):
        if self.instance is None:
            await self.initialize_instance()
        else:
            await self.scan_container()

    async def initialize_instance(self):

        # --> 1. Call parent initialization
        await self._initialize()

        # --> 2. Create instance
        response = await call_boto3_client_async('ec2', 'run_instances', self._run_instances)

        # --> Wait until instance running


        # --> 3. Connect to container (SSM)
        await self.connect()

    async def shutdown(self):
        await self._shutdown()

    async def remove(self):
        await self._remove()


    @property
    def _run_instances(self):
        user_data = '''[settings.ecs]
cluster = "daphne-dev-cluster"'''
        return {
            "ImageId": "ami-06a14133d3bf45cbc",
            "InstanceType": "t2.medium",
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": [
                "sg-03871503ca9368508"
            ],
            "SubnetId": "subnet-05cc334fd084cb66c",
            "IamInstanceProfile": {
                 'Name': 'ecsInstanceRole'
             },
            "UserData": user_data,
            "TagSpecifications": [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'PING_REQUEST_QUEUE',
                            'Value': self.ping_request_queue
                        },
                        {
                            'Key': 'PING_RESPONSE_QUEUE',
                            'Value': self.ping_response_queue
                        },
                        {
                            'Key': 'PRIVATE_QUEUE_REQUEST',
                            'Value': self.ping_request_queue
                        },
                        {
                            'Key': 'PRIVATE_QUEUE_RESPONSE',
                            'Value': self.ping_response_queue
                        },
                        {
                            'Key': 'IDENTIFIER',
                            'Value': self.identifier
                        }
                    ]
                },
            ],
        }


    """
            _____                            _   
          / ____|                          | |  
         | |     ___  _ __  _ __   ___  ___| |_ 
         | |    / _ \| '_ \| '_ \ / _ \/ __| __|
         | |___| (_) | | | | | | |  __/ (__| |_ 
          \_____\___/|_| |_|_| |_|\___|\___|\__|
    """
    # - Connect to design-evaluator inside of instance
    async def connect(self):
        print('--> CONNECTING TO DESIGN EVALUATOR:', self.identifier)

        # --> 1. Await instance








