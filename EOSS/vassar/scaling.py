import os
import threading
import time
import asyncio

from EOSS.docker.api import DockerClient
from EOSS.vassar.api import VASSARClient
from EOSS.graphql.api import GraphqlClient

from asgiref.sync import async_to_sync


# Keep the user-id but create a new dataset for evaluation


def connection_thread(user_info, request_queue_url, response_queue_url):
    print('--> VASSAR HANDSHAKE STARTED')
    temp_client = VASSARClient(user_info)
    async_to_sync(temp_client.send_connect_message)(request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)
    user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_connection_success = async_to_sync(temp_client.connect_to_vassar)(request_queue_url, response_queue_url, 3)
    print('--> VASSAR BUILD SUCCESS:', vassar_connection_success)




class EvaluationScaling:

    def __init__(self, user_info, num_instances, user_req=False, fast=True):
        self.user_req = user_req
        self.user_info = user_info
        self.num_instances = num_instances

        # --> URLs
        self.request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        self.response_queue_url = os.environ["VASSAR_RESPONSE_URL"]
        self.request_queue_url_2 = os.environ["VASSAR_REQUEST_URL_2"]
        self.response_queue_url_2 = os.environ["VASSAR_RESPONSE_URL_2"]

        # --> CLIENTS
        self.docker_client = DockerClient(self.user_info, fast=fast)
        self.vassar_client = VASSARClient(user_info)
        self.graphql_client = GraphqlClient(user_info)

    def shutdown(self):
        self.docker_client.stop_containers()

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
        if not self.vassar_client.queue_exists(self.request_queue_url_2):
            self.vassar_client.create_queue(self.request_queue_url_2.split("/")[-1], dead_letter_arn)
        if not self.vassar_client.queue_exists(self.response_queue_url_2):
            self.vassar_client.create_queue(self.response_queue_url_2.split("/")[-1], dead_letter_arn)

    def initialize(self, block=True):
        print('--> INITIALIZING SCALING')
        containers_to_start = self.num_instances - len(self.docker_client.containers)
        if containers_to_start < 0:
            containers_to_start = 0

        # 1. Ensure appropriate queues exist
        self.init_queues()

        # 2. Start docker containers
        if self.user_req:
            self.docker_client.start_containers(self.num_instances, self.request_queue_url, self.response_queue_url)
        else:
            self.docker_client.start_containers(self.num_instances, self.request_queue_url_2, self.response_queue_url_2)

        # 3. Initialize each of the containers
        build_threads = []
        for x in range(0, containers_to_start):
            if self.user_req:
                th = threading.Thread(target=connection_thread, args=(self.user_info, self.request_queue_url, self.response_queue_url))
            else:
                th = threading.Thread(target=connection_thread, args=(self.user_info, self.request_queue_url_2, self.response_queue_url_2))
            th.start()
            build_threads.append(th)

        # 5. Wait for threads to finish if blocking
        if block:
            for th in build_threads:
                th.join()

        print('--> SCALING INITIALIZATION COMPLETE')

    def bit_list_2_bool_list(self, bit_list):
        bool_list = []
        for bit in bit_list:
            if bit == 0:
                bool_list.append(False)
            else:
                bool_list.append(True)
        return bool_list

    def bit_list_2_bit_str(self, bit_list):
        input_str = ''
        for bit in bit_list:
            if bit == 1:
                input_str += '1'
            else:
                input_str += '0'
        return input_str

    # Takes 2D array of bits
    def evaluate_batch(self, batch):
        print('--> EVALUATING BATCH')
        requested_evals = []
        for idx, arch in enumerate(batch):
            inputs = self.bit_list_2_bool_list(arch)
            requested_evals.append(self.bit_list_2_bit_str(arch))
            self.vassar_client.evaluate_architecture_ai4se(inputs, eval_queue_url=self.user_info.eosscontext.vassar_request_queue_url, block=False)

        return requested_evals


