import asyncio
import json

from EOSS.aws.clients.SqsClient import SqsClient
from EOSS.aws.instance.AbstractInstance import AbstractInstance




class DesignEvaluatorInstance(AbstractInstance):

    def __init__(self, user_info, instance=None, instance_status_info=None, instance_ssm_info=None):
        super().__init__(user_info, instance, instance_status_info, instance_ssm_info)
        self.instance_type = 'design-evaluator'


    async def initialize(self):
        if self.instance is not None:
            await self._existing_instance()
        else:
            await self._new_resources()
            await self._new_instance(await self._definition)

    ##################
    ### PROPERTIES ###
    ##################

    @property
    async def _user_data(self):
        return '''#!/bin/bash
        . /home/ec2-user/update.sh'''
    @property
    async def _tags(self):
        return [
            {
                'Key': 'Name',
                'Value': 'daphne-stack'
            },
            {
                'Key': 'ResourceGroup',
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
    async def _definition(self):
        return {
            # "ImageId": "ami-0784177864ad003bd",  # DesignEvaluatorProdImagev1.0
            # "ImageId": "ami-0f14a43a3fe818407",  # DesignEvaluatorProdImagev2.0
            # "ImageId": "ami-0f598a7aeac3948fc",  # DesignEvaluatorProdImagev3.0
            # "ImageId": "ami-02b34b6bd313c02f1",  # DesignEvaluatorProdImagev4.0
            # "ImageId": "ami-0ed4b8a5ca628fd8f",  # DesignEvaluatorProdImagev5.0
            "ImageId": "ami-07ecbec4e2200e873",    # DaphneServiceProdImagev1.0
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
            "HibernationOptions": {
                "Configured": True
            },
            "UserData": (await self._user_data),
            "TagSpecifications": [
                {
                    'ResourceType': 'instance',
                    'Tags': (await self._tags)
                },
            ],
        }



    ############
    ### PING ###
    ############

    async def ping(self):
        response = await super().ping()
        return response
    
    
    ################
    ### CONSOLE  ###
    ################
    
    # async def start_instance(self):
    #     result = await super().start_instance()
    #     return {'identifier': self.identifier, 'result': result}
    # async def stop_instance(self):
    #     # --> 1. Try to stop via vassar inside
    #     # await SqsClient.send_exit_msg(self.private_request_url)
    #     # stopping = await self.wait_on_state('stopping', seconds=30)
    #
    #     # --> 2. Try to stop via ec2 call
    #     result = await super().stop_instance()
    #     return {'identifier': self.identifier, 'result': result}
    # async def hibernate_instance(self):
    #     result = await super().hibernate_instance()
    #     return {'identifier': self.identifier, 'result': result}
    # async def run_container(self):
    #     result = await super().run_container()
    #     return {'identifier': self.identifier, 'result': result}
    # async def stop_container(self):
    #     result = await super().stop_container()
    #     return {'identifier': self.identifier, 'result': result}
    # async def update_container(self):
    #     result = await super().update_container()
    #     return {'identifier': self.identifier, 'result': result}

    async def build_vassar(self):

        # --> 1. Check container running
        if await self.get_instance_state() != 'running' or not await self.container_running():
            return {'identifier': self.identifier, 'result': False}

        # --> 2. Send build msg
        response = await SqsClient.send_build_msg(self.private_request_url, self.private_response_url)
        return {'identifier': self.identifier, 'result': response is not None}




