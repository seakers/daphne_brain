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
            await SqsClient.send_build_msg(self.private_request_url)


    ##################
    ### PROPERTIES ###
    ##################


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
    async def _user_data2(self):
        return '''#!/bin/bash
    sudo systemctl start amazon-ssm-agent'''

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
                'Value': 'LOADING'
            }
        ]

    @property
    async def _definition(self):
        return {
            # "ImageId": "ami-0784177864ad003bd",  # DesignEvaluatorProdImagev1.0
            # "ImageId": "ami-0f14a43a3fe818407",  # DesignEvaluatorProdImagev2.0
            # "ImageId": "ami-0f598a7aeac3948fc",  # DesignEvaluatorProdImagev3.0
            "ImageId": "ami-02b34b6bd313c02f1",    # DesignEvaluatorProdImagev4.0
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
            # "UserData": (await self._user_data2),
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
    
    
    #####################
    ### NEW FUNCTIONS ###
    #####################
    
    async def stop_instance(self):
        await super().stop_instance()
    async def start_instance(self):
        await super().start_instance()
    async def stop_container(self):
        await super().start_container()
    async def start_container(self):
        return 0
    async def pull_container(self):
        return 0
    async def build_container(self):
        return 0





    ##################
    ### DEPRECATED ###
    ##################



    async def start(self):
        await self.purge_queues()

        await super().start()

        await SqsClient.send_build_msg(self.private_request_url)

    async def stop(self):

        # --> 1. Try to stop via vassar inside
        await SqsClient.send_exit_msg(self.private_request_url)
        stopping = await self.wait_on_state('stopping', seconds=30)

        # --> 2. Force stop if inner-stop times out
        if stopping is False:
            await super().stop()

    async def remove(self):
        await super().remove()

    async def build(self):
        await super().build()




