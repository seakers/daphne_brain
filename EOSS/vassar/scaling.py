import os
import threading
import time
import asyncio

from EOSS.docker.api import DockerClient
from EOSS.vassar.api import VASSARClient
from EOSS.graphql.api import GraphqlClient

from asgiref.sync import async_to_sync


# Keep the user-id but create a new dataset for evaluation


def acknowledge_vassar(user_info, request_queue_url, response_queue_url):
    print('--> VASSAR HANDSHAKE STARTED')
    temp_client = VASSARClient(user_info)
    async_to_sync(temp_client.send_connect_message)(request_queue_url)
    user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_ack_success = async_to_sync(temp_client.connect_to_vassar)(request_queue_url, response_queue_url, 3)
    async_to_sync(temp_client.send_initialize_message)(user_request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id, vassar_container_uuid)
    build_success = async_to_sync(temp_client.receive_successful_build)(user_response_queue_url, vassar_container_uuid, 3)
    print('--> VASSAR BUILD ATTEMPT:', build_success)
    return 0



class EvaluationScaling:

    def __init__(self, user_info, num_instances):
        self.user_info = user_info
        self.num_instances = num_instances

        # --> URLs
        self.request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        self.response_queue_url = os.environ["VASSAR_RESPONSE_URL"]

        # --> CLIENTS
        self.docker_client = DockerClient()
        self.vassar_client = VASSARClient(user_info)
        self.graphql_client = GraphqlClient(user_info)

    def init_queues(self):
        if not self.vassar_client.queue_exists_by_name("dead-letter"):
            dead_letter_url, dead_letter_arn = self.vassar_client.create_dead_queue("dead-letter")
        else:
            dead_letter_url = self.vassar_client.get_queue_url("dead-letter")
            dead_letter_arn = self.vassar_client.get_queue_arn(dead_letter_url)
        if not self.vassar_client.queue_exists(self.response_queue_url):
            self.vassar_client.create_queue(self.response_queue_url.split("/")[-1], dead_letter_arn)
        if not self.vassar_client.queue_exists(self.request_queue_url):
            self.vassar_client.create_queue(self.request_queue_url.split("/")[-1], dead_letter_arn)

    # def acknowledge_vassar(self):
    #     temp_client = VASSARClient(self.user_info)
    #     user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_ack_success = async_to_sync(temp_client.connect_to_vassar(self.request_queue_url, self.response_queue_url, 3))
    #     async_to_sync(temp_client.send_initialize_message(user_request_queue_url, self.user_info.eosscontext.group_id, self.user_info.eosscontext.problem_id, vassar_container_uuid))
    #     build_success = async_to_sync(temp_client.receive_successful_build(user_response_queue_url, vassar_container_uuid, 3))
    #     print('--> VASSAR BUILD ATTEMPT:', build_success)
    #     return 0

    def initialize(self, block=True):
        print('--> INITIALIZING SCALING')
        time.sleep(3)


        # 1. Ensure appropriate queues exist
        self.init_queues()

        # 2. Start docker containers
        self.docker_client.start_containers(self.num_instances)

        # 3. Send a connection request for each of the containers
        for x in range(0, self.num_instances):
            async_to_sync(self.vassar_client.send_connect_message(self.request_queue_url))

        # 4. For each of the requested instances, initialize
        build_threads = []
        for x in range(0, self.num_instances):
            th = threading.Thread(target=acknowledge_vassar, args=(self.user_info, self.request_queue_url, self.response_queue_url))
            th.start()
            build_threads.append(th)

        # 5. Wait for threads to finish if blocking
        if block:
            for th in build_threads:
                th.join()



