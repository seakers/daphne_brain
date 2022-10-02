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
        }, True)
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
    async def get_user_active_instances_all(user_id, resource_type):
        active_instances = await InstanceClient.get_user_active_instances(user_id, resource_type)
        active_instances = sorted(active_instances, key=lambda d: d['InstanceId'])
        instance_ids = [instance['InstanceId'] for instance in active_instances]

        # --> Get instance status
        instance_statuses = []
        if len(instance_ids) > 0:
            request = await call_boto3_client_async('ec2', 'describe_instance_status', {
                "InstanceIds": instance_ids
            }, True)
            if request is not None and 'InstanceStatuses' in request:
                instance_statuses = request['InstanceStatuses']
        # instance_statuses = sorted(instance_statuses, key=lambda d: d['InstanceId'])

        # --> Get instance additional info
        instance_infos = []
        if len(instance_ids) > 0:
            request = await call_boto3_client_async('ssm', 'describe_instance_information', {
                "Filters": [
                    {
                        'Key': 'InstanceIds',
                        'Values': instance_ids
                    }
                ]
            }, True)
            if request is not None and 'InstanceInformationList' in request:
                instance_infos = request['InstanceInformationList']
                if len(instance_infos) != len(active_instances):
                    print('--> ERROR, MORE ACTIVE INSTANCES THAN INSTANCE INFO OBJS')
        # instance_infos = sorted(instance_infos, key=lambda d: d['InstanceId'])

        # --> Iterate over active instances and append
        final_statuses = []
        final_infos = []
        for instance in active_instances:
            status_item = next((item for item in instance_statuses if item["InstanceId"] == instance['InstanceId']), None)
            final_statuses.append(status_item)
            info_item = next((item for item in instance_infos if item["InstanceId"] == instance['InstanceId']), None)
            final_infos.append(info_item)

        return active_instances, final_statuses, final_infos

    @staticmethod
    async def get_user_instances_by_states(user_id, resource_type, states):
        # possible_state = ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']
        instances = await InstanceClient.get_user_instances(user_id, resource_type)
        state_instances = []
        for instance in instances:
            if instance['State']['Name'] in states:
                state_instances.append(instance)
        return state_instances

