import asyncio
import os
import boto3
import json
from EOSS.aws.utils import call_boto3_client_async, find_obj_value
from EOSS.aws.clients.SqsClient import SqsClient
from EOSS.aws.instance.AbstractInstance import AbstractInstance



"""

Tags
-   RESOURCE_STATE


AWS Functions
    1. run_instances()
    
    2. start_instances()
    3. stop_instances()
    
    SSM
    1. send_command()     - used to start container service inside ec2

"""


class DesignEvaluatorInstance(AbstractInstance):

    def __init__(self, user_info, instance=None):
        super().__init__(user_info, instance)
        self.instance_type = 'design-evaluator'

        self.design_evaluator_request_queue_url = self.eosscontext.design_evaluator_request_queue_url

    @property
    async def _user_data(self):
        return '''#!/bin/bash
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)
sudo service docker start
sudo $(sudo aws ecr get-login --region us-east-2 --no-include-email)
sudo docker pull 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator
ENV_STRING=""
JSON_TAGS=$(aws ec2 describe-tags --filters "Name=resource-id,Values=${INSTANCE_ID}" --region=us-east-2)
for row in $(echo ${JSON_TAGS} | jq -c '.Tags[]'); do
        var_key=$(echo ${row} | jq -r '.Key')
        var_value=$(echo ${row} | jq -r '.Value')
        ENV_STRING+="--env ${var_key}=${var_value} "
done
sudo docker run --name=evaluator ${ENV_STRING} 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator:latest'''

    @property
    async def _tags(self):
        return [
            {
                'Key': 'Name',
                'Value': 'daphne-stack'
            },
            {
                'Key': 'IDENTIFIER',
                'Value': self.identifier
            },
            {
                'Key': 'USER_ID',
                'Value': str(self.user_id)
            },
            {
                'Key': 'RESOURCE_TYPE',
                'Value': 'design-evaluator'
            },
            {
                'Key': 'REGION',
                'Value': 'us-east-2'
            },
            {
                'Key': 'REQUEST_MODE',
                'Value': 'CRISP-ATTRIBUTES'
            },
            {
                'Key': 'DEPLOYMENT_TYPE',
                'Value': 'AWS'
            },
            {
                'Key': 'MAXEVAL',
                'Value': '5'
            },
            {
                'Key': 'APOLLO_URL',
                'Value': 'http://graphql.daphne.dev:8080/v1/graphql'
            },
            {
                'Key': 'APOLLO_URL_WS',
                'Value': 'ws://graphql.daphne.dev:8080/v1/graphql'
            },
            {
                'Key': 'EVAL_REQUEST_URL',
                'Value': self.eosscontext.design_evaluator_request_queue_url
            },
            {
                'Key': 'EVAL_RESPONSE_URL',
                'Value': self.eosscontext.design_evaluator_response_queue_url
            },
            {
                'Key': 'PING_REQUEST_URL',
                'Value': self.ping_request_url
            },
            {
                'Key': 'PING_RESPONSE_URL',
                'Value': self.ping_response_url
            },
            {
                'Key': 'PRIVATE_REQUEST_URL',
                'Value': self.private_request_url
            },
            {
                'Key': 'PRIVATE_RESPONSE_URL',
                'Value': self.private_response_url
            },
            {
                'Key': 'RESOURCE_STATE',
                'Value': 'INITIALIZING'
            }
        ]

    @property
    async def _run_instances(self):
        return {
            "ImageId": "ami-0784177864ad003bd",
            "InstanceType": "t2.medium",
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": [
                "sg-03871503ca9368508"
            ],
            "KeyName": 'gabe-master',
            "SubnetId": "subnet-05cc334fd084cb66c",
            "IamInstanceProfile": {
                'Name': 'ecsInstanceRole'
            },
            "UserData": (await self._user_data),
            "TagSpecifications": [
                {
                    'ResourceType': 'instance',
                    'Tags': (await self._tags)
                },
            ],
        }



    """
      _____       _ _   _       _ _         
     |_   _|     (_) | (_)     | (_)        
       | |  _ __  _| |_ _  __ _| |_ _______ 
       | | | '_ \| | __| |/ _` | | |_  / _ \
      _| |_| | | | | |_| | (_| | | |/ /  __/
     |_____|_| |_|_|\__|_|\__,_|_|_/___\___|
     - When UserInformation is being created, create instances then stop all to reach starting state
     - This is done in create_instance function
    """

    async def initialize(self):
        if self.instance is not None:
            await self.scan_container()
        else:
            await self.create_instance()

    # --> NOTE: creating the ec2 instance should automatically start the design-evaluator service inside
    # - this is done through userdata
    async def create_instance(self):

        # --> 1. Call parent initialization
        await self._initialize()

        # --> 2. Create instance + wait until running
        result = await call_boto3_client_async('ec2', 'run_instances', await self._run_instances)
        if result is None:
            return

        # --> 3. Wait until instance is pending / starting then stop
        running = await self.wait_on_states(['pending', 'running'], seconds=120)
        if running is True:
            await super().stop()

        # --> 4. Set RESOURCE_STATE tag to READY
        await self.set_tag('RESOURCE_STATE', 'READY')





    """
       _____  _                _   
      / ____|| |              | |  
     | (___  | |_  __ _  _ __ | |_ 
      \___ \ | __|/ _` || '__|| __|
      ____) || |_| (_| || |   | |_ 
     |_____/  \__|\__,_||_|    \__|
    """

    async def start(self):
        await self.purge_queues()

        await super().start()

        await SqsClient.send_build_msg(self.private_request_url)



    """
       _____  _                
      / ____|| |               
     | (___  | |_  ___   _ __  
      \___ \ | __|/ _ \ | '_ \ 
      ____) || |_| (_) || |_) |
     |_____/  \__|\___/ | .__/ 
                        | |    
                        |_|    
    """

    async def stop(self):

        # --> 1. Try to stop via vassar inside
        await SqsClient.send_exit_msg(self.private_request_url)
        stopping = await self.wait_on_state('stopping', seconds=30)

        # --> 2. Force stop if inner-stop times out
        if stopping is False:
            await super().stop()

    """
     _____                                    
    |  __ \                                   
    | |__) | ___  _ __ ___    ___ __   __ ___ 
    |  _  / / _ \| '_ ` _ \  / _ \\ \ / // _ \
    | | \ \|  __/| | | | | || (_) |\ V /|  __/
    |_|  \_\\___||_| |_| |_| \___/  \_/  \___|
                                       
    """

    async def remove(self):
        await super().remove()



    """
      ____        _ _     _ 
     |  _ \      (_) |   | |
     | |_) |_   _ _| | __| |
     |  _ <| | | | | |/ _` |
     | |_) | |_| | | | (_| |
     |____/ \__,_|_|_|\__,_|                 
    """

    async def build(self):
        await super().build()


    """
          _____ _             
         |  __ (_)            
         | |__) | _ __   __ _ 
         |  ___/ | '_ \ / _` |
         | |   | | | | | (_| |
         |_|   |_|_| |_|\__, |
                         __/ |
                        |___/ 
    """

    async def ping(self):
        await super().ping()
