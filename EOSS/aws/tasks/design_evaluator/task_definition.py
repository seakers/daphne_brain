family = 'user-n-design-evaluator-task'

executionRoleArn = "arn:aws:iam::923405430231:role/ecsTaskExecutionRole"
taskRoleArn = "arn:aws:iam::923405430231:role/DaphneEvaluatorTaskRole"

cpu = "1024"
memory = "4096"
memoryReservation = "2048"
networkMode = 'awsvpc'


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
    'FARGATE',
    'EC2'
]

requiresCompatibilities = [
    'FARGATE'
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

