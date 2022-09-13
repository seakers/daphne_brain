from EOSS.aws.utils import get_boto3_client
import json
import random
import botocore
import asyncio
from EOSS.aws.utils import _save_eosscontext, sync_to_async_mt, call_boto3_client_async


vpc_id = 'vpc-0167d66edf8eebc3c'


class InstanceClient:

    def __init__(self, user_info):
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.eosscontext = user_info.eosscontext


    @staticmethod
    async def get_instances(user_id, resource_type):
        request = await call_boto3_client_async('ec2', 'describe_instances', {
            "Filters": [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                },
                {
                    'Name': 'tag:USER_ID',
                    'Values': [
                        str(user_id),
                    ]
                },
                {
                    'Name': 'tag:RESOURCE_TYPE',
                    'Values': [
                        resource_type
                    ]
                },
            ]
        })
        if 'Reservations' in request:
            return [item['Instances'][0] for item in request['Reservations']]
        return []

    @staticmethod
    async def get_instances_by_state(user_id, resource_type, state='running'):
        possible_state = ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']
        if state not in possible_state:
            print('--> ERROR, IMPOSSIBLE INSTANCE REQ STATE:', state)
        instances = await InstanceClient.get_instances(user_id, resource_type)
        if len(instances) > 0:
            in_state = []
            for instance in instances:
                if instance['State']['Name'] == state:
                    in_state.append(instance)
            return in_state
        return instances
