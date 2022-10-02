import boto3
import os
import time
import asyncio
import random
from asgiref.sync import SyncToAsync, sync_to_async
from django.conf import settings
from EOSS.models import EOSSContext
from botocore.client import Config

def sync_to_async_mt(func):
    return SyncToAsync(func, thread_sensitive=False)


@sync_to_async
def _save_eosscontext(eosscontext: EOSSContext):
    eosscontext.save()


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


def dev_access_key():
    return 'AKIAJVM34C5MCCWRJCCQ'


def dev_secret_key():
    return 'Pgd2nnD9wAZOCLA5SchYf1REzdYdJvDBpMEEEybU'


def instance_priv_ipv4():
    return '172.31.63.4'


def graphql_server_address(dev=False):
    return os.environ['HASURA_HOST']


def graphql_server_address_ws(dev=False):
    if settings.DEPLOYMENT_TYPE == "local":
        return 'ws://graphql:8080/v1/graphql'
    else:
        return os.environ['HASURA_HOST_WS']


def eval_task_iam_arn():
    return 'arn:aws:iam::923405430231:role/Daphne-EvaluatorTask'


def task_execution_role_arn():
    return 'arn:aws:iam::923405430231:role/Daphne-TaskExecutionRole'


def eval_subnet():
    return 'subnet-0dccba7980012f057'


def dev_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, region_name=region_name, aws_access_key_id=dev_access_key(),
                        aws_secret_access_key=dev_secret_key(), use_ssl=False)


def prod_client(client_type, region_name='us-east-2'):
    return boto3.client(client_type, region_name=region_name, endpoint_url=f"https://sqs.{region_name}.amazonaws.com")


def get_boto3_client(client_type, region_name='us-east-2'):
    return prod_client(client_type, region_name)
    # if settings.DEPLOYMENT_TYPE == "local":
    #     return dev_client(client_type, region_name)
    # else:
    #     return prod_client(client_type, region_name)


################
### AIOBOTO3 ###
################
import asyncio
import aioboto3


async def call_boto3_client_async(client_type, func_name, params=None, debug=True):
    if debug is True:
        print('--> ATTEMPTING ASYNC AWS CALL:', client_type, func_name)
    result = None
    session = aioboto3.Session()
    async with session.client(client_type, region_name='us-east-2', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                              aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']) as client:
        try:
            func = getattr(client, func_name)
            if params is None:
                result = await func()
            else:
                result = await func(**params)
        except Exception as ex:
            print('--> (AWS ERROR)', client_type, func_name, '-----', ex)
            return None
    return result

async def call_boto3_client_async_timeout(client_type, func_name, params=None, debug=True, connect_timeout=3):
    if debug is True:
        print('--> ATTEMPTING ASYNC AWS CALL:', client_type, func_name)
    result = None
    config = Config(connect_timeout=connect_timeout, retries={'max_attempts': 0})
    session = aioboto3.Session()
    async with session.client(client_type, region_name='us-east-2', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                              aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], config=config) as client:
        try:
            func = getattr(client, func_name)
            if params is None:
                result = await func()
            else:
                result = await func(**params)
        except Exception as ex:
            print('--> (AWS ERROR)', client_type, func_name, '-----', ex)
            return None
    return result

async def backoff_boto3_client_async(client_type, func_name, params=None, debug=False, seconds=30):
    result = await call_boto3_client_async(client_type, func_name, params, debug)
    trys = 1
    sleep_time = 2
    attempts = int(seconds / sleep_time)
    while result is None and trys < attempts:
        result = await call_boto3_client_async(client_type, func_name, params, debug)
        trys += 1
    return 0





##############
### SEARCH ###
##############

async def find_obj(objs, key_name, key_value):
    for obj in objs:
        if key_name not in obj:
            continue
        if obj[key_name] == key_value:
            return obj
    return None


async def find_obj_value(objs, key_name, key_value, set_name):
    obj = await find_obj(objs, key_name, key_value)
    if set_name not in obj:
        return None
    return obj[set_name]


async def find_obj_and_set(objs, key_name, key_value, set_name, set_value):
    obj = await find_obj(objs, key_name, key_value)
    if obj is not None:
        obj[set_name] = set_value
    return obj


#######################
### REQUEST BACKOFF ###
#######################


async def exponential_backoff_sleep(x):
    backoff_seconds = 1
    sleep_time = (backoff_seconds * 2 ** x + random.uniform(0, 1))
    await asyncio.sleep(sleep_time)


def exponential_backoff(func, attempts=5, backoff='EXPONENTIAL', dne=False):
    result = return_flipper(func, dne)
    x = 0
    while result is None:
        if backoff == 'EXPONENTIAL':
            _exponential_sleep(x)
        if backoff == 'LINEAR':
            _linear_sleep(x)
        result = return_flipper(func, dne)
        x += 1
        if x > attempts:
            break
    return result





async def exponential_backoff_async(func, attempts=5, backoff='EXPONENTIAL', dne=False):
    result = await return_flipper_async(func, dne)
    x = 0
    while result is None:
        if backoff == 'EXPONENTIAL':
            await _exponential_sleep_async(x)
        if backoff == 'LINEAR':
            await _linear_sleep_async(2)
        result = await return_flipper_async(func, dne)
        x += 1
        if x > attempts:
            break
    return result


def _exponential_sleep(x):
    backoff_seconds = 1
    sleep_time = (backoff_seconds * 2 ** x + random.uniform(0, 1))
    time.sleep(sleep_time)


def _linear_sleep(x):
    time.sleep(x)


async def _exponential_sleep_async(x):
    backoff_seconds = 1
    sleep_time = (backoff_seconds * 2 ** x + random.uniform(0, 1))
    await asyncio.sleep(sleep_time)


async def _linear_sleep_async(x):
    await asyncio.sleep(x)


def return_flipper(func, dne=False):
    if dne is False:
        return func()
    result = func()
    if result is None:
        return {}
    return None


async def return_flipper_async(func, params=None, dne=False):
    if dne is False:
        if params is not None:
            return await func(**params)
        else:
            return await func()

    if params is not None:
        result = await func(**params)
    else:
        result = await func()
    if result is None:
        return {}
    return None
