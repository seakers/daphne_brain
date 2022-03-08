import boto3

from EOSS.aws.utils import dev_client, prod_client
from EOSS.aws.utils import eval_subnet

class Service:

    def __init__(self, cluster_arn, dev=False):
        if dev:
            self.client = dev_client('ecs')
        else:
            self.client = prod_client('ecs')
        self.cluster_arn = str(cluster_arn)


    def build_service(self, problem_id, task_definition_arn):
        service_arn = self.does_service_exist(problem_id)
        if service_arn is not None:
            return service_arn
        else:
            service_name = Service.formulate_service_name(problem_id)
            response = self.client.create_service(
                cluster=self.cluster_arn,
                serviceName=service_name,
                taskDefinition=task_definition_arn,
                desiredCount=1,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [eval_subnet()],
                        'assignPublicIp': 'DISABLED'
                    }
                },
                schedulingStrategy='REPLICA',
                deploymentController={'type': 'ECS'},
                tags=[
                    {'key': 'PROBLEM_ID', 'value': str(problem_id)},
                    {'key': 'TYPE', 'value': 'EVAL'}
                ]
            )
            return response['service']['serviceArn']


    def does_service_exist(self, problem_id):
        service_name = Service.formulate_service_name(problem_id)
        service_arns = self.get_cluster_service_arns()
        response = self.client.describe_services(
            cluster=self.cluster_arn,
            services=service_arns,
        )
        for service in response['services']:
            if service['serviceName'] == service_name:
                return service['serviceArn']
        return None


    def get_cluster_service_arns(self):
        response = self.client.list_services(
            cluster=self.cluster_arn,
            launchType='FARGATE',
        )
        return response['serviceArns']


    @staticmethod
    def formulate_service_name(problem_id):
        return 'evaluator-service-' + str(problem_id)


