import copy
import botocore
import json
import asyncio


# --> AWS Tools
from EOSS.aws.utils import get_boto3_client, exponential_backoff_sleep
from EOSS.aws.clients.SqsClient import SqsClient
from EOSS.aws.tasks.design_evaluator import task_definition as design_evaluator_task_definition
from EOSS.aws.tasks.design_evaluator import task_instance as design_evaluator_task
from EOSS.aws.utils import _save_eosscontext, find_obj_and_set, call_boto3_client_async



class EcsClient:

    def __init__(self, user_info):
        print('--> CREATING ECS CLIENT')
        self.user_info = user_info
        self.user_id = self.user_info.user.id
        self.eosscontext = user_info.eosscontext

        

        # --> Cluster Info: daphne-cluster
        self.cluster_name = 'daphne-dev-cluster'
        # self.cluster_arn = self.eosscontext.cluster_name


        


    # --> This is called to validate all user-specific services / tasks exist
    async def initialize(self):

        # --> Initialize Sqs Client
        # await self.sqs_client.initialize()


        # --> 1. Validate daphne-cluster exists
        self.cluster_arn = await self.get_or_create_cluster(self.cluster_name)
        

        # --> 2. Validate user specific task definitions exist
        if self.design_evaluator_task_name is None:
            self.design_evaluator_task_name = 'user-' + str(self.user_id) + '-design-evaluator-task'
        self.design_evaluator_task_arn = await self.get_or_create_task_definition(
            self.design_evaluator_task_name,
            'design-evaluator'
        )
        
        # if self.genetic_algorithm_task_name is None:
        #     self.genetic_algorithm_task_name = 'user-' + str(self.user_id) + '-genetic-algorithm-task'
        # self.genetic_algorithm_task_arn = await self.get_or_create_task_definition(
        #     self.genetic_algorithm_task_name,
        #     'genetic-algorithm'
        # )


        # --> 3. Run requested number of user tasks
        # de_response = await self.regulate_design_evaluator_tasks()
        # ga_response = await self.regulate_genetic_algorithm_tasks()


    ###############
    ### Cluster ###
    ###############

    @staticmethod
    async def get_or_create_cluster(cluster_name):
        cluster_arn = await EcsClient.cluster_exists(cluster_name)
        if cluster_arn is None:            
            response = await call_boto3_client_async('ecs', 'create_cluster', {
                "clusterName": cluster_name,
                "capacityProviders":  ['FARGATE'],
                "tags":  [{'key': 'name', 'value': cluster_name}]
            })
            
            return response['cluster']['clusterArn']
        else:
            return cluster_arn

    @staticmethod
    async def cluster_exists(cluster_name):
        list_cluster_response = await call_boto3_client_async('ecs', 'list_clusters')
        if 'clusterArns' not in list_cluster_response:
            return None
        cluster_arns = list_cluster_response['clusterArns']
        response = await call_boto3_client_async('ecs', 'describe_clusters', {'clusters': cluster_arns, 'include': ['ATTACHMENTS', 'SETTINGS']})
        clusters = response['clusters']
        for cluster in clusters:
            if cluster['clusterName'] == cluster_name:
                return cluster['clusterArn']
        return None



    ########################
    ### Task Definitions ###
    ########################


    """ Get / Create Task Definition
    - Returns task definition ARN
    """
    async def get_or_create_task_definition(self, task_name, task_type):

        # --> Get task arn and return if exists
        task_arn = await self.task_definition_exists(task_name)
        if task_arn is not None:
            return task_arn

        # --> Create task and return ARN
        if task_type == 'design-evaluator':
            return await self.register_design_evaluator_task_definition(task_name)
        elif task_type == 'genetic-algorithm':
            return await self.register_genetic_algorithm_task_definition(task_name)
        else:
            return None


    async def task_definition_exists(self, task_name):
        try:
            response = await call_boto3_client_async('ecs', 'describe_task_definition', {
                "taskDefinition": task_name
            })
            if response is None or 'taskDefinition' not in response:
                return None
            return response['taskDefinition']['taskDefinitionArn']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None




    # Family: user-1-design-evaluator-task
    async def register_design_evaluator_task_definition(self, task_name):

        # --> 1. Configure task definition
        task_config = (json.load(open('/app/EOSS/aws/tasks/design-evaluator.json')))['task_definition']
        task_config['family'] = task_name
        task_config['containerDefinitions'][0]['name'] = task_name

        # --> 2. Register task
        try:
            response = await call_boto3_client_async('ecs', 'register_task_definition', task_config)
            if response is None or 'taskDefinition' not in response:
                return None
            return response['taskDefinition']['taskDefinitionArn']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR REGISTERING TASK DEFINITION', error)
            return None



    # Family: user-1-genetic-algorithm-task
    async def register_genetic_algorithm_task_definition(self, task_name):
        return None




    #############
    ### Tasks ###
    #############

    async def describe_task(self, task_arn):
        try:
            response = await call_boto3_client_async('ecs', 'describe_tasks', {
                "cluster": self.cluster_arn,
                "tasks": [task_arn],
                "include": ['TAGS']
            })
            return response['tasks'][0]
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    async def get_task_arns(self, task_definition_arn):
        try:
            response = await call_boto3_client_async('ecs', 'list_tasks', {
                "cluster": self.cluster_arn,
                "family": task_definition_arn
            })
            return response['taskArns']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    """ Regulator Pattern
    - The first pattern my intuition came up with when thinking about how to regulate
    a number of task instances. Starts and stops tasks based on the current number running and 
    the requested number stored in EOSSContext
    
    """


    # --> Regulate: design-evaluator
    async def regulate_design_evaluator_tasks(self):
        print('--> REGULATING DESIGN EVALUATOR TASKS')

        # --> 1. Determine number of current tasks
        task_arns = await self.get_task_arns(self.design_evaluator_task_name)
        if task_arns is None:
            return None
        num_current_tasks = len(task_arns)

        # --> 2. Regulate tasks based on user eoss context value
        if num_current_tasks < self.design_evaluator_task_count:
            print('--> start services')
            num_start = abs(num_current_tasks - self.design_evaluator_task_count)
            for idx in range(num_start):
                num_current_tasks += 1
                await self.start_design_evaluator_task()
        elif num_current_tasks > self.design_evaluator_task_count:
            num_stop = abs(num_current_tasks - self.design_evaluator_task_count)
            for idx in range(num_stop):
                await self.stop_design_evaluator_task(task_arns[idx])
        else:
            return None

    # --> Start: design-evaluator
    async def start_design_evaluator_task(self):

        """ 1. Create Queues for Design Evaluator
        1. user-1-design-evaluator-private-request-queue-XXXXX
        2. user-1-design-evaluator-private-response-queue-XXXXX
        3. user-1-design-evaluator-ping-request-queue-XXXXX
        4. user-1-design-evaluator-ping-response-queue-XXXXX
        """
        instance_private_request_queue_url = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-request-queue'
        )

        instance_private_response_queue_url = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-private-response-queue'
        )

        instance_ping_request_queue_url = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-request-queue'
        )

        instance_ping_response_queue_url = await self.sqs_client.create_queue_name_unique(
            'user-' + str(self.user_id) + '-design-evaluator-ping-response-queue'
        )


        # --> 2. Create task configuration object
        task_config = (json.load(open('/app/EOSS/aws/tasks/design-evaluator.json')))['task_instance']
        task_config['cluster'] = self.cluster_arn

        task_config['overrides']['containerOverrides'][0]['name'] = self.design_evaluator_task_name
        task_config['overrides']['containerOverrides'][0]['environment'] = [
            {'name': 'EVAL_REQUEST_URL', 'value': self.eosscontext.design_evaluator_request_queue_url},
            {'name': 'EVAL_RESPONSE_URL', 'value': self.eosscontext.design_evaluator_response_queue_url},
            {'name': 'PRIVATE_REQUEST_URL', 'value': instance_private_request_queue_url},
            {'name': 'PRIVATE_RESPONSE_URL', 'value': instance_private_response_queue_url},
            {'name': 'PING_REQUEST_URL', 'value': instance_ping_request_queue_url},
            {'name': 'PING_RESPONSE_URL', 'value': instance_ping_response_queue_url},
        ]
        task_config['tags'] = [
            {'key': 'PRIVATE_REQUEST_URL', 'value': instance_private_request_queue_url},
            {'key': 'PRIVATE_RESPONSE_URL', 'value': instance_private_response_queue_url},
            {'key': 'PING_REQUEST_URL', 'value': instance_ping_request_queue_url},
            {'key': 'PING_RESPONSE_URL', 'value': instance_ping_response_queue_url},
        ]
        task_config['taskDefinition'] = self.design_evaluator_task_arn


        try:
            response = await call_boto3_client_async('ecs', 'run_task', task_config)
            if response is None or 'tasks' not in response:
                print('--> ERROR: could not start service')
                return None
            return response['tasks'][0]['taskArn']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR', error)
            return None

    async def wait_for_task_exponential(self, task_definition_arn, task_arn):
        iter_count = 0
        error_count = 0
        error_max = 5

        curr_task_arns = await self.get_task_arns(task_definition_arn)
        if curr_task_arns is None:
            error_count += 1
            curr_task_arns = []

        while (task_arn not in curr_task_arns) and (error_count < error_max):
            await exponential_backoff_sleep(iter_count)
            iter_count += 1
            curr_task_arns = await self.get_task_arns(task_definition_arn)
            if curr_task_arns is None:
                error_count += 1
                curr_task_arns = []

    # --> Stop: design-evaluator
    async def stop_design_evaluator_task(self, task_arn):

        # --> 1. Get queues to delete from container
        task = self.describe_task(task_arn)
        if task is None:
            return None
        delete_queue_urls = []
        delete_queue_urls.append(next(item for item in task['tags'] if item['key'] == 'PING_REQUEST_URL'))
        delete_queue_urls.append(next(item for item in task['tags'] if item['key'] == 'PING_RESPONSE_URL'))
        delete_queue_urls.append(next(item for item in task['tags'] if item['key'] == 'PRIVATE_REQUEST_URL'))
        delete_queue_urls.append(next(item for item in task['tags'] if item['key'] == 'PRIVATE_RESPONSE_URL'))

        # --> 2. Stop container
        await self.stop_task(task_arn)

        # --> 3. Delete queues
        for queue_url in delete_queue_urls:
            await self.sqs_client.delete_queue_url(queue_url)

    async def stop_task_and_wait(self, task_arn, task_definition_arn):
        response = await self.stop_task(task_arn)
        if response is None:
            return None

        iter_count = 0
        error_count = 0
        error_max = 5

        curr_task_arns = await self.get_task_arns(task_definition_arn)
        if curr_task_arns is None:
            error_count += 1
            curr_task_arns = []

        while task_arn in curr_task_arns:
            await exponential_backoff_sleep(iter_count)
            iter_count += 1
            curr_task_arns = await self.get_task_arns(task_definition_arn)
            if curr_task_arns is None:
                error_count += 1
                curr_task_arns = []
            if error_count >= error_max:
                return None

        return response

    async def stop_task(self, task_arn):
        try:
            response = await call_boto3_client_async('ecs', 'stop_task', {
                "cluster": self.cluster_arn,
                "task": task_arn
            })
            return response['task']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR STOPPING TASK', error, task_arn)
            return None




    # --> Regulate: genetic-algorithm
    async def regulate_genetic_algorithm_tasks(self):
        return None












    ############################
    ### Service (DEPRECATED) ###
    ############################

    """ Service Types
        1. design-evaluator   - user-1-design-evaluator-service
        2. genetic-algorithm  - user-1-genetic-algorithm-service

    - Returns service ARN
    """

    async def get_or_create_service(self, service_name, service_type, task_arn):
        service_arn = await self.service_exists(service_name)
        if service_arn is None:
            if service_type == 'design-evaluator':
                return await self.create_design_evaluator_service(service_name, task_arn)
            elif service_type == 'genetic-algorithm':
                return await self.create_genetic_algorithm_service(service_name, task_arn)
        return service_arn

    async def service_exists(self, service_name):

        # --> 1. List cluster service arns
        response = await call_boto3_client_async('ecs', 'list_services', {
            "cluster": self.cluster_name
        })
        if 'serviceArns' not in response:
            return None
        service_arns = response['serviceArns']

        # --> 2. Describe services by arn
        response = await call_boto3_client_async('ecs', 'describe_services', {
            "cluster": self.cluster_name,
            "services": service_arns
        })

        # --> 3. Match the service by name
        for service in response['services']:
            if service_name == service['serviceName']:
                return service['serviceArn']
        return None

    """ Create Functions
    - Returns service ARN

    """
    async def create_design_evaluator_service(self, service_name, task_arn):

        # --> Configure service settings
        service_config = copy.deepcopy(design_evaluator_task)
        service_config.cluster = self.cluster_arn
        service_config.serviceName = service_name
        service_config.desiredCount = 0

        # --> Create service
        try:
            response = await call_boto3_client_async('ecs', 'create_service', {
                "cluster": service_config.cluster,
                "serviceName": service_config.serviceName,
                "desiredCount": service_config.desiredCount,
                "schedulingStrategy": service_config.schedulingStrategy,
                "deploymentController": service_config.deploymentController,
                "enableECSManagedTags": service_config.enableECSManagedTags,
                "propagateTags": service_config.propagateTags,
                "placementConstraints": service_config.placementConstraints
            })
            return response['service']['serviceArn']
        except botocore.exceptions.ClientError as error:
            print('--> ERROR CREATING SERVICE', error)
            return None

    async def create_genetic_algorithm_service(self, service_name, task_arn):
        return None

    ###############
    ### Helpers ###
    ###############

