import logging
import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.aws.utils import get_boto3_client

from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design

# Get an instance of a logger
logger = logging.getLogger('EOSS.explorer')

class CheckGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # Start connection with VASSAR
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port, user_info=user_info)
                client.start_connection()

                status = client.is_ga_running(user_info.eosscontext.ga_id)

                # End the connection before return statement
                client.end_connection()

                return Response({
                    'ga_status': status
                })

            except Exception as exc:
                logger.exception('Exception while checking GA status!')
                client.end_connection()
                return Response({
                    "error": "Error checking the GA status",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })
