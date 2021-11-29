import os
import docker
import threading
from EOSS.docker.GaContainerClient import GaContainerClient
from EOSS.docker.VassarContainerClient import VassarContainerClient






class Resources:
    def __init__(self, user_info, is_agent, eval_container_count=0, ga_container_count=0):
        self.user_info = user_info
        self.is_agent = is_agent
        self.eval_container_count = eval_container_count
        self.ga_container_count = ga_container_count
        self.docker_client = docker.from_env()

        # --> 1. Set vassar request url based on: is_agent
        self.eval_request_queue = self.user_info.eval_request_queue

        # --> 2. Gather the currently running containers
        self.vassar_containers = []
        self.ga_containers = []
        self.gather_resources()

        # --> 3. Regulate the desired number of resources (if needed)
        self.regulate_resources()

    def add_vassar_container(self, container):
        self.vassar_containers.append(VassarContainerClient(self.user_info, container=container))

    def add_ga_container(self, container):
        self.ga_containers.append(GaContainerClient(self.user_info, container=container))

    def remove_containers(self, containers):
        remove_threads = []
        for container in containers:
            th = threading.Thread(target=container.shutdown)
            th.start()
            remove_threads.append(th)
        for th in remove_threads:
            th.join()

    def gather_resources(self):
        user_id_key = 'USER_ID=' + str(self.user_info.user.id)
        eval_type_key = 'TYPE=eval'
        ga_type_key = 'TYPE=ga'

        # --> 1. Query eval and ga containers
        eval_container_query = self.docker_client.containers.list(filters={'label': [user_id_key, eval_type_key]})
        ga_container_query = self.docker_client.containers.list(filters={'label': [user_id_key, ga_type_key]})

        # --> 2. Link pre-existing vassar / ga containers
        link_threads = []
        for container in eval_container_query:
            th = threading.Thread(target=self.add_vassar_container, args=(container,))
            th.start()
            link_threads.append(th)
        for container in ga_container_query:
            th = threading.Thread(target=self.add_ga_container, args=(container,))
            th.start()
            link_threads.append(th)
        for th in link_threads:
            th.join()

    def regulate_resources(self):
        regulate_threads = []

        # --> 1. Regulate vassar containers
        if len(self.vassar_containers) < self.eval_container_count:
            for idx in range(len(self.vassar_containers), self.eval_container_count):
                th = threading.Thread(target=self.add_vassar_container, args=(None,))
                th.start()
                regulate_threads.append(th)
        elif len(self.vassar_containers) > self.eval_container_count:
            popped_containers = []
            for idx in range(self.eval_container_count, len(self.vassar_containers)):
                popped_containers.append(self.vassar_containers.pop())
            th = threading.Thread(target=self.remove_containers, args=(popped_containers,))
            th.start()
            regulate_threads.append(th)

        # --> 2. Regulate ga containers
        if len(self.ga_containers) < self.ga_container_count:
            for idx in range(len(self.ga_containers), self.ga_container_count):
                th = threading.Thread(target=self.add_ga_container, args=(None,))
                th.start()
                regulate_threads.append(th)
        elif len(self.ga_containers) > self.ga_container_count:
            popped_containers = []
            for idx in range(self.ga_container_count, len(self.ga_containers)):
                popped_containers.append(self.ga_containers.pop())
            th = threading.Thread(target=self.remove_containers, args=(popped_containers,))
            th.start()
            regulate_threads.append(th)

        # --> 3. Join regulate threads
        for th in regulate_threads:
            th.join()

    def ping_resource(self, response_list, container):
        response_list.append(container.ping())

    def ping_resources(self):
        survey = {
            'vassar_containers': [],
            'ga_containers': [],
        }

        ping_threads = []
        for container in self.vassar_containers:
            th = threading.Thread(target=self.ping_resource, args=(survey['vassar_containers'], container))
            th.start()
            ping_threads.append(th)
        for container in self.ga_containers:
            th = threading.Thread(target=self.ping_resource, args=(survey['ga_containers'], container))
            th.start()
            ping_threads.append(th)
        for th in ping_threads:
            th.join()

        return survey









