import logging
import os
import re

from EOSS.vassar.api import VASSARClient

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from auth_API.helpers import get_or_create_user_information, get_user_information


# Get an instance of a logger
logger = logging.getLogger('EOSS.settings')


class Connect(APIView):
    def post(self, request: Request, format=None):
        user_info = get_user_information(request.session, request.user)
        vassar_client = VASSARClient(user_info)

        # TODO: Handle errors better
        # TODO: Move this to Websockets so server is not blocked for a long time on a single request
        
        # Obtain queue urls from environment and ensure they exist
        request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        response_queue_url = os.environ["VASSAR_RESPONSE_URL"]
        ga_request_queue_url = os.environ["GA_REQUEST_URL"]
        ga_response_queue_url = os.environ["GA_RESPONSE_URL"]
        dead_letter_url, dead_letter_arn = vassar_client.create_dead_queue("dead-letter")
        vassar_client.create_queue(request_queue_url.split("/")[-1], dead_letter_arn)
        vassar_client.create_queue(response_queue_url.split("/")[-1], dead_letter_arn)
        vassar_client.create_queue(ga_request_queue_url.split("/")[-1], dead_letter_arn)
        vassar_client.create_queue(ga_response_queue_url.split("/")[-1], dead_letter_arn)

        # Check if there is an existing VASSAR connection
        if user_info.eosscontext.vassar_request_queue_url is not None and vassar_client.queue_exists(user_info.eosscontext.vassar_request_queue_url):
            vassar_status = vassar_client.check_status(user_info.eosscontext.vassar_request_queue_url, user_info.eosscontext.vassar_response_queue_url)
        else:
            vassar_status = "waiting_for_user"
        print("Initial VASSAR status", vassar_status)

        if vassar_status == "waiting_for_user":
            # Uninitialize VASSAR until reconnection is successful
            user_info.eosscontext.vassar_information = {}
            user_info.eosscontext.save()

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            vassar_client.send_connect_message(request_queue_url)

            vassar_status = "waiting_for_ack"

        if vassar_status == "waiting_for_ack":
            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            user_request_queue_url, user_response_queue_url = vassar_client.connect_to_vassar(request_queue_url, response_queue_url)
            print(user_request_queue_url, user_response_queue_url)

            vassar_status = "uninitialized"

        if vassar_status == "uninitialized":
            # 3. Build the current problem on the container
            print("----> Initializing services")
            vassar_client.send_initialize_message(user_request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)
            vassar_client.receive_successful_build(user_response_queue_url)
            vassar_status = "ready"

        print("Final VASSAR status", vassar_status)
        
        # Check if there is an existing GA connection
        if user_info.eosscontext.ga_request_queue_url is not None and vassar_client.queue_exists(user_info.eosscontext.ga_request_queue_url):
            ga_status = vassar_client.check_status(user_info.eosscontext.ga_request_queue_url, user_info.eosscontext.ga_response_queue_url)
        else:
            ga_status = "waiting_for_user"
        print("Initial GA status", ga_status)

        if ga_status == "waiting_for_user":
            # Uninitialize GA until reconnection is successful
            user_info.eosscontext.ga_information = {}
            user_info.eosscontext.save()

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            vassar_client.send_connect_message(ga_request_queue_url)

            ga_status = "waiting_for_ack"

        if ga_status == "waiting_for_ack":
            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            user_ga_request_queue_url, user_ga_response_queue_url = vassar_client.connect_to_ga(ga_request_queue_url, ga_response_queue_url, user_request_queue_url)
            print(user_ga_request_queue_url, user_ga_response_queue_url)

            ga_status = "ready"
        print("Initial GA status", ga_status)

        if vassar_status == "ready" and ga_status == "ready":
            return Response({
                "status": "VASSAR & GA Connection successful!",
                "vassar_status": vassar_status,
                "ga_status": ga_status
            })
        elif vassar_status == "ready":
            return Response({
                "status": "VASSAR Connection successful! GA not so much...",
                "vassar_status": vassar_status,
                "ga_status": ga_status
            })
        elif ga_status == "ready":
            return Response({
                "status": "GA Connection successful! VASSAR not so much...",
                "vassar_status": vassar_status,
                "ga_status": ga_status
            })
        else:
            return Response({
                "status": "No connection was successful...",
                "vassar_status": vassar_status,
                "ga_status": ga_status
            })