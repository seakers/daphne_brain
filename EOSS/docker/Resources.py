import docker
import threading
from EOSS.docker.clients.GaContainerClient import GaContainerClient
from EOSS.docker.clients.VassarContainerClient import VassarContainerClient


class Resources:
    def __init__(self, user_info):
        self.user_info = user_info
        self.docker_client = docker.from_env()

        # --> 1. Set vassar request url based on: is_agent
        self.eval_request_queue = self.user_info.eval_request_queue
        self.eval_response_queue = self.user_info.eval_request_queue

        # --> 2. Gather the currently running containers
        self.vassar_containers = []
        self.ga_containers = []
        self.gather_resources()

        # --> 3. Determine if threads will be joined
        self.join_threads = False

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

    """
      _____                  _       _         _____                                         
     |  __ \                | |     | |       |  __ \                                        
     | |__) |___  __ _ _   _| | __ _| |_ ___  | |__) |___  ___  ___  _   _ _ __ ___ ___  ___ 
     |  _  // _ \/ _` | | | | |/ _` | __/ _ \ |  _  // _ \/ __|/ _ \| | | | '__/ __/ _ \/ __|
     | | \ \  __/ (_| | |_| | | (_| | ||  __/ | | \ \  __/\__ \ (_) | |_| | | | (_|  __/\__ \
     |_|  \_\___|\__, |\__,_|_|\__,_|\__\___| |_|  \_\___||___/\___/ \__,_|_|  \___\___||___/
                  __/ |                                                                      
                 |___/ 
    """

    def regulate_resources(self, eval_container_count, ga_container_count):
        regulate_threads = []

        # --> 1. Regulate vassar containers
        if eval_container_count != -1:
            if len(self.vassar_containers) < eval_container_count:
                for idx in range(len(self.vassar_containers), eval_container_count):
                    th = threading.Thread(target=self.add_vassar_container, args=(None,))
                    th.start()
                    regulate_threads.append(th)
            elif len(self.vassar_containers) > eval_container_count:
                popped_containers = []
                for idx in range(eval_container_count, len(self.vassar_containers)):
                    popped_containers.append(self.vassar_containers.pop())
                th = threading.Thread(target=self.remove_containers, args=(popped_containers,))
                th.start()
                regulate_threads.append(th)

        # --> 2. Regulate ga containers
        if ga_container_count != -1:
            if len(self.ga_containers) < ga_container_count:
                for idx in range(len(self.ga_containers), ga_container_count):
                    th = threading.Thread(target=self.add_ga_container, args=(None,))
                    th.start()
                    regulate_threads.append(th)
            elif len(self.ga_containers) > ga_container_count:
                popped_containers = []
                for idx in range(ga_container_count, len(self.ga_containers)):
                    popped_containers.append(self.ga_containers.pop())
                th = threading.Thread(target=self.remove_containers, args=(popped_containers,))
                th.start()
                regulate_threads.append(th)

        # --> 3. Join regulate threads
        if self.join_threads:
            for th in regulate_threads:
                th.join()

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
        if self.join_threads:
            for th in remove_threads:
                th.join()

    """
      _____ _             
     |  __ (_)            
     | |__) | _ __   __ _ 
     |  ___/ | '_ \ / _` |
     | |   | | | | | (_| |
     |_|   |_|_| |_|\__, |
                     __/ |
                    |___/ 
    """

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

    def ping_resource(self, response_list, container):
        response_list.append(container.ping())

    """
       _____              
      / ____|   /\        
     | |  __   /  \   ___ 
     | | |_ | / /\ \ / __|
     | |__| |/ ____ \\__ \
      \_____/_/    \_\___/
    """

    def start_GAs(self, identifiers, objectives):
        start_threads = []
        for identifier in identifiers:
            resource = self.get_resource(identifier)
            th = threading.Thread(target=resource.start_algorithm, args=(objectives,))
            th.start()
            start_threads.append(th)
        for th in start_threads:
            th.join()

    def stop_GAs(self, identifiers):
        stop_threads = []
        for identifier in identifiers:
            resource = self.get_resource(identifier)
            th = threading.Thread(target=resource.stop_algorithm)
            th.start()
            stop_threads.append(th)
        for th in stop_threads:
            th.join()

    def stop_GAs_all(self):
        stop_threads = []
        for resource in self.ga_containers:
            th = threading.Thread(target=resource.stop_algorithm)
            th.start()
            stop_threads.append(th)
        for th in stop_threads:
            th.join()

    def get_resource(self, identifier):
        for container in self.vassar_containers:
            if container.identifier == identifier:
                return container
        for container in self.ga_containers:
            if container.identifier == identifier:
                return container
        return None

    """
      ____        _ _     _ 
     |  _ \      (_) |   | |
     | |_) |_   _ _| | __| |
     |  _ <| | | | | |/ _` |
     | |_) | |_| | | | (_| |
     |____/ \__,_|_|_|\__,_|                 
    """

    def build_evaluators(self):
        build_threads = []
        for resource in self.vassar_containers:
            th = threading.Thread(target=resource.build, args=())
            th.start()
            build_threads.append(th)
        if self.join_threads:
            for th in build_threads:
                th.join()


