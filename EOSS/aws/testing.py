import boto3
import botocore
import os

#### --- SERVICE DEFINITION

cluster='daphne-cluster'  # or cluster ARN
serviceName='user-n-design-evaluator-service'
taskDefinition='user-1-design-evaluator-task' # or task definition ARN


desiredCount=0


launchType='EXTERNAL'


overrides = {
    'containerOverrides': [
        {
            'name': 'design-evaluator',
            'environment': [
                {'name': 'PING_REQUEST_URL', 'value': 'NULL'},      # Override
                {'name': 'PING_RESPONSE_URL', 'value': 'NULL'},     # Override
                {'name': 'PRIVATE_REQUEST_URL', 'value': 'NULL'},   # Override
                {'name': 'PRIVATE_RESPONSE_URL', 'value': 'NULL'},  # Override
            ]
        }
    ],
}


networkConfiguration={
    'awsvpcConfiguration': {
        'subnets': [
            'subnet-04e3b403f96b248e1',  # daphne-subnet-1
            'subnet-036c4d99822a7606d'   # daphne-subnet-2
        ],
        'securityGroups': [
            'sg-0e497c6b20f939260',
        ],
        'assignPublicIp': 'DISABLED'
    }
}
healthCheckGracePeriodSeconds=0
schedulingStrategy='REPLICA'
deploymentController={
    'type': 'EXTERNAL'
}

enableECSManagedTags=True
propagateTags='TASK_DEFINITION'

placementConstraints=[
    {
        'type': 'distinctInstance'
    }
]



#### --- TASK DEFINITION

family = 'user-n-design-evaluator-task'

executionRoleArn = "arn:aws:iam::923405430231:role/ecsTaskExecutionRole"
taskRoleArn = "arn:aws:iam::923405430231:role/DaphneEvaluatorTaskRole"

cpu = "1024"
memory = "4096"
memoryReservation = "2048"

containerDefinitions = [
    {
        'name': 'design-evaluator',
        'image': '923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator:latest',
        'cpu': 1024,
        'memory': 4096,
        'memoryReservation': 2048,
        'essential': True,
        'command': [
            '/app/evaluator/bin/evaluator',
        ],
        'environment': [
            {'name': 'DEPLOYMENT_TYPE', 'value': 'AWS'},

            {'name': 'APOLLO_URL', 'value': 'http://graphql.daphne.local:8080/v1/graphql'},
            {'name': 'APOLLO_URL_WS', 'value': 'ws://graphql.daphne.local:8080/v1/graphql'},

            {'name': 'PING_REQUEST_URL', 'value': 'NULL'},
            {'name': 'PING_RESPONSE_URL', 'value': 'NULL'},
            {'name': 'PRIVATE_REQUEST_URL', 'value': 'NULL'},
            {'name': 'PRIVATE_RESPONSE_URL', 'value': 'NULL'},
            {'name': 'EVAL_REQUEST_URL', 'value': 'NULL'},
            {'name': 'EVAL_RESPONSE_URL', 'value': 'NULL'},

            {'name': 'CLUSTER_ARN', 'value': 'arn:aws:ecs:us-east-2:923405430231:cluster/daphne-cluster'},
            {'name': 'SERVICE_ARN', 'value': 'NULL'},

            {'name': 'JAVA_OPTS', 'value': '-Xmx3840m'},
        ],
        'mountPoints': [
            {
                'sourceVolume': 'vassar_resources',
                'containerPath': '/resources',
                'readOnly': False
            },
        ],
        'logConfiguration': {
            'logDriver': 'awslogs',
            "options": {
                "awslogs-group": "daphne-evaluator",
                "awslogs-region": "us-east-2",
                "awslogs-create-group": "true",
                "awslogs-stream-prefix": "daphne"
            }
        }
    }
]

compatibilities = [
    "FARGATE",
    "EC2"
]
networkMode = 'awsvpc'

requiresCompatibilities = [
    "FARGATE"
]

volumes = [
    {
        'name': 'vassar_resources',
        'efsVolumeConfiguration': {
            'fileSystemId': 'fs-d3977da8',
            'rootDirectory': '/VASSAR_resources',
            'transitEncryption': 'ENABLED'
        }
    },
]



def get_client(service):

    client = boto3.client(
        service,
        region_name='us-east-2',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
    )
    return client








################
### Clusters ###
################

def get_cluster_name_from_arn(arn):
    return arn.split('/')[-1]

def test_cluster():

    client = get_client('ecs')
    print(client)

    response = client.list_clusters()

    print(cluster_exists(client, 'daphne-cluster'))




def cluster_exists(ecs_client, cluster_name):
    list_cluster_response = ecs_client.list_clusters()
    if 'clusterArns' not in list_cluster_response:
        return None
    cluster_arns = list_cluster_response['clusterArns']
    describe_clusters_response = ecs_client.describe_clusters(clusters=cluster_arns, include=['ATTACHMENTS', 'SETTINGS'])
    clusters = describe_clusters_response['clusters']
    for cluster in clusters:
        if cluster['clusterName'] == cluster_name:
            return cluster['clusterArn']
    return None




################
### Services ###
################


def test_services():


    get_or_create_service('test-service')




    return 0


def get_or_create_service(service_name):

    ecs_client = get_client('ecs')
    response = ecs_client.list_services(cluster='daphne-cluster')
    if 'serviceArns' not in response:
        return None
    service_arns = response['serviceArns']

    response = ecs_client.describe_services(
        cluster='daphne-cluster',
        services=service_arns
    )

    for service in response['services']:
        print(service['serviceArn'])


    return 0




#############
### Tasks ###
#############


def test_tasks():
    ecs_client = get_client('ecs')


    # response = ecs_client.create_service(
    #     cluster=cluster,
    #     serviceName=serviceName,
    #     desiredCount=desiredCount,
    #     schedulingStrategy=schedulingStrategy,
    #     deploymentController=deploymentController,
    #     enableECSManagedTags=enableECSManagedTags,
    #     propagateTags=propagateTags,
    #     placementConstraints=placementConstraints
    # )



    
    


    # response = ecs_client.register_task_definition(
    #     family='user-n-design-evaluator-task',
    #     taskRoleArn=taskRoleArn,
    #     executionRoleArn=executionRoleArn,
    #     networkMode=networkMode,
    #     containerDefinitions=containerDefinitions,
    #     volumes=volumes,
    #     requiresCompatibilities=requiresCompatibilities,
    #     cpu=cpu,
    #     memory=memory,
    #     tags=[
    #         {'key': 'PING_REQUEST_URL', 'value': 'NULL'},  # Override
    #         {'key': 'PING_RESPONSE_URL', 'value': 'NULL'},  # Override
    #         {'key': 'PRIVATE_REQUEST_URL', 'value': 'NULL'},  # Override
    #         {'key': 'PRIVATE_RESPONSE_URL', 'value': 'NULL'},  # Override
    #     ]
    # )
    # print(response)


    print('--> PRINTING TASKS\n\n\n')

    try:
        response = ecs_client.list_tasks(
            cluster='daphne-cluster',
            family='user-n-design-evaluator-task'
        )
        tasks = response['taskArns']
        print(response)
        print(len(tasks))

        response = ecs_client.describe_tasks(
            cluster='daphne-cluster',
            tasks=tasks,
            include=['TAGS']
        )
        for task in response['tasks']:
            print('\n\n\n', task['tags'])
    except botocore.exceptions.ClientError as error:
        print('--> ERROR', error)
        return None


    # try:
    #     response = ecs_client.describe_task_definition(
    #         taskDefinition='user-n-design-evaluator-task'
    #     )
    #     print(response)
    # except botocore.exceptions.ClientError as error:
    #     print('--> ERROR', error)
    #     return None

    # print('--> PRINTING SERVICES\n\n\n')
    # try:
    #     response = ecs_client.describe_services(
    #         cluster='daphne-cluster',
    #         services=[]
    #     )
    #     print(response)
    # except botocore.exceptions.ClientError as error:
    #     print('--> ERROR', error)
    #     return None


    # try:
    #     response = ecs_client.run_task(
    #         cluster='daphne-cluster',
    #         count=1,
    #         launchType='FARGATE',
    #         networkConfiguration=networkConfiguration,
    #         overrides=overrides,
    #         propagateTags='TASK_DEFINITION',
    #         taskDefinition='arn:aws:ecs:us-east-2:923405430231:task-definition/user-n-design-evaluator-task:5',
    #         tags=[
    #             {'key': 'PING_REQUEST_URL', 'value': 'NULL'},  # Override
    #             {'key': 'PING_RESPONSE_URL', 'value': 'NULL'},  # Override
    #             {'key': 'PRIVATE_REQUEST_URL', 'value': 'NULL'},  # Override
    #             {'key': 'PRIVATE_RESPONSE_URL', 'value': 'NULL'},  # Override
    #         ]
    #     )
    #     print(response)
    # except botocore.exceptions.ClientError as error:
    #     print('--> ERROR', error)
    #     return None

    #
    # try:
    #     response = ecs_client.stop_task(
    #         cluster='daphne-cluster',
    #         task='arn:aws:ecs:us-east-2:923405430231:task/daphne-cluster/a7407b3affc44c74ab7451c2edd9c67d'
    #     )
    #     print(response)
    # except botocore.exceptions.ClientError as error:
    #     print('--> ERROR', error)
    #     return None


    return 0


##############
### Queues ###
##############




def test_queues():
    sqs_client = get_client('sqs')

    try:
        response = sqs_client.create_queue(QueueName='testing-queue')
        print(response)
    except botocore.exceptions.ClientError as error:
        print('--> ERROR', error)
        return None



    return 0






if __name__ == "__main__":
    print("--> TESTING AWS")
    test_tasks()



