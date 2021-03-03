import boto3
import os


def get_secret_access_key_env():
    return os.environ['AWS_SECRET_ACCESS_KEY']


def get_access_key_id_env():
    return os.environ['AWS_ACCESS_KEY_ID']


def dev_access_key():
    return 'AKIAJVM34C5MCCWRJCCQ'


def dev_secret_key():
    return 'Pgd2nnD9wAZOCLA5SchYf1REzdYdJvDBpMEEEybU'


def instance_priv_ipv4():
    return '172.31.63.4'


def graphql_server_address(dev=False):
    if not dev:
        return 'http://' + instance_priv_ipv4() + ':6002/v1/graphql'
    else:
        return 'http://graphql:8080/v1/graphql'


def graphql_server_address_ws(dev=False):
    if not dev:
        return 'ws://' + instance_priv_ipv4() + ':6002/v1/graphql'
    else:
        return 'ws://graphql:8080/v1/graphql'


def eval_task_iam_arn():
    return 'arn:aws:iam::923405430231:role/Daphne-EvaluatorTask'


def eval_subnet():
    return 'subnet-0dccba7980012f057'




def dev_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, endpoint_url='http://localstack:4576', region_name='us-east-2', aws_access_key_id=dev_access_key(), aws_secret_access_key=dev_secret_key())

def prod_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, region_name=region_name)






