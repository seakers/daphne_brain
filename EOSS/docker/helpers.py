from EOSS.aws.utils import get_boto3_client





def create_or_purge_queue(queue_name):
    sqs_client = get_boto3_client('sqs')
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            sqs_client.purge_queue(QueueUrl=queue_url)
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    return None


def get_or_create_queue(queue_name):
    sqs_client = get_boto3_client('sqs')
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    print('--> GET OR CREATE QUEUE RETURNING NONE --> SMTH WRONG')
    return None


