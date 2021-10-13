import docker
import threading
import random

config = {
    'image': 'vassar:experiment',
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
        'AWS_STACK_ENDPOINT': 'http://172.18.0.2:9324',
        'APOLLO_URL': 'http://172.18.0.13:8080/v1/graphql',
        'APOLLO_URL_WS': 'ws://172.18.0.13:8080/v1/graphql'
    },
    'entrypoint': 'gradle run'
}


class DockerClient:

    def __del__(self):
        self.stop_containers()

    def __init__(self):
        self.client = docker.from_env()
        self.identifier = str(random.randint(10000, 99999))
        self.containers = {}

    def start_containers(self, num):
        print('--> STARTING', num, 'CONTAINERS')
        for x in range(0, num):
            name = 'sensitivity-' + str(x) + '-' + self.identifier
            container = self.client.containers.run(
                image=config['image'],
                detach=config['detach'],
                network=config['network'],
                environment=config['environment'],
                name=name
            )
            self.containers[name] = container

    def stop_containers(self):
        print('--> STOPPING CONTAINERS')
        for name in self.containers:
            th = threading.Thread(target=self.containers[name].stop)
            th.start()
