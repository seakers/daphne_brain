import asyncio
import os
import threading
import json


from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer


from daphne_context.models import UserInformation
from daphne_ws.async_db_methods import _get_user_information, _save_subcontext, _save_user_info
from daphne_ws.consumers import DaphneConsumer

from EOSS.aws.clients.EcsClient import EcsClient
from EOSS.aws.utils import get_boto3_client
from EOSS.aws.service.ServiceManager import ServiceManager
from EOSS.data.design_helpers import add_design
from EOSS.active import live_recommender
from EOSS.vassar.api import VASSARClient
from EOSS.graphql.client.Dataset import DatasetGraphqlClient
from EOSS.teacher.models import ArchitecturesEvaluated, ArchitecturesUpdated, ArchitecturesClicked
from EOSS.vassar.scaling import EvaluationScaling


class EOSSConsumer(DaphneConsumer):
    # WebSocket event handlers
    async def receive_json(self, content, **kwargs):
        print('--> EOSS WS MESSAGE: ', self.scope['user'], self.scope['session'])
        """
            Called when we get a text frame. Channels will JSON-decode the payload
            for us and pass it as the first argument.
        """

        # --> 1. Call parent function
        await super(EOSSConsumer, self).receive_json(content, **kwargs)

        # --> 2. Get user_info
        user_info: UserInformation = await _get_user_information(self.scope['session'], self.scope['user'])
        if user_info is None:
            print('--> NO USER INFO FOUND FOR WS CONNECTION:', self.scope['user'], self.scope['session'])
            return



        """ Message Types                
                
                1.  active_engineer
                2.  active_historian
                3.  active_analyst
                
                
                4.  connect_services / regulate_services
                5.  connect_vassar
                6.  connect_ga
                
                
                7.  start_ga
                8.  apply_feature
                9.  stop_ga
                
                10. rebuild_vassar
                
                11. teacher_clicked_arch
                12. teacher_clicked_arch_update
                13. teacher_evaluated_arch
                
                14. ping
        """
        if content.get('msg_type') == 'active_engineer':
            message = await sync_to_async(live_recommender.generate_engineer_message)(
                user_info,
                content.get('genome'),
                self.scope['session'].session_key)
            if message:
                await self.send_json(
                    {
                        'type': 'active.message',
                        'message': message
                    })
        elif content.get('msg_type') == 'active_historian':
            message = await sync_to_async(live_recommender.generate_historian_message)(
                user_info,
                content.get('genome'),
                self.scope['session'].session_key)
            if message:
                await self.send_json({
                    'type': 'active.message',
                    'message': message
                })
        elif content.get('msg_type') == 'active_analyst':
            message = await sync_to_async(live_recommender.generate_analyst_message)(
                user_info,
                self.scope['session'].session_key)
            if message:
                await self.send_json({
                    'type': 'active.message',
                    'message': message
                })


        elif content.get('msg_type') == 'connect_services':
            if user_info.user is not None:
                await self.connect_services(user_info, content)
        elif content.get('msg_type') == 'start_ga':
            await self.start_ga(user_info)
        elif content.get('msg_type') == 'apply_feature':
            await self.apply_ga_feature(user_info, content.get("featureExpression"))
        elif content.get('msg_type') == 'stop_ga':
            await self.stop_ga(user_info)


        elif content.get('msg_type') == 'rebuild_vassar':
            await self.rebuild_vassar(user_info, content.get('group_id'), content.get('problem_id'), content.get('dataset_id'))


        elif content.get('msg_type') == 'teacher_clicked_arch':
            content = content.get('teacher_context')    # --> Dict
            entry = ArchitecturesClicked(user_information=user_info, arch_clicked=json.dumps(content))
            entry.save()
        elif content.get('msg_type') == 'teacher_clicked_arch_update':
            content = content.get('teacher_context')  # --> List
            entry = ArchitecturesUpdated(user_information=user_info, arch_updated=json.dumps(content))
            entry.save()
        elif content.get('msg_type') == 'teacher_evaluated_arch':
            content = content.get('teacher_context')  # --> Dict
            entry = ArchitecturesEvaluated(user_information=user_info, arch_evaluated=json.dumps(content))
            entry.save()


        elif content.get('msg_type') == 'ping':
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            # Only ping vassar and GA if logged in
            if user_info.user is not None:
                await self.ping_services(user_info, content)

            # if user_info.user is not None:
            #     vassar_client = VASSARClient(user_info)
            #     container_statuses = await vassar_client.send_ping_message()
            #     for uuid, still_alive in container_statuses["vassar"].items():
            #         if still_alive:
            #             status = "ready"
            #         else:
            #             status = "missed_ping"
            #         await self.send_json({
            #             'type': 'services.vassar_status',
            #             'uuid': uuid,
            #             'status': status
            #         })
            #     for uuid, still_alive in container_statuses["ga"].items():
            #         if still_alive:
            #             status = "ready"
            #         else:
            #             status = "missed_ping"
            #         await self.send_json({
            #             'type': 'services.ga_status',
            #             'uuid': uuid,
            #             'status': status
            #         })
        # elif content.get('msg_type') == 'mycroft':
        #     self.send_json({
        #         'type': 'mycroft.message',
        #         'message': 'mycroft test'
        #     })




    #############
    ### Roles ###
    #############

    # --> Out Messages
    async def active_message(self, event):
        print(event)
        await self.send_json(event)
    def teacher_design_space(self, event):
        self.send_json(event)
    def teacher_objective_space(self, event):
        self.send_json(event)
    def teacher_sensitivities(self, event):
        self.send_json(event)
    def teacher_features(self, event):
        self.send_json(event)


    


    ################
    ### Services ###
    ################

    async def ping_services(self, user_info: UserInformation, content):
        print('--> PING SERVICES (PLACEHOLDER)')

    # --> Functions
    async def connect_services(self, user_info: UserInformation, content):
        print('--> CONNECTING SERVICES')

        # --> 1. Set desired number of services
        if 'num_eval' in content:
            user_info.eosscontext.design_evaluator_task_count = int(content.get('num_eval'))
        if 'num_ga' in content:
            user_info.eosscontext.genetic_algorithm_task_count = int(content.get('num_ga'))
        _save_user_info(user_info)

        # --> 2. Regulate services
        # service_manager = ServiceManager(user_info)
        # result = await service_manager.initialize()
        # if result is True:
        #     await service_manager.regulate_services()



    ##############
    ### Vassar ###
    ##############

    # --> Functions
    async def rebuild_vassar(self, user_info: UserInformation, group_id: int, problem_id: int, dataset_id: int):
        print('--> REBUILD VASSAR (PLACEHOLDER)')
        await self.send_json({
            'type': 'services.vassar_rebuild',
            'status': "success"
        })
        return 0

    async def connect_vassar_old(self, user_info: UserInformation, skip_check: bool = False):
        vassar_client = VASSARClient(user_info)

        max_retries_vassar_ack = 5
        max_retries_vassar_build = 5
        vassar_connection_success = False

        # Obtain queue urls from environment and ensure they exist
        request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        response_queue_url = os.environ["VASSAR_RESPONSE_URL"]
        if not await vassar_client.queue_exists_by_name("dead-letter"):
            dead_letter_url, dead_letter_arn = await vassar_client.create_dead_queue("dead-letter")
        else:
            dead_letter_url = await vassar_client.get_queue_url("dead-letter")
            dead_letter_arn = await vassar_client.get_queue_arn(dead_letter_url)
        request_create_task = None
        response_create_task = None
        if not await vassar_client.queue_exists(request_queue_url):
            request_create_task = asyncio.create_task(
                vassar_client.create_queue(request_queue_url.split("/")[-1], dead_letter_arn))
        if not await vassar_client.queue_exists(response_queue_url):
            response_create_task = asyncio.create_task(
                vassar_client.create_queue(response_queue_url.split("/")[-1], dead_letter_arn))
        if request_create_task is not None:
            await request_create_task
        if response_create_task is not None:
            await response_create_task

        # New initialization paradigm starts here
        # - only one connectionRequest message is sent

        # 1. Check to see if there is an existing vassar connection
        if not skip_check:
            if user_info.eosscontext.vassar_request_queue_url is not None and await vassar_client.queue_exists(
                    user_info.eosscontext.vassar_request_queue_url):
                vassar_status, vassar_uuid = await vassar_client.check_status(
                    user_info.eosscontext.vassar_request_queue_url,
                    user_info.eosscontext.vassar_response_queue_url)
            else:
                vassar_status = "waiting_for_user"
                vassar_uuid = None
        else:
            vassar_status = "waiting_for_user"
            vassar_uuid = None

        if vassar_uuid is not None:
            # Save information to database
            await sync_to_async(vassar_client._initialize_vassar)(user_info.eosscontext.vassar_request_queue_url,
                                                                  user_info.eosscontext.vassar_response_queue_url,
                                                                  vassar_uuid)

        await self.send_json({
            'type': 'services.vassar_status',
            'status': vassar_status
        })
        print("Initial VASSAR status", vassar_status)

        # 2. If the design-evaluator instance is not initialized, send initialization request
        user_request_queue_url, user_response_queue_url, vassar_container_uuid = None, None, None
        vassar_connection_success = vassar_status == "ready"
        if vassar_status == "waiting_for_user":
            # Uninitialize VASSAR until reconnection is successful
            await sync_to_async(vassar_client._uninitialize_vassar)()

            # 2.1. Send connectionRequest to eval queue and update front-end
            print("----> Sending connection message")
            await vassar_client.send_connect_message(request_queue_url, user_info.eosscontext.group_id,
                                                     user_info.eosscontext.problem_id)

            vassar_status = "waiting_for_ack"
            await self.send_json({
                'type': 'services.vassar_status',
                'status': vassar_status
            })

            # 2.2. Wait for initialized design-evaluator to return parameters
            user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_connection_success = await vassar_client.connect_to_vassar(
                request_queue_url, response_queue_url, max_retries_vassar_ack)

            if vassar_connection_success:
                vassar_status = "ready"
                await self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })
            else:
                vassar_status = "ack_error"
                await self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })
        return vassar_connection_success

    async def rebuild_vassar_old(self, user_info: UserInformation, group_id: int, problem_id: int, dataset_id: int):
        vassar_client = VASSARClient(user_info)
        response_received = await vassar_client.rebuild_vassar(group_id, problem_id, dataset_id)
        if response_received:
            await self.send_json({
                'type': 'services.vassar_rebuild',
                'status': "success"
            })
        else:
            await self.send_json({
                'type': 'services.vassar_rebuild',
                'status': "failure"
            })






    ##########
    ### GA ###
    ##########



    # --> Functions
    async def start_ga(self, user_info: UserInformation):
        print('--> STARTING GA (PLACEHOLDER)')
        await self.send_json({
            'type': 'services.ga_status',
            'status': 'ready'
        })
        return 0

    async def stop_ga(self, user_info: UserInformation):
        print('--> STOPPING GA (PLACEHOLDER)')
        await self.send_json({
            'type': 'services.ga_status',
            'status': 'stop_requested'
        })
        return 0
    async def apply_ga_feature(self, user_info: UserInformation, feature_expression):
        return 0



    async def connect_ga_old(self, user_info: UserInformation, skip_check=False):
        vassar_client = VASSARClient(user_info)

        max_retries_ga_ack = 5

        # Obtain queue urls from environment and ensure they exist
        ga_request_queue_url = os.environ["GA_REQUEST_URL"]
        ga_response_queue_url = os.environ["GA_RESPONSE_URL"]
        if not await vassar_client.queue_exists_by_name("dead-letter"):
            dead_letter_url, dead_letter_arn = await vassar_client.create_dead_queue("dead-letter")
        else:
            dead_letter_url = await vassar_client.get_queue_url("dead-letter")
            dead_letter_arn = await vassar_client.get_queue_arn(dead_letter_url)

        request_create_task = None
        response_create_task = None
        if not await vassar_client.queue_exists(ga_request_queue_url):
            request_create_task = asyncio.create_task(
                vassar_client.create_queue(ga_request_queue_url.split("/")[-1], dead_letter_arn))
        if not await vassar_client.queue_exists(ga_response_queue_url):
            response_create_task = asyncio.create_task(
                vassar_client.create_queue(ga_response_queue_url.split("/")[-1], dead_letter_arn))
        if request_create_task is not None:
            await request_create_task
        if response_create_task is not None:
            await response_create_task

        # Check if there is an existing GA connection
        if not skip_check:
            if user_info.eosscontext.ga_request_queue_url is not None and await vassar_client.queue_exists(
                    user_info.eosscontext.ga_request_queue_url):
                ga_status, ga_uuid = await vassar_client.check_status(user_info.eosscontext.ga_request_queue_url,
                                                                      user_info.eosscontext.ga_response_queue_url)
            else:
                ga_status = "waiting_for_user"
                ga_uuid = None
        else:
            ga_status = "waiting_for_user"
            ga_uuid = None

        if ga_uuid is not None:
            # Save information to database
            await sync_to_async(vassar_client._initialize_ga)(user_info.eosscontext.ga_request_queue_url,
                                                              user_info.eosscontext.ga_response_queue_url,
                                                              ga_uuid)

        await self.send_json({
            'type': 'services.ga_status',
            'status': ga_status
        })
        print("Initial GA status", ga_status)

        if ga_status == "waiting_for_user":
            # Uninitialize GA until reconnection is successful
            await sync_to_async(vassar_client._uninitialize_ga)()

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            await vassar_client.send_connect_message(ga_request_queue_url)

            ga_status = "waiting_for_ack"
            await self.send_json({
                'type': 'services.ga_status',
                'status': ga_status
            })

        if ga_status == "waiting_for_ack":
            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            vassar_user_request_queue_url = user_info.eosscontext.vassar_request_queue_url
            user_ga_request_queue_url, user_ga_response_queue_url, ack_success = await vassar_client.connect_to_ga(
                ga_request_queue_url, ga_response_queue_url, vassar_user_request_queue_url, max_retries_ga_ack)
            print(user_ga_request_queue_url, user_ga_response_queue_url)

            if ack_success:
                ga_status = "ready"
            else:
                ga_status = "ack_error"
                await self.send_json({
                    'type': 'services.ga_status',
                    'status': ga_status
                })

        if ga_status == "ready":
            await self.send_json({
                'type': 'services.ga_status',
                'status': ga_status
            })
        print("Initial GA status", ga_status)

    async def start_ga_old(self, user_info: UserInformation):
        vassar_client = VASSARClient(user_info)
        dataset_client = DatasetGraphqlClient(user_info)

        if self.scope["user"].is_authenticated:
            try:

                if await dataset_client.check_dataset_read_only():
                    await self.send_json({
                        'type': 'services.ga_running_status',
                        'status': 'dataset_error',
                        'message': "Dataset is read only"
                    })
                # Define new queue for listening to GA algorithm status
                if not await vassar_client.queue_exists_by_name("dead-letter"):
                    dead_letter_url, dead_letter_arn = await vassar_client.create_dead_queue("dead-letter")
                else:
                    dead_letter_url = await vassar_client.get_queue_url("dead-letter")
                    dead_letter_arn = await vassar_client.get_queue_arn(dead_letter_url)

                ga_algorithm_queue_name = "user-queue-ga-algorithm-" + str(self.scope["user"].id)
                if not await vassar_client.queue_exists_by_name(ga_algorithm_queue_name):
                    ga_algorithm_queue_url = await vassar_client.create_queue(ga_algorithm_queue_name, dead_letter_arn)
                else:
                    ga_algorithm_queue_url = await vassar_client.get_queue_url(ga_algorithm_queue_name)

                # Start GA in container
                await vassar_client.start_ga(ga_algorithm_queue_url)

                # Start listening for AWS SQS inputs
                def aws_consumer():
                    print("--> GA Thread: Algorithm Queue URL is", ga_algorithm_queue_url)
                    sqs_client = get_boto3_client('sqs')
                    is_done = False
                    is_ga_running = False

                    while not is_done:
                        user_info.refresh_from_db()
                        channel_name = user_info.channel_name
                        response = sqs_client.receive_message(QueueUrl=ga_algorithm_queue_url, MaxNumberOfMessages=5,
                                                              WaitTimeSeconds=1, AttributeNames=["All"],
                                                              MessageAttributeNames=["All"])
                        if "Messages" in response:
                            sorted_messages = sorted(response["Messages"],
                                                     key=lambda msg: int(msg["Attributes"]["SentTimestamp"]))
                            # Send message back to frontend that GA is working fine
                            for message in sorted_messages:
                                if message["MessageAttributes"]["msgType"]["StringValue"] == "gaStarted":
                                    channel_layer = get_channel_layer()
                                    async_to_sync(channel_layer.send)(channel_name, {
                                        'type': 'services.ga_running_status',
                                        'status': 'started',
                                        'message': "GA started correctly!"
                                    })
                                    is_ga_running = True
                                    is_done = False
                                    # TODO: Add a new field to eosscontext on GA thread status
                                    print("--> GA Thread: GA Started!")
                                    sqs_client.delete_message(QueueUrl=ga_algorithm_queue_url,
                                                              ReceiptHandle=message["ReceiptHandle"])
                                elif message["MessageAttributes"]["msgType"]["StringValue"] == "gaEnded":
                                    if is_ga_running:
                                        channel_layer = get_channel_layer()
                                        async_to_sync(channel_layer.send)(channel_name, {
                                            'type': 'services.ga_running_status',
                                            'status': 'stopped',
                                            'message': "GA stopped correctly!"
                                        })
                                        is_done = True
                                        print('--> GA Thread: Ending the thread!')
                                    # TODO: Add a new field to eosscontext on GA thread status
                                    sqs_client.delete_message(QueueUrl=ga_algorithm_queue_url,
                                                              ReceiptHandle=message["ReceiptHandle"])
                                elif message["MessageAttributes"]["msgType"]["StringValue"] == "newGaArch":
                                    print('--> GA Thread: Processing a new arch!')
                                    # Keeping up for proactive
                                    add_design(self.scope["session"], self.scope["user"])
                                    sqs_client.delete_message(QueueUrl=ga_algorithm_queue_url,
                                                              ReceiptHandle=message["ReceiptHandle"])
                                elif message["MessageAttributes"]["msgType"]["StringValue"] == "ping":
                                    print('--> GA Thread: Ping received!')
                                    channel_layer = get_channel_layer()
                                    async_to_sync(channel_layer.send)(channel_name, {
                                        'type': 'services.ga_running_status',
                                        'status': 'started',
                                        'message': "Ping back"
                                    })
                                    sqs_client.delete_message(QueueUrl=ga_algorithm_queue_url,
                                                              ReceiptHandle=message["ReceiptHandle"])
                                else:
                                    # Return message to queue
                                    sqs_client.change_message_visibility(QueueUrl=ga_algorithm_queue_url,
                                                                         ReceiptHandle=message["ReceiptHandle"],
                                                                         VisibilityTimeout=0)

                    print('--> GA Thread: Thread done!')

                thread = threading.Thread(target=aws_consumer)
                thread.start()

                await self.send_json({
                    'type': 'services.ga_running_status',
                    'status': 'start_requested',
                    'message': "GA start has been requested"
                })

            except Exception as exc:
                await self.send_json({
                    'type': 'services.ga_running_status',
                    'status': 'start_error',
                    'message': "Error starting the GA: " + str(exc)
                })

        else:
            await self.send_json({
                'type': 'services.ga_running_status',
                'status': 'auth_error',
                'message': "This is only available to registered users!"
            })

    async def stop_ga_old(self, user_info: UserInformation):
        vassar_client = VASSARClient(user_info)

        if self.scope["user"].is_authenticated:
            try:
                # Call the GA stop function on Engineer
                await vassar_client.stop_ga()

                await self.send_json({
                    'type': 'services.ga_running_status',
                    'status': 'stop_requested',
                    'message': "GA stop has been requested"
                })

            except Exception as exc:
                await self.send_json({
                    'type': 'services.ga_running_status',
                    'status': 'stop_error',
                    'message': "Error stopping the GA: " + str(exc)
                })

        else:
            await self.send_json({
                'type': 'services.ga_running_status',
                'status': 'auth_error',
                'message': "This is only available to registered users!"
            })

    async def apply_ga_feature_old(self, user_info: UserInformation, feature_expression):
        vassar_client = VASSARClient(user_info)
        await vassar_client.apply_feature(feature_expression)


    # --> Out Messages
    async def services_ga_status(self, event):
        print(event)
        await self.send_json(event)

    async def ga_started(self, event):
        print(event)
        await self.send_json(event)

    async def ga_finished(self, event):
        print(event)
        await self.send_json(event)

    async def ga_new_archs(self, event):
        print(event)
        await self.send_json(event)
        
        
        

    ###################
    ### Data-Mining ###
    ###################

    # --> Out Messages
    async def data_mining_problem_entities(self, event):
        print(event)
        await self.send_json(event)

    async def data_mining_search_started(self, event):
        print(event)
        await self.send_json(event)

    async def data_mining_search_finished(self, event):
        # print(event)
        await self.send_json(event)

    async def services_ga_running_status(self, event):
        await self.send_json(event)






    ###############
    ### Mycroft ###
    ###############

    # --> Out Messages
    async def mycroft_message(self, event):
        print(event)
        await self.send_json(event)

       
