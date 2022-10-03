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

        # --> 1. Get user instances
        user_instances = await InstanceClient.get_user_active_instances(user_id, resource_type)
        if len(user_instances) == 0:
            return [], [], []


        # --> 2. Post process instance data
        user_instance_ids = []
        user_running_instance_ids = []
        for instance in user_instances:
            user_instance_ids.append(instance['InstanceId'])
            if instance['State']['Name'] == 'running':
                user_running_instance_ids.append(instance['InstanceId'])



        # --> 3. Get status info / ssm info in parallel
        async def query_status(instance_ids, results):
            if len(instance_ids) == 0:
                return []
            request = await call_boto3_client_async('ec2', 'describe_instance_status', {"InstanceIds": instance_ids}, True)
            if request is not None and 'InstanceStatuses' in request:
                results['status'] = request['InstanceStatuses']
            else:
                results['status'] = []
        async def query_ssm(instance_ids, results):
            if len(instance_ids) == 0:
                results['ssm'] = []
            request = await call_boto3_client_async('ssm', 'describe_instance_information', {
                "Filters": [
                    {
                        'Key': 'InstanceIds',
                        'Values': instance_ids
                    }
                ]
            }, True)
            if request is not None and 'InstanceInformationList' in request:
                results['ssm'] = request['InstanceInformationList']
            else:
                results['ssm'] = []

        async_tasks = []
        results = {}
        async_tasks.append(query_status(user_instance_ids, results))
        async_tasks.append(query_ssm(user_running_instance_ids, results))
        for task in async_tasks:
            await task

        instance_status_info = results['status']
        instance_ssm_info = results['ssm']


        # --> 4. Create final objects
        instance_status_info_list = []
        instance_ssm_info_list = []
        for instance in user_instances:
            instance_status_info_list.append(
                next((item for item in instance_status_info if item["InstanceId"] == instance['InstanceId']), None)
            )
            instance_ssm_info_list.append(
                next((item for item in instance_ssm_info if item["InstanceId"] == instance['InstanceId']), None)
            )

        return user_instances, instance_status_info_list, instance_ssm_info_list

    @staticmethod
    async def get_user_instances_by_states(user_id, resource_type, states):
        # possible_state = ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']
        instances = await InstanceClient.get_user_instances(user_id, resource_type)
        state_instances = []
        for instance in instances:
            if instance['State']['Name'] in states:
                state_instances.append(instance)
        return state_instances

