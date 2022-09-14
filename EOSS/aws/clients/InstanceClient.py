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
    async def get_daphne_instances():
        request = await call_boto3_client_async('ec2', 'describe_instances', {
            "Filters": [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                },
                {
                    'Name': 'tag:Name',
                    'Values': [
                        'daphne-stack'
                    ]
                },
            ]
        })
        if 'Reservations' in request:
            return [item['Instances'][0] for item in request['Reservations']]
        return []


    @staticmethod
    async def get_user_instances(user_id, resource_type):
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
    async def get_user_active_instances(user_id, resource_type):
        active_instances = []
        instances = await InstanceClient.get_user_instances(user_id, resource_type)
        for instance in instances:
            if instance['State']['Name'] not in ['terminated']:
                active_instances.append(instance)
        return active_instances

    @staticmethod
    async def get_user_instances_by_states(user_id, resource_type, states):
        # possible_state = ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']
        instances = await InstanceClient.get_user_instances(user_id, resource_type)
        state_instances = []
        for instance in instances:
            if instance['State']['Name'] in states:
                state_instances.append(instance)
        return state_instances

