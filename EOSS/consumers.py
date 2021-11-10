import asyncio
import os

from asgiref.sync import sync_to_async
from daphne_context.models import UserInformation
from daphne_ws.async_db_methods import _get_user_information, _save_subcontext, _save_user_info
from daphne_ws.consumers import DaphneConsumer
from EOSS.active import live_recommender
from EOSS.vassar.api import VASSARClient

class EOSSConsumer(DaphneConsumer):
    # WebSocket event handlers
    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # First call function from base class
        await super(EOSSConsumer, self).receive_json(content, **kwargs)
        # Then add new behavior
        key = self.scope['path'].lstrip('api/')

        # Get an updated session store
        user_info: UserInformation = await _get_user_information(self.scope['session'], self.scope['user'])

        # Update context to SQL one
        if content.get('msg_type') == 'context_add':
            for subcontext_name, subcontext in content.get('new_context').items():
                for key, value in subcontext.items():
                    setattr(getattr(user_info, subcontext_name), key, value)
                await _save_subcontext(user_info, subcontext_name)
            _save_user_info(user_info)
        elif content.get('msg_type') == 'active_engineer':
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
        elif content.get('msg_type') == 'connect_services':
            await self.connect_services(user_info)
        elif content.get('msg_type') == 'connect_vassar':
            await self.connect_vassar(user_info, skip_check=True)
        elif content.get('msg_type') == 'connect_ga':
            await self.connect_ga(user_info, skip_check=True)
        elif content.get('msg_type') == 'rebuild_vassar':
            await self.rebuild_vassar(user_info, content.get('group_id'), content.get('problem_id'))
        elif content.get('msg_type') == 'ping':
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            # Only ping vassar and GA if logged in
            if user_info.user is not None:
                vassar_client = VASSARClient(user_info)
                container_statuses = await vassar_client.send_ping_message()
                for uuid, still_alive in container_statuses["vassar"].items():
                    if still_alive:
                        status = "ready"
                    else:
                        status = "missed_ping"
                    await self.send_json({
                        'type': 'services.vassar_status',
                        'uuid': uuid,
                        'status': status
                    })
                for uuid, still_alive in container_statuses["ga"].items():
                    if still_alive:
                        status = "ready"
                    else:
                        status = "missed_ping"
                    await self.send_json({
                        'type': 'services.ga_status',
                        'uuid': uuid,
                        'status': status
                    })
        # elif content.get('msg_type') == 'mycroft':
        #     self.send_json({
        #         'type': 'mycroft.message',
        #         'message': 'mycroft test'
        #     })

    async def mycroft_message(self, event):
        print(event)
        await self.send_json(event)

    async def ga_new_archs(self, event):
        print(event)
        await self.send_json(event)

    async def ga_started(self, event):
        print(event)
        await self.send_json(event)

    async def ga_finished(self, event):
        print(event)
        await self.send_json(event)

    async def services_ga_status(self, event):
        print(event)
        await self.send_json(event)

    async def active_message(self, event):
        print(event)
        await self.send_json(event)

    async def data_mining_problem_entities(self, event):
        print(event)
        await self.send_json(event)

    async def data_mining_search_started(self, event):
        print(event)
        await self.send_json(event)

    async def data_mining_search_finished(self, event):
        # print(event)
        await self.send_json(event)


    async def connect_services(self, user_info: UserInformation):
        vassar_success = await self.connect_vassar(user_info)
        if vassar_success:
            await self.connect_ga(user_info)

    async def connect_vassar(self, user_info: UserInformation, skip_check: bool=False):
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
            request_create_task = asyncio.create_task(vassar_client.create_queue(request_queue_url.split("/")[-1], dead_letter_arn))
        if not await vassar_client.queue_exists(response_queue_url):
            response_create_task = asyncio.create_task(vassar_client.create_queue(response_queue_url.split("/")[-1], dead_letter_arn))
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
                vassar_status = await vassar_client.check_status(user_info.eosscontext.vassar_request_queue_url,
                                                                 user_info.eosscontext.vassar_response_queue_url)
            else:
                vassar_status = "waiting_for_user"
        else:
            vassar_status = "waiting_for_user"

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
            await vassar_client.send_connect_message(request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)

            vassar_status = "waiting_for_ack"
            await self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })

            # 2.2. Wait for initialized design-evaluator to return parameters
            user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_connection_success = await vassar_client.connect_to_vassar(request_queue_url, response_queue_url, max_retries_vassar_ack)

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

    async def rebuild_vassar(user_info: UserInformation, group_id: int, problem_id: int):
        vassar_client = VASSARClient(user_info)
        vassar_client.rebuild_vassar(group_id, problem_id)

    async def connect_ga(self, user_info: UserInformation, skip_check=False):
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
            request_create_task = asyncio.create_task(vassar_client.create_queue(ga_request_queue_url.split("/")[-1], dead_letter_arn))
        if not await vassar_client.queue_exists(ga_response_queue_url):
            response_create_task = asyncio.create_task(vassar_client.create_queue(ga_response_queue_url.split("/")[-1], dead_letter_arn))
        if request_create_task is not None:
            await request_create_task
        if response_create_task is not None:
            await response_create_task

        # Check if there is an existing GA connection
        if not skip_check:
            if user_info.eosscontext.ga_request_queue_url is not None and await vassar_client.queue_exists(user_info.eosscontext.ga_request_queue_url):
                ga_status = await vassar_client.check_status(user_info.eosscontext.ga_request_queue_url, user_info.eosscontext.ga_response_queue_url)
            else:
                ga_status = "waiting_for_user"
        else:
            ga_status = "waiting_for_user"

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
            user_ga_request_queue_url, user_ga_response_queue_url, ack_success = await vassar_client.connect_to_ga(ga_request_queue_url, ga_response_queue_url, vassar_user_request_queue_url, max_retries_ga_ack)
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