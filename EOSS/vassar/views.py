import logging
import os
import re
from EOSS.vassar.api import VASSARClient

from rest_framework.views import APIView
from rest_framework.response import Response

from auth_API.helpers import get_or_create_user_information, get_user_information


# Get an instance of a logger
logger = logging.getLogger('EOSS.settings')


class Connect(APIView):
    def post(self, request, format=None):
        vassar_client = VASSARClient()
        user_info = get_user_information(request['session'], self.scope['user'])
        queue_url = os.environ["EVAL_QUEUE_URL"]

        # TODO: Extend to GA
        # TODO: Remove stale queues from SQS + downsize ECS if needed
        # TODO: Add new instances to ECS in connect_to_services if no services available in 10 seconds
        # TODO: Move this to Websockets so server is not blocked for a long time on a single request

        # 1. Send connectionRequest to eval queue
        vassar_client.send_connect_message(queue_url, user_info.user.id)

        # 2. Wait for an answer to the connectionRequest and connect to responsive containers
        user_queue_url = vassar_client.connect_to_services(queue_url)

        # 3. Build the current problem on the container
        vassar_client.send_initialize_message(user_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)
        vassar_client.receive_successful_build(user_queue_url)
        return Response({
            "status": "VASSAR Connection successful!"
        })
