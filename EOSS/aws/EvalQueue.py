import boto3

from EOSS.aws.utils import dev_client, prod_client


class EvalQueue:


    def __init__(self, dev=False):
        self.region = 'us-east-2'
        self.queue_name_prefix = 'evaluator-queue-'
        if dev:
            self.client = dev_client('sqs')
        else:
            self.client = prod_client('sqs')



    def create_eval_queue(self, problem_id):
        queue_name = self.queue_name_prefix + str(problem_id)
        response = self.client.create_queue(
            QueueName=queue_name,
            tags={
                'PROBLEM_ID': str(problem_id),
                'TYPE': 'EVAL'
            }
        )
        queue_url = response['QueueUrl']
        return queue_url

    def delete_queue(self, queue_url):
        self.client.delete_queue(
            QueueUrl=queue_url
        )

    def get_queue_url(self, problem_id):
        queue_name = self.queue_name_prefix + str(problem_id)
        response = self.client.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        return queue_url

    def does_queue_exist(self, problem_id):
        list_response = self.client.list_queues()
        queue_urls = list_response['QueueUrls']
        for url in queue_urls:
            tags = self.client.list_queue_tags(QueueUrl=url)['Tags']
            if 'PROBLEM_ID' in tags:
                if tags['PROBLEM_ID'] == str(problem_id):
                    return True
        return False

    def get_all_eval_queue_urls(self):
        list_response = self.client.list_queues()
        if 'QueueUrls' not in list_response:
            print('--> NO EVAL QUEUES EXIST')
            return []
        else:
            queue_urls = list_response['QueueUrls']
            url_list = []
            for url in queue_urls:
                tags = self.client.list_queue_tags(QueueUrl=url)['Tags']
                if 'TYPE' in tags:
                    if tags['TYPE'] == 'EVAL':
                        url_list.append(url)
            return url_list


    def delete_all_eval_queues(self):
        urls = self.get_all_eval_queue_urls()
        for url in urls:
            self.delete_queue(url)


