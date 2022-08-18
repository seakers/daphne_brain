cluster='daphne-cluster'  # or cluster ARN
serviceName='user-n-design-evaluator-service'
taskDefinition='user-1-design-evaluator-task' # or task definition ARN


desiredCount=0


launchType='FARGATE'




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

tags = [
    {'key': 'PING_REQUEST_URL', 'value': 'NULL'},  # Override
    {'key': 'PING_RESPONSE_URL', 'value': 'NULL'},  # Override
    {'key': 'PRIVATE_REQUEST_URL', 'value': 'NULL'},  # Override
    {'key': 'PRIVATE_RESPONSE_URL', 'value': 'NULL'},  # Override
]






### -----------------------------------------------------------------



capacityProviderStrategy=[
    {
        'capacityProvider': 'string',
        'weight': 123,
        'base': 123
    }
]

clientToken='string'

deploymentConfiguration={
    'deploymentCircuitBreaker': {
        'enable': True,
        'rollback': True
    },
    'maximumPercent': 123,
    'minimumHealthyPercent': 123
}
tags=[
    {
        'key': 'string',
        'value': 'string'
    }
]


role='string'


enableExecuteCommand=True

placementStrategy=[
    {
        'type': 'binpack',
        'field': ''
    }
]


serviceRegistries=[
    {
        'registryArn': 'string',
        'port': 123,
        'containerName': 'string',
        'containerPort': 123
    }
]


loadBalancers=[
    {
        'targetGroupArn': 'string',
        'loadBalancerName': 'string',
        'containerName': 'string',
        'containerPort': 123
    }
]


platformVersion='string'

