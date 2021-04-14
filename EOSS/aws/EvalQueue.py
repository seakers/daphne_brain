import boto3

from EOSS.aws.utils import get_boto3_client, user_input, pprint


class EvalQueue:


    def __init__(self):
        self.region = 'us-east-2'
        self.queue_name_prefix = 'user-queue-'
        self.client = get_boto3_client('sqs')


    def create_ga_queue(self):
        response = self.client.create_queue(
            QueueName=self.ga_queue_name,
            tags={
                'TYPE': 'GA'
            }
        )
        print('---> CREATE QUEUE RESPONSE', response)
        queue_url = response['QueueUrl']
        return queue_url

    def create_user_queues(self, user_id):
        request_queue_name = self.queue_name_prefix + 'request-' + str(user_id)
        response_queue_name = self.queue_name_prefix + 'response-' + str(user_id)
        response = self.client.create_queue(
            QueueName=request_queue_name,
            tags={
                'USER_ID': str(user_id)
            }
        )
        print('---> CREATE QUEUE RESPONSE', response)
        request_queue_url = response['QueueUrl']
        response = self.client.create_queue(
            QueueName=response_queue_name,
            tags={
                'USER_ID': str(user_id)
            }
        )
        print('---> CREATE QUEUE RESPONSE', response)
        response_queue_url = response['QueueUrl']
        return request_queue_url, response_queue_url

    def get_or_create_ga_queue(self):
        list_response = self.client.list_queues()
        if 'QueueUrls' not in list_response:
            return self.create_ga_queue()
        queue_urls = list_response['QueueUrls']
        print(list_response)
        for url in queue_urls:
            tag_response = self.client.list_queue_tags(QueueUrl=url)
            if 'Tags' in tag_response:
                tags = self.client.list_queue_tags(QueueUrl=url)['Tags']
                if 'TYPE' in tags:
                    if tags['TYPE'] == 'GA':
                        return url
        return self.create_ga_queue()



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



    def delete_all_eval_queues(self):
        print('\n\n---------- REMOVING SQS QUEUES ----------')
        urls = self.get_all_eval_queue_urls()
        pprint(urls)
        if not user_input('\n ---> The queues above are going to be deleted, would you like to continue? (yes/no):  '):
            exit(0)
        for url in urls:
            self.delete_queue(url)
        print('--- FINISHED\n\n')


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
                    if tags['TYPE'] == 'EVAL' or tags['TYPE'] == 'GA':
                        url_list.append(url)
            return url_list

    def delete_queue(self, queue_url):
        self.client.delete_queue(
            QueueUrl=queue_url
        )