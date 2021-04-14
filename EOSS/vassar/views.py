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
        
        request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        response_queue_url = os.environ["VASSAR_RESPONSE_URL"]

        # Check if there is an existing VASSAR connection
        if user_info.eosscontext.vassar_request_queue_url is not None:
            current_status = vassar_client.check_status()
        else:
            current_status = "waiting_for_user"
        
        if current_status != "ready":
            # Uninitialize VASSAR until reconnection is successful
            user_info.eosscontext.vassar_ready = False
            user_info.eosscontext.save()

            # TODO: Extend to GA
            # TODO: Remove stale queues from SQS + downsize ECS if needed
            # TODO: Add new instances to ECS in connect_to_services if no services available in 10 seconds
            # TODO: Move this to Websockets so server is not blocked for a long time on a single request

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            vassar_client.send_connect_message(request_queue_url)

            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            user_request_queue_url, user_response_queue_url = vassar_client.connect_to_services(request_queue_url, response_queue_url)
            print(user_request_queue_url, user_response_queue_url)

            # 3. Build the current problem on the container
            print("----> Initializing services")
            vassar_client.send_initialize_message(user_request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)
            vassar_client.receive_successful_build(user_response_queue_url)
            return Response({
                "status": "VASSAR Connection successful!"
            })
        else:
            return Response({
                "status": "VASSAR was already connected!"
            })
