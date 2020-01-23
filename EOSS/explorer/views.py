import logging
import threading

from rest_framework.views import APIView
from rest_framework.response import Response
import json
import pika
import time

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.models import Design
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture
from auth_API.helpers import get_or_create_user_information
from EOSS.explorer.helpers import send_archs_from_queue_to_main_dataset, send_archs_back, \
    generate_background_search_message
from EOSS.data.design_helpers import add_design

# Get an instance of a logger
logger = logging.getLogger('EOSS.explorer')


class StartGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # Start connection with VASSAR
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port)
                client.start_connection()

                problem = request.data['problem']

                # Restart archs queue before starting the GA again
                Design.objects.filter(activecontext__exact=user_info.eosscontext.activecontext).delete()
                user_info.eosscontext.last_arch_id = user_info.eosscontext.design_set.count()
                user_info.eosscontext.save()

                # Convert the architecture list and wait for threads to be available (ask for stop again just in case)
                thrift_list = []
                inputs_unique_set = set()

                if problem in assignation_problems:
                    for arch in user_info.eosscontext.design_set.all():
                        thrift_list.append(
                            BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                        hashed_input = hash(tuple(json.loads(arch.inputs)))
                        inputs_unique_set.add(hashed_input)
                elif problem in partition_problems:
                    for arch in user_info.eosscontext.design_set.all():
                        thrift_list.append(
                            DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                        hashed_input = hash(tuple(json.loads(arch.inputs)))
                        inputs_unique_set.add(hashed_input)
                else:
                    raise ValueError('Unrecognized problem type: {0}'.format(problem))

                if user_info.eosscontext.ga_id is not None:
                    client.stop_ga(user_info.eosscontext.ga_id)
                ga_id = client.start_ga(problem, request.user.username, thrift_list)
                user_info.eosscontext.ga_id = ga_id
                user_info.eosscontext.save()

                # End the connection before return statement
                client.end_connection()

                # Start listening for redis inputs to share through websockets
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                channel = connection.channel()

                channel.queue_declare(queue=ga_id + '_gabrain')

                def callback(ch, method, properties, body):
                    thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                    message = json.loads(body)
                    if message['type'] == 'new_arch':
                        print('Processing some new archs!')
                        nonlocal inputs_unique_set
                        # Archs are added one by one
                        new_archs = [message['data']]
                        send_back = []
                        # Add archs to the context data before sending back to user
                        for arch in new_archs:
                            hashed_input = hash(tuple(arch['inputs']))
                            if hashed_input not in inputs_unique_set:
                                full_arch = {
                                    'inputs': arch['inputs'],
                                    'outputs': arch['outputs']
                                }
                                if thread_user_info.eosscontext.activecontext.show_background_search_feedback:
                                    full_arch = add_design(full_arch, request.session, request.user, False)
                                else:
                                    full_arch = add_design(full_arch, request.session, request.user, True)
                                send_back.append(full_arch)
                                inputs_unique_set.add(hashed_input)
                                thread_user_info.save()

                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()

                        background_queue_qs = Design.objects.filter(
                            activecontext_id__exact=thread_user_info.eosscontext.activecontext.id)
                        if background_queue_qs.count() == 10:
                            ws_message = generate_background_search_message(thread_user_info)
                            async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                              {
                                                                  'type': 'active.message',
                                                                  'message': ws_message
                                                              })
                        if thread_user_info.eosscontext.activecontext.show_background_search_feedback:
                            back_list = send_archs_from_queue_to_main_dataset(thread_user_info)
                            send_back.extend(back_list)
                            send_archs_back(channel_layer, thread_user_info.channel_name, send_back)
                    if message['type'] == 'ga_started':
                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                          {
                                                              'type': 'ga.started'
                                                          })
                    if message['type'] == 'ga_done':
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                          {
                                                              'type': 'ga.finished'
                                                          })
                        print('Ending the thread!')
                        channel.stop_consuming()

                channel.basic_consume(queue=ga_id + '_gabrain',
                                      on_message_callback=callback,
                                      auto_ack=True)

                thread = threading.Thread(target=channel.start_consuming)
                thread.start()

                return Response({
                    "status": 'GA started correctly!'
                })

            except Exception as exc:
                logger.exception('Exception in starting the GA!')
                client.end_connection()
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
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port)
                client.start_connection()

                # Call the GA stop function on Engineer
                client.stop_ga(user_info.eosscontext.ga_id)
                user_info.eosscontext.ga_id = None
                user_info.eosscontext.save()

                # End the connection before return statement
                client.end_connection()

                return Response({
                    "status": 'GA stopped correctly!'
                })

            except Exception as exc:
                logger.exception('Exception in stopping the GA!')
                client.end_connection()
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
                client = VASSARClient(port)
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
