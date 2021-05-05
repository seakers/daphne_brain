import boto3
import os

from django.conf import settings


def pprint(to_print):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(to_print)

def user_input(yes_no_message):
    response = input(yes_no_message)
    if response != 'yes':
        print('EXITING COMMAND')
        return False
    else:
        return True

def get_secret_access_key_env():
    return os.environ['AWS_SECRET_ACCESS_KEY']

def get_access_key_id_env():
    return os.environ['AWS_ACCESS_KEY_ID']

def dev_access_key():
    return 'AKIAJVM34C5MCCWRJCCQ'

def dev_secret_key():
    return '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'

def instance_priv_ipv4():
    return '172.31.63.4'

def graphql_server_address(dev=False):
    if settings.DEPLOYMENT_TYPE == "local":
        return 'http://graphql:6002/v1/graphql'
    else:
        return os.environ['HASURA_HOST']

def graphql_server_address_ws(dev=False):
    if settings.DEPLOYMENT_TYPE == "local":
        return 'ws://graphql:6002/v1/graphql'
    else:
        return os.environ['HASURA_HOST_WS']

def eval_task_iam_arn():
    return 'arn:aws:iam::923405430231:role/Daphne-EvaluatorTask'

def task_execution_role_arn():
    return 'arn:aws:iam::923405430231:role/Daphne-TaskExecutionRole'

def eval_subnet():
    return 'subnet-0dccba7980012f057'




def dev_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, endpoint_url='http://localstack:4576', region_name='us-east-2', aws_access_key_id=dev_access_key(), aws_secret_access_key=dev_secret_key())

def prod_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, region_name=region_name, endpoint_url=f"https://sqs.{region_name}.amazonaws.com")

def get_boto3_client(client_type,  region_name='us-east-2'):
    if settings.DEPLOYMENT_TYPE == "local":
        return dev_client(client_type, region_name)
    else:
        return prod_client(client_type, region_name)