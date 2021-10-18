import docker
import threading
import random
import copy

config = {
    'network': 'daphne_default',
    'detach': True,
    'environment': {
        'AWS_ACCESS_KEY_ID': 'AKIAJVM34C5MCCWRJCCQ',
        'AWS_SECRET_ACCESS_KEY': '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',
        'REGION': 'elasticmq',
        'REQUEST_MODE': 'CRISP-ATTRIBUTES',
        'VASSAR_REQUEST_URL': 'http://localhost:9324/000000000000/vassar_request',
        'VASSAR_RESPONSE_URL': 'http://localhost:9324/000000000000/vassar_response',
        'DEPLOYMENT_TYPE': 'local',
        'JAVA_OPTS': '-"Dcom.sun.management.jmxremote.rmi.port=10000 -Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10000 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.local.only=false -Djava.rmi.server.hostname=localhost"',
        'AWS_STACK_ENDPOINT': 'http://172.18.0.6:9324',
        'APOLLO_URL': 'http://172.18.0.14:8080/v1/graphql',
        'APOLLO_URL_WS': 'ws://172.18.0.14:8080/v1/graphql',
        'REQUEST_KEY': 'NONE'
    },
    # 'entrypoint': 'gradle run'
}


class DockerClient:

    def __init__(self, user_info, fast=True):
        self.fast = fast
        self.user_info = user_info
        self.client = docker.from_env()
        self.containers = []
        self.labels = {
            'USER_ID': str(self.user_info.user.id)
        }
        self.label_key = 'USER_ID=' + str(self.user_info.user.id)

        # --> Gather Containers
        self.gather_containers()

    def gather_containers(self):
        container_query = self.client.containers.list(
            filters={
                'label': [self.label_key]
            }
        )
        for container in container_query:
            if container not in self.containers:
                self.containers.append(container)
        print('--> GATHERED CONTAINERS:', len(self.containers))


    def start_containers(self, num):
        print('--> STARTING', num, 'CONTAINERS')

        # Place request key in evironment
        env = copy.deepcopy(config['environment'])

        img = "vassar:experiment"
        if self.fast:
            img = "vassar:experiment_fast"


        # Start containers
        for x in range(0, num):
            name = 'user-' + str(self.user_info.user.id) + '-container-' + str(len(self.containers))
            container = self.client.containers.run(
                image=img,
                detach=config['detach'],
                network=config['network'],
                environment=env,
                name=name,
                labels=self.labels
            )
            self.containers.append(container)

    def stop_containers(self):
        print('--> STOPPING CONTAINERS')
        threads = []
        for container in self.containers:
            th = threading.Thread(target=container.stop)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        th = threading.Thread(target=self.client.containers.prune)
        th.start()

