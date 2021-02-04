import os
import json
import time
import boto3

from EOSS.aws.utils import dev_client, prod_client
from EOSS.aws.utils import eval_task_iam_arn


class Task:

    def __init__(self, dev=False):
        if dev:
            self.client = dev_client('ecs')
        else:
            self.client = prod_client('ecs')



    def register_task_definition(self,
                                 group_id,
                                 problem_id,
                                 eval_queue_url,
                                 apollo_url,
                                 apollo_ws_url,
                                 request_mode='CRISP-ATTRIBUTES'
                                 ):
        task_arn = self.does_task_exist(problem_id)
        print('---> TASK DEFINITION VALUE:', task_arn)
        if task_arn is None:
            response = self.client.register_task_definition(
                family='evaluator',
                taskRoleArn=eval_task_iam_arn(),
                networkMode='awsvpc',
                requiresCompatibilities=['FARGATE'],
                cpu='1 vCPU',
                memory='2 GB',
                containerDefinitions=[
                    {
                        "name": "vassar",
                        "image": "apazagab/design-evaluator",
                        "privileged": False,
                        "interactive": True,
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            'options': {
                                'awslogs-region': 'us-east-2',
                                'awslogs-group': 'seakers-evaluation-logs',
                                'awslogs-stream-prefix': 'daphne-eval-logs'
                            }
                        },
                        "environment": [
                            {"name": "PROBLEM_ID", "value": str(problem_id)},
                            {"name": "GROUP_ID", "value": str(group_id)},
                            {"name": "REQUEST_MODE", "value": str(request_mode)},
                            {"name": "PRIVATE_QUEUE_NAME", "value": "RANDOM"},
                            {"name": "EVAL_QUEUE_URL", "value": str(eval_queue_url)},
                            {"name": "APOLLO_URL_WS", "value": str(apollo_url)},
                            {"name": "APOLLO_URL", "value": str(apollo_ws_url)}
                        ]
                    }
                ],
                tags=[
                    {
                        'key': 'PROBLEM_ID',
                        'value': str(problem_id)
                    },
                    {
                        'key': 'TYPE',
                        'value': 'EVAL'
                    }
                ],

            )
            return response['taskDefinition']['taskDefinitionArn']
        else:
            return task_arn


    def does_task_exist(self, problem_id):
        response = self.client.list_task_definitions(familyPrefix='evaluator', sort='ASC')
        if 'taskDefinitionArns' not in response:
            return None
        task_arns = response['taskDefinitionArns']
        for task_arn in task_arns:
            description = self.client.describe_task_definition(taskDefinition=task_arn)
            if 'tags' not in description:
                continue
            tags = description['tags']
            for tag in tags:
                if tag['key'] == 'PROBLEM_ID' and tag['value'] == str(problem_id):
                    return description['taskDefinition']['taskDefinitionArn']
        return None


    def delete_all_eval_task_definitions(self):

        # 1. Get all task definition arns in the correct family
        list_response = self.client.list_task_definitions(familyPrefix='evaluator')
        print('---> TASK DEFINITIONS', list_response)
        if 'taskDefinitionArns' not in list_response:
            print('---> NO TASK DEFINITIONS FOUND')
            return
        task_def_arns = list_response['taskDefinitionArns']

        # 2. Deregister all task definitions
        for task_def_arn in task_def_arns:
            print('---> DEREGISTERING TASK', task_def_arn)
            self.client.deregister_task_definition(taskDefinition=task_def_arn)
        return











