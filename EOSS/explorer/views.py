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


class StartGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

                # Check for read-only datasets before starting
                client = VASSARClient(user_information=user_info)
                if client.check_dataset_read_only():
                    return Response({
                        "error": "Dataset is read only"
                    })

                # Stop GA in container if it was runnning
                async_to_sync(client.stop_ga)()
                # Start GA in container
                async_to_sync(client.start_ga)()

                # Start listening for AWS SQS inputs
                def aws_consumer():
                    thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                    ga_response_queue_url = thread_user_info.eosscontext.ga_response_queue_url
                    print("--> GA Thread: Queue URL is", ga_response_queue_url)
                    sqs_client = get_boto3_client('sqs')
                    is_done = False
                    channel_layer = get_channel_layer()
        

                    while not is_done:
                        response = sqs_client.receive_message(QueueUrl=ga_response_queue_url, MaxNumberOfMessages=3, WaitTimeSeconds=5, MessageAttributeNames=["All"])
                        if "Messages" in response:
                            # Send message back to frontend that GA is working fine
                            async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                                {
                                                                    'type': 'services.ga_status',
                                                                    'status': 'ready'
                                                                })
                            for message in response["Messages"]:
                                if message["MessageAttributes"]["msgType"]["StringValue"] == "gaStarted":
                                    #TODO: Add a new field to eosscontext on GA thread status
                                    print("--> GA Thread: GA Started!")
                                    sqs_client.delete_message(QueueUrl=ga_response_queue_url, ReceiptHandle=message["ReceiptHandle"])
                                elif message["MessageAttributes"]["msgType"]["StringValue"] == "gaEnded":
                                    #TODO: Add a new field to eosscontext on GA thread status
                                    sqs_client.delete_message(QueueUrl=ga_response_queue_url, ReceiptHandle=message["ReceiptHandle"])
                                    is_done = True
                                    print('--> GA Thread: Ending the thread!')
                                elif message["MessageAttributes"]["msgType"]["StringValue"] == "newGaArch":
                                    print('--> GA Thread: Processing a new arch!')
                                    # Keeping up for proactive
                                    add_design(request.session, request.user)
                                    sqs_client.delete_message(QueueUrl=ga_response_queue_url, ReceiptHandle=message["ReceiptHandle"])
                                else:
                                    # Return message to queue
                                    sqs_client.change_message_visibility(QueueUrl=ga_response_queue_url, ReceiptHandle=message["ReceiptHandle"], VisibilityTimeout=1)

                    print('--> GA Thread: Thread done!')

                thread = threading.Thread(target=aws_consumer)
                thread.start()

                return Response({
                    "status": 'GA started correctly!'
                })

            except Exception as exc:
                logger.exception('Exception in starting the GA!')
                return Response({
                    "error": "Error starting the GA",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })


class StopGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

                # Start connection with VASSAR
                client = VASSARClient(user_information=user_info)

                # Call the GA stop function on Engineer
                async_to_sync(client.stop_ga)()

                return Response({
                    "status": 'GA stopped correctly!'
                })

            except Exception as exc:
                logger.exception('Exception in stopping the GA!')
                return Response({
                    "error": "Error stopping the GA",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })


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
