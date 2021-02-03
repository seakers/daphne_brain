from django.core.management.base import BaseCommand, CommandError
import pprint

from EOSS.graphql.api import GraphqlClient
from EOSS.aws.EvalQueue import EvalQueue
from EOSS.aws.Cluster import Cluster
from EOSS.aws.Task import Task
from EOSS.aws.AutoScalingService import AutoScalingService


class Command(BaseCommand):
    help = 'Configures aws for scalable daphne architecture'

    def proceed_value(self):
        response = input('\nWARNING: this command will wipe all AWS Queues and Task Definitions to create fresh ones. Type yes to proceed: ')
        if response != 'yes':
            print('EXITING COMMAND')
            return False
        else:
            return True

    def pprint(self, to_print):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(to_print)


    def remove_all_aws_eval_resources(self, dev):
        cluster_client = Cluster(dev=dev)
        cluster_client.remove_services()
        task_client = Task(dev=dev)
        task_client.delete_all_eval_task_definitions()
        queue_client = EvalQueue(dev=dev)
        queue_client.delete_all_eval_queues()



    def handle(self, *args, **options):
        print('---> CONFIGURING DAPHNE AWS ARCHITECTURE')
        if not self.proceed_value():
            return

        # 1. Get problem ids
        graphql_client = GraphqlClient()
        problems = graphql_client.get_problems()
        self.pprint(problems)

        # 2. Delete all cluster services, task definitions, and pre-existing eval queues
        self.remove_all_aws_eval_resources(dev=True)

        # 3. For each problem id, create an eval queue and store the url
        # queue_client = EvalQueue(dev=True)
        # for problem in problems:
        #     url = queue_client.create_eval_queue(problem['id'])
        #     problem['queue_url'] = url
        # self.pprint(problems)

        # 4. For each problem, creating an auto scaling service
        # service_arns = []
        # cluster_arn = Cluster().get_or_create_cluster()
        # for problem in problems:
        #     service = AutoScalingService(problem, cluster_arn)
        #     service_arns.append(service.build())














