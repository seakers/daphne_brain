import docker
import threading
import random
import copy

from EOSS.aws.utils import get_boto3_client

ga_config = {
    'image': 'vassar:ga_experiment',
    'network': 'daphne_service',
    'detach': True,
    'environment': {
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',
        'REGION': 'elasticmq',
        'REQUEST_MODE': 'CRISP-ATTRIBUTES',
        'GA_REQUEST_URL': 'http://localhost:9324/000000000000/ga_request',
        'GA_RESPONSE_URL': 'http://localhost:9324/000000000000/ga_response',
        'DEPLOYMENT_TYPE': 'local',
        'JAVA_OPTS': '-"Dcom.sun.management.jmxremote.rmi.port=10000 -Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10000 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.local.only=false -Djava.rmi.server.hostname=localhost"',
        'AWS_STACK_ENDPOINT': 'http://172.12.0.5:9324',
        'APOLLO_URL': 'http://172.12.0.13:8080/v1/graphql',
        'APOLLO_URL_WS': 'ws://172.12.0.13:8080/v1/graphql',
        'REQUEST_KEY': 'NONE'
    },
    # 'entrypoint': 'gradle run'
}


config = {
    'network': 'daphne_service',
    'detach': True,
    'environment': {
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',
        'REGION': 'elasticmq',
        'REQUEST_MODE': 'CRISP-ATTRIBUTES',
        'VASSAR_REQUEST_URL': 'http://localhost:9324/000000000000/vassar_request',
        'VASSAR_RESPONSE_URL': 'http://localhost:9324/000000000000/vassar_response',
        'DEPLOYMENT_TYPE': 'local',
        'JAVA_OPTS': '-"Dcom.sun.management.jmxremote.rmi.port=10000 -Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10000 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.local.only=false -Djava.rmi.server.hostname=localhost"',
        'AWS_STACK_ENDPOINT': 'http://172.12.0.5:9324',
        'APOLLO_URL': 'http://172.12.0.13:8080/v1/graphql',
        'APOLLO_URL_WS': 'ws://172.12.0.13:8080/v1/graphql',
        'REQUEST_KEY': 'NONE'
    },
    'mem_limit': '2g',
    'cpu_period': 100000,
    'cpu_quota': 100000,
    # 'entrypoint': 'gradle run'
}


def start_container(container_list, docker_api, image, detach, network, environment, name, labels, mem_limit, cpu_period, cpu_quota):
    container_list.append(
        docker_api.containers.run(
            image=image,
            detach=detach,
            network=network,
            environment=environment,
            name=name,
            labels=labels,
            mem_limit=mem_limit,
            cpu_period=cpu_period,
            cpu_quota=cpu_quota
        )
    )

def start_container_experiment(container_list, docker_api, container_config):
    container_list.append(
        docker_api.containers.run(
            image=container_config['image'],
            detach=container_config['detach'],
            network=container_config['network'],
            environment=container_config['environment'],
            name=container_config['name'],
            labels=container_config['labels'],
            mem_limit=container_config['mem_limit'],
            cpu_period=container_config['cpu_period'],
            cpu_quota=container_config['cpu_quota']
        )
    )


def rebuild_experiment_container(sqs_client, queue_url_request, queue_url_response):
    # --> 1. Send rebuild message
    sqs_client.send_message(
        QueueUrl=queue_url_request,
        MessageBody='boto3',
        MessageAttributes={
            'msgType': {
                'StringValue': 'build_experiment',
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': str(-1),
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': str(-1),
                'DataType': 'String'
            }
        })

    # --> 2. Wait for success message in response queue
    for counter in range(5):
        response = sqs_client.receive_message(QueueUrl=queue_url_response, MaxNumberOfMessages=1, WaitTimeSeconds=5)
        if "Messages" in response:
            for message in response["Messages"]:
                sqs_client.delete_message(QueueUrl=queue_url_response, ReceiptHandle=message["ReceiptHandle"])
                break
            return True
    return False



class DockerClient:

    def __init__(self, user_info, fast=True, container_type='eval'):
        self.container_type = container_type
        self.fast = fast
        self.user_info = user_info
        self.client = docker.from_env()
        self.containers = []
        self.private_queue_urls_request = []
        self.private_queue_urls_response = []
        self.labels = {
            'USER_ID': str(self.user_info.user.id),
            'TYPE': str(self.container_type)
        }
        self.label_key_1 = 'USER_ID=' + str(self.user_info.user.id)
        self.label_key_2 = 'TYPE=' + str(self.container_type)

        # --> Gather Containers
        self.gather_containers()

    def gather_containers(self):
        container_query = self.client.containers.list(
            filters={
                'label': [self.label_key_1, self.label_key_2]
            }
        )
        for container in container_query:
            if container not in self.containers:
                self.containers.append(container)
        print('--> GATHERED CONTAINERS:', len(self.containers))

    def start_ga_container(self):
        print('--> REQUERST GA CONTAINER')
        if len(self.containers) > 0:
            print('--> GA CONTAINER ALREADY EXISTS:', len(self.containers))
            return False

        name = 'user-' + str(self.user_info.user.id) + '-ga-container'
        self.containers.append(
            self.client.containers.run(
                image=ga_config['image'],
                detach=ga_config['detach'],
                network=ga_config['network'],
                environment=ga_config['environment'],
                name=name,
                labels=self.labels
            )
        )
        return True

    def create_or_purge_queue(self, queue_name):
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

    def rebuild_experiment_containers(self):
        sqs_client = get_boto3_client('sqs')
        rebuild_threads = []
        for idx, queue_url_request in enumerate(self.private_queue_urls_request):
            queue_url_response = self.private_queue_urls_response[idx]
            th = threading.Thread(
                target=rebuild_experiment_container,
                args=(sqs_client, queue_url_request, queue_url_response)
            )
            th.start()
            rebuild_threads.append(th)
        for th in rebuild_threads:
            th.join()
        print('--> CONTAINERS REBUILT')

    def start_containers_experiment(self, num, vassar_request_url, vassar_response_url):
        print('--> STARTING CONTAINERS FOR EXPERIMENT:', num)

        # --> 1. Create private queues for containers
        for x in range(num):
            queue_name_request = 'user-'+str(self.user_info.user.id)+'-container-priv-queue-request-' + str(x)
            queue_name_response = 'container-priv-queue-response-' + str(x)
            queue_url_request = self.create_or_purge_queue(queue_name_request)
            queue_url_response = self.create_or_purge_queue(queue_name_response)
            if queue_url_request and queue_url_response:
                self.private_queue_urls_request.append(queue_url_request)
                self.private_queue_urls_response.append(queue_url_response)
            else:
                print('--> ERROR LOOKING FOR QUEUES')
                exit(0)

        # --> 2. Create containers and pass private queues
        start_threads = []
        for x in range(num):
            experiment_config = {
                'network': 'daphne_service',
                'detach': True,
                'labels': self.labels,
                'name': str('user-' + str(self.user_info.user.id) + '-container-' + str(x)),
                'image': 'apazagab/vassar:experiment2',
                'environment': {
                    'AWS_ACCESS_KEY_ID': '',
                    'AWS_SECRET_ACCESS_KEY': '',
                    'REGION': 'elasticmq',
                    'REQUEST_MODE': 'CRISP-ATTRIBUTES',
                    'VASSAR_REQUEST_URL': vassar_request_url,
                    'VASSAR_RESPONSE_URL': vassar_response_url,
                    'DEPLOYMENT_TYPE': 'local',
                    'JAVA_OPTS': '-"Dcom.sun.management.jmxremote.rmi.port=10000 -Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10000 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.local.only=false -Djava.rmi.server.hostname=localhost"',
                    'AWS_STACK_ENDPOINT': 'http://172.12.0.5:9324',
                    'APOLLO_URL': 'http://172.12.0.13:8080/v1/graphql',
                    'APOLLO_URL_WS': 'ws://172.12.0.13:8080/v1/graphql',
                    'REQUEST_KEY': 'NONE',
                    'MAXEVAL': 5,
                    'PRIVATE_QUEUE_REQUEST': self.private_queue_urls_request[x],
                    'PRIVATE_QUEUE_RESPONSE': self.private_queue_urls_response[x]
                },
                'mem_limit': '2g',
                'cpu_period': 100000,
                'cpu_quota': 100000,
            }
            th = threading.Thread(
                target=start_container_experiment,
                args=(self.containers, self.client, experiment_config)
            )
            th.start()
            start_threads.append(th)

        # --> 3. Join start threads
        for thread in start_threads:
            thread.join()

    def start_containers(self, num, vassar_request_url, vassar_response_url, msg_batch_size=1):
        print('--> REQUESTED', num, 'CONTAINERS')
        print('--> CURRENT CONTAINERS', len(self.containers))


        # Place request key in evironment
        env = copy.deepcopy(config['environment'])
        env['VASSAR_REQUEST_URL'] = vassar_request_url
        env['VASSAR_RESPONSE_URL'] = vassar_response_url
        env['MAXEVAL'] = msg_batch_size


        img = "apazagab/vassar:experiment"

        use_threading = True


        # Start containers
        start_threads = []
        for x in range(len(self.containers), num):
            name = 'user-' + str(self.user_info.user.id) + '-container-' + str(x)

            if use_threading:
                th = threading.Thread(
                    target=start_container,
                    args=(self.containers, self.client, img, config['detach'], config['network'], env, name, self.labels, config['mem_limit'], config['cpu_period'], config['cpu_quota'])
                )
                th.start()
                start_threads.append(th)
            else:
                name = 'user-' + str(self.user_info.user.id) + '-container-' + str(len(self.containers))
                container = self.client.containers.run(
                    image=img,
                    detach=config['detach'],
                    network=config['network'],
                    environment=env,
                    name=name,
                    labels=self.labels,
                    mem_limit=config['mem_limit'],
                    cpu_period=config['cpu_period'],
                    cpu_quota=config['cpu_quota']
                )
                self.containers.append(container)

        for thread in start_threads:
            thread.join()

    def stop_containers(self):
        print('--> STOPPING CONTAINERS')
        threads = []
        for container in self.containers:
            th = threading.Thread(target=container.stop)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        self.client.containers.prune()

