import asyncio
import json

from EOSS.aws.clients.SqsClient import SqsClient
from EOSS.aws.instance.AbstractInstance import AbstractInstance


class GeneticAlgorithmInstance(AbstractInstance):

    def __init__(self, user_info, instance=None, instance_status_info=None, instance_ssm_info=None):
        super().__init__(user_info, instance, instance_status_info, instance_ssm_info)
        self.instance_type = 'genetic-algorithm'

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
                'Value': 'genetic-algorithm'
            },
            {
                'Key': 'DEPLOYMENT_TYPE',
                'Value': 'AWS'
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
            },
            {
                'Key': 'MESSAGE_RETRIEVAL_SIZE',
                'Value': '3'
            },
            {
                'Key': 'MESSAGE_QUERY_TIMEOUT',
                'Value': '5'
            },
            {
                'Key': 'DEBUG',
                'Value': 'false'
            }
        ]

    @property
    async def _definition(self):
        return {
            "ImageId": "ami-07ecbec4e2200e873",  # DaphneServiceProdImagev1.0 TODO: create
            "InstanceType": "t2.small",
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

    async def start_ga(self):

        # --> 1. Check container running
        if await self.get_instance_state() != 'running' or not await self.container_running():
            return False

        # --> 2. Send start msg
        response = await SqsClient.send_start_ga_msg(self.private_request_url,
                                                     self.eosscontext.group_id,
                                                     self.eosscontext.problem_id,
                                                     self.eosscontext.dataset_id,
                                                     self.private_response_url)
        return response is not None

    async def stop_ga(self):

        # --> 1. Check container running
        if await self.get_instance_state() != 'running' or not await self.container_running():
            return False

        # --> 2. Send start msg
        response = await SqsClient.send_stop_ga_msg(self.private_request_url, self.private_response_url)
        return response is not None

    async def apply_feature(self):
        return 0
