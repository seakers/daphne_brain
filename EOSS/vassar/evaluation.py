from daphne_context.models import UserInformation
from EOSS.aws.utils import get_boto3_client
from EOSS.graphql.api import GraphqlClient
from EOSS.data.design_helpers import add_design
from asgiref.sync import async_to_sync, sync_to_async

import threading

from EOSS.graphql.clients.Dataset import Dataset

from aiobotocore.session import get_session
from EOSS.aws.utils import dev_access_key, dev_secret_key

class Evaluation:

    def __init__(self, user_info: UserInformation):
        self.user_info = user_info

        self.dataset_id = user_info.eosscontext.dataset_id
        self.eval_request_queue = user_info.eval_request_queue
        self.eval_response_queue = user_info.eval_response_queue

        self.sqs_client = get_boto3_client('sqs')
        self.db_client = GraphqlClient(user_info=user_info)
        self.d_client = Dataset(self.user_info)


        self.diversifier = False
        self.diversifier = user_info.eosscontext.activecontext.check_for_diversity

    async def purge_all(self):
        session = get_session()
        async with session.create_client('sqs',
                                         region_name='us-east-2',
                                         endpoint_url='http://mock-sqs:9324',
                                         aws_access_key_id=dev_access_key(),
                                         aws_secret_access_key=dev_secret_key()) as client:
            response = await client.purge_queue(QueueUrl=self.eval_request_queue)
            response = await client.purge_queue(QueueUrl=self.eval_response_queue)

    ############
    ### EVAL ###
    ############

    async def evaluate(self, inputs, user_session=None):

        # --> 1. If validation returns anything but None there was a problem
        checks = await self._validation(inputs)
        if checks:
            return checks

        # --> 2. Get correct inputs
        inputs = await Evaluation._format(inputs)

        # --> 3. Send async sqs message
        session = get_session()
        async with session.create_client('sqs',
                                         region_name='us-east-2',
                                         endpoint_url='http://mock-sqs:9324',
                                         aws_access_key_id=dev_access_key(),
                                         aws_secret_access_key=dev_secret_key()) as client:
            response_attributes = (await self._msg_evaluate(inputs, self.dataset_id))['MessageAttributes']
            response = await client.send_message(QueueUrl=self.eval_request_queue, MessageBody='boto3', MessageAttributes=response_attributes)

        # --> 4. Subscribe to architecture if requested
        if self.diversifier is True and user_session:
            result = await self.d_client.subscribe_to_architecture(inputs)
            if result:
                await sync_to_async(add_design)(user_session, self.user_info.user)

    async def evaluate_batch(self, batch, dataset_id=None):
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 1. Get async session
        session = get_session()
        async with session.create_client('sqs',
                                         region_name='us-east-2',
                                         endpoint_url='http://mock-sqs:9324',
                                         aws_access_key_id=dev_access_key(),
                                         aws_secret_access_key=dev_secret_key()) as client:
            # 2. Convert all designs to appropriate form and submit
            batch_10 = []
            for idx, inputs in enumerate(batch):
                batch_10.append(await self._msg_evaluate(await Evaluation._format(inputs), used_dataset_id, idx))
                if len(batch_10) == 10:
                    response = await client.send_message_batch(QueueUrl=self.eval_request_queue, Entries=batch_10)
                    batch_10 = []
            # 2. Submit any leftover designs
            if len(batch_10) > 0:
                response = await client.send_message_batch(QueueUrl=self.eval_request_queue, Entries=batch_10)

    ##############
    ### UPDATE ###
    ##############

    async def update(self, architecture):
        # --> 0.0 Validate architecture can be updated based on current container problem configuration

        # --> 1. Send update message to eval queue
        session = get_session()
        async with session.create_client('sqs',
                                         region_name='us-east-2',
                                         endpoint_url='http://mock-sqs:9324',
                                         aws_access_key_id=dev_access_key(),
                                         aws_secret_access_key=dev_secret_key()) as client:
            response_attributes = (await self._msg_update(await Evaluation._format(architecture['input']), architecture['id'], architecture['dataset_id']))['MessageAttributes']
            response = await client.send_message(QueueUrl=self.eval_request_queue, MessageBody='boto3', MessageAttributes=response_attributes)

    async def update_batch(self, architectures):
        # --> 1. Get async session
        session = get_session()
        async with session.create_client('sqs',
                                         region_name='us-east-2',
                                         endpoint_url='http://mock-sqs:9324',
                                         aws_access_key_id=dev_access_key(),
                                         aws_secret_access_key=dev_secret_key()) as client:
            batch_10 = []
            for idx, architecture in enumerate(architectures):
                batch_10.append(await self._msg_update(architecture['input'], architecture['id'], architecture['dataset_id'], idx))
                if len(batch_10) == 10:
                    response = await client.send_message_batch(QueueUrl=self.eval_request_queue, Entries=batch_10)
                    batch_10 = []

            # 2. Submit any leftover designs
            if len(batch_10) > 0:
                response = await client.send_message_batch(QueueUrl=self.eval_request_queue, Entries=batch_10)

    async def update_false(self, dataset_id=None):
        # --> 1. Get dataset id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Get false architecture ids
        architectures = await self.d_client.get_architectures_false(dataset_id=dataset_id)
        await self.update_batch(architectures)

    ###########
    ### MSG ###
    ###########

    async def _msg_update(self, input, arch_id, dataset_id, idx=None):
        msg = {
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'evaluate',
                    'DataType': 'String'
                },
                'eval_type': {
                    'StringValue': 'NDSM',
                    'DataType': 'String'
                },
                'input': {
                    'StringValue': str(input),
                    'DataType': 'String'
                },
                'arch_id': {
                    'StringValue': str(arch_id),
                    'DataType': 'String'
                },
                'dataset_id': {
                    'StringValue': str(dataset_id),
                    'DataType': 'String'
                },
                'index_type': {
                    'StringValue': 'UPDATE',
                    'DataType': 'String'
                }
            },
            'MessageBody': 'boto3',
        }
        if idx is not None:
            msg['Id'] = str(idx)
        return msg

    async def _msg_evaluate(self, input, dataset_id, idx=None):
        msg = {
            'MessageAttributes': {
                'msgType': {
                    'StringValue': 'evaluate',
                    'DataType': 'String'
                },
                'input': {
                    'StringValue': input,
                    'DataType': 'String'
                },
                'dataset_id': {
                    'StringValue': str(dataset_id),
                    'DataType': 'String'
                },
                'eval_type': {
                    'StringValue': 'NDSM',
                    'DataType': 'String'
                },
                'index_type': {
                    'StringValue': 'FULL',
                    'DataType': 'String'
                }
            },
            'MessageBody': 'boto3'
        }
        if idx is not None:
            msg['Id'] = str(idx)
        return msg

    ###############
    ### HELPERS ###
    ###############

    @staticmethod
    async def _format(inputs):
        ### Inputs could be one of three forms --> convert as necessary
        # 1. List of bits
        # 2. List of booleans
        # 3. String of bits (required for eval)
        converted_inputs = ''
        if isinstance(inputs, list):
            if len(inputs) > 0:
                if isinstance(inputs[0], int):
                    for x in inputs:
                        if x == 0:
                            converted_inputs += '0'
                        elif x == 1:
                            converted_inputs += '1'
                elif isinstance(inputs[0], bool):
                    for x in inputs:
                        if x == False:
                            converted_inputs += '0'
                        elif x == True:
                            converted_inputs += '1'
            else:
                print('--> INPUT LIST EMPTY')
                return None
        else:
            converted_inputs = inputs
        return converted_inputs

    async def _dataset_id(self, dataset_id=None):
        if dataset_id:
            return dataset_id
        else:
            return self.dataset_id

    async def _validation(self, inputs):
        inputs = await Evaluation._format(inputs)

        # 1. Check if dataset is read only
        if await self.d_client.check_dataset_read_only():
            print('--> DATASET IS READ ONLY:', self.dataset_id)
            return {"status": "Dataset is read only", "code": "read_only_dataset"}

        # 2. Check if design already exists
        architecture = await self.d_client.check_existing_architecture(inputs)
        if architecture:
            print('--> ARCHITECTURE ALREADY EXISTS:', self.dataset_id)
            return {"status": "Architecture already exists", "code": "arch_repeated", "arch_id": architecture['id']}

        return None

    @staticmethod
    def input_conversion(inputs):
        ### Inputs could be one of three forms --> convert as necessary
        # 1. List of bits
        # 2. List of booleans
        # 3. String of bits (required for eval)
        converted_inputs = ''
        if isinstance(inputs, list):
            if len(inputs) > 0:
                if isinstance(inputs[0], int):
                    for x in inputs:
                        if x == 0:
                            converted_inputs += '0'
                        elif x == 1:
                            converted_inputs += '1'
                elif isinstance(inputs[0], bool):
                    for x in inputs:
                        if x == False:
                            converted_inputs += '0'
                        elif x == True:
                            converted_inputs += '1'
            else:
                print('--> INPUT LIST EMPTY')
                return None
        else:
            converted_inputs = inputs
        return converted_inputs

