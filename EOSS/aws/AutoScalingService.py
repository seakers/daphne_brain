import os
import boto3

from EOSS.aws.Task import Task
from EOSS.aws.Cluster import Cluster
from EOSS.aws.Service import Service

from EOSS.aws.utils import graphql_server_address
from EOSS.aws.utils import graphql_server_address_ws




# When a new problem is created, this class handles setting up the load balancing process for the new queue


class AutoScalingService:


    def __init__(self, problem_info, cluster_arn, dev=False):
        self.problem_id = problem_info['id']
        self.group_id = problem_info['group_id']
        self.queue_url = problem_info['queue_url']
        self.graphql_server_address = graphql_server_address(dev)
        self.graphql_server_address_ws = graphql_server_address_ws(dev)
        self.cluster_arn = cluster_arn
        self.dev = dev


    def build(self):

        self.print_attributes()

        # 1. Create a new task definition for the problem
        task = Task(dev=self.dev)
        task_definition_arn = task.register_task_definition(
            self.group_id,
            self.problem_id,
            self.queue_url,
            self.graphql_server_address,
            self.graphql_server_address_ws
        )
        print('--> TASK DEFINITION ARN', task_definition_arn)

        # 2. Create a new service to auto-scale the task definition
        # service_arn = Service(self.cluster_arn).build_service(self.problem_id, task_definition_arn)
        # return service_arn


        print('------------------------------------------\n\n\n')


    def print_attributes(self):
        print('\n\n\n---------- AUTO SCALING SERVICE ----------')
        print('---> group_id', self.group_id)
        print('---> problem_id', self.problem_id)
        print('---> queue_url', self.queue_url)
        print('---> graphql_server_address', self.graphql_server_address)
        print('---> graphql_server_address_ws', self.graphql_server_address_ws)
        print('---> cluster_arn', self.cluster_arn)