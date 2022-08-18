


family = 'design-evaluator'

cpu = "1024"
memory = "4096"
memoryReservation = "2048"

executionRoleArn = "arn:aws:iam::923405430231:role/ecsTaskExecutionRole"
taskRoleArn = "arn:aws:iam::923405430231:role/DaphneEvaluatorTaskRole"

containerDefinitions = [
    {
        'name': 'design-evaluator',
        'image': '923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator:latest',
        'cpu': 123,
        'memory': 123,
        'portMappings': [
            {
                'containerPort': 123,
                'hostPort': 123,
                'protocol': 'tcp' | 'udp'
            },
        ],
        'essential': True,
        'command': [
            'string',
        ],
        'environment': [
            {'name': 'PING_REQUEST_URL', 'value': 'string'},
            {'name': 'PING_RESPONSE_URL', 'value': 'string'},
            {'name': 'PRIVATE_REQUEST_URL', 'value': 'string'},
            {'name': 'PRIVATE_RESPONSE_URL', 'value': 'string'},
            {'name': 'EVAL_REQUEST_URL', 'value': 'string'},
            {'name': 'EVAL_RESPONSE_URL', 'value': 'string'}
        ],
        'mountPoints': [
            {
                'sourceVolume': 'vassar_resources',
                'containerPath': '/resources',
                'readOnly': False
            },
        ],
        'logConfiguration': {
            'logDriver': 'awslogs'
        }
    }
]


compatibilities = [
    'FARGATE',
    'EC2'
],

requiresCompatibilities = [
    'FARGATE'
],


volumes = [
    {
        'name': 'vassar_resources',
        'efsVolumeConfiguration': {
            'fileSystemId': 'string',
            'rootDirectory': '/VASSAR_resources',
            'transitEncryption': 'ENABLED'
        }
    },
],


tags = [
    {'key': 'user_id', 'value': '1'},
    {'key': 'type', 'value': 'design-evaluator'}
]

