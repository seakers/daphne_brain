import boto3

from EOSS.aws.utils import dev_client, prod_client




class Cluster:

    def __init__(self, dev=False):
        if dev:
            self.client = dev_client('ecs')
        else:
            self.client = prod_client('ecs')
        self.cluster_name = 'evaluator-cluster'


    def get_or_create_cluster(self):
        cluster_arn = self.does_cluster_exist(self.cluster_name)
        if cluster_arn is None:
            response = self.client.create_cluster(
                clusterName=self.cluster_name,
                capacityProviders=['FARGATE'],
                tags=[
                    {'key': 'name', 'value': 'evaluator-cluster'}
                ]
            )
            return response['cluster']['clusterArn']
        else:
            return cluster_arn

    def does_cluster_exist(self, cluster_name):
        cluster_arns = self.client.list_clusters()['clusterArns']
        clusters = self.client.describe_clusters(clusters=cluster_arns, include=['ATTACHMENTS', 'SETTINGS'])['clusters']
        for cluster in clusters:
            if cluster['clusterName'] == cluster_name:
                return cluster['clusterArn']
        return None


 #  _____                                       _____                     _
 # |  __ \                                     / ____|                   (_)
 # | |__) | ___  _ __ ___    ___ __   __ ___  | (___    ___  _ __ __   __ _   ___  ___  ___
 # |  _  / / _ \| '_ ` _ \  / _ \\ \ / // _ \  \___ \  / _ \| '__|\ \ / /| | / __|/ _ \/ __|
 # | | \ \|  __/| | | | | || (_) |\ V /|  __/  ____) ||  __/| |    \ V / | || (__|  __/\__ \
 # |_|  \_\\___||_| |_| |_| \___/  \_/  \___| |_____/  \___||_|     \_/  |_| \___|\___||___/


    def remove_services(self):
        # 1. Get all the services in the evaluator cluster
        service_arns = self.get_cluster_service_arns()
        if not service_arns:
            return 0

        # 2. Stop all the tasks for each service in the cluster
        service_details = self.get_cluster_service_descriptions(service_arns)
        for details in service_details:
            self.stop_service_tasks(details)
            self.update_service_desired_task_count(details)
            self.delete_service(details)



    def delete_service(self, service_details):
        response = self.client.delete_service(
            cluster=self.cluster_name,
            service=service_details['serviceName'],
            force=True
        )

    def update_service_desired_task_count(self, service_details, count=0):
        response = self.client.update_service(
            cluster=self.cluster_name,
            service=service_details['serviceName'],
            desiredCount=count
        )
        return

    def stop_service_tasks(self, service_details):
        # 1. List all tasks and filter on service
        list_tasks_response = self.client.list_tasks(
            cluster=self.cluster_name,
            serviceName=service_details['serviceName'],
            launchType='FARGATE'
        )
        if 'taskArns' not in list_tasks_response:
            # The service has no tasks
            return
        task_arns = list_tasks_response['taskArns']

        # 2. Stop returned tasks
        for task_arn in task_arns:
            stop_task_response = self.client.stop_task(task=task_arn)
        return



    def get_cluster_service_arns(self):
        # Check to see if the cluster exists first
        cluster_arn = self.does_cluster_exist(self.cluster_name)
        if cluster_arn is None:
            return []

        response = self.client.list_services(
            cluster=self.cluster_name,
            launchType='FARGATE',
        )
        if 'serviceArns' not in response:
            return []
        else:
            return response['serviceArns']

    def get_cluster_service_descriptions(self, service_arns):
        response = self.client.describe_services(
            cluster=self.cluster_name,
            services=service_arns,
            include=[
                'TAGS',
            ]
        )
        if 'services' not in response:
            return []
        else:
            return response['services']



