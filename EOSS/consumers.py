import asyncio
import os

from asgiref.sync import sync_to_async
from daphne_context.models import UserInformation
from daphne_ws.async_db_methods import _get_user_information, _save_subcontext, _save_user_info
from daphne_ws.consumers import DaphneConsumer
from EOSS.active import live_recommender
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling
from EOSS.docker.Resources import Resources


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

        elif content.get('msg_type') == 'regulate_services':
            await self.regulate_services(user_info, content.get('num_eval'), content.get('num_ga'))
        elif content.get('msg_type') == 'build':
            await self.build(user_info)
        elif content.get('msg_type') == 'ping':
            await self.ping_services(user_info)
        elif content.get('msg_type') == 'start_ga':
            await self.start_ga(user_info, content.get('identifier'), content.get('objectives'))
        elif content.get('msg_type') == 'stop_ga':
            await self.stop_ga(user_info, content.get('identifier'))
        elif content.get('msg_type') == 'stop_ga_all':
            await self.stop_ga_all(user_info)
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

    # Called every time the experiment stage changes
    async def connect_services(self, user_info: UserInformation):
        vassar_success = await self.connect_vassar(user_info)
        if vassar_success:
            await self.connect_ga(user_info)

    async def connect_vassar(self, user_info: UserInformation, skip_check: bool=False):
        # 1. Initialize instances
        vassar_instances = 1

        # 2. Create scaling client
        scaling = await sync_to_async(EvaluationScaling)(user_info, vassar_instances, user_req=True, fast=False)
        await sync_to_async(scaling.initialize)()


        # 1. Check to see if vassar connection was successful
        vassar_client = VASSARClient(user_info)
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
        return True

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
            await vassar_client.send_connect_message(ga_request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)

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





    async def build(self,  user_info: UserInformation):
        print('--> BUILDING EVALUATORS')
        resources = await sync_to_async(Resources)(user_info)
        await sync_to_async(resources.build_evaluators)()
        return True

    async def regulate_services(self, user_info: UserInformation, num_eval, num_ga):
        print('--> REGULATING SERVICES')
        resources = await sync_to_async(Resources)(user_info)
        await sync_to_async(resources.regulate_resources)(int(num_eval), int(num_ga))
        return True

    async def ping_services(self, user_info: UserInformation):
        print('--> PINGING SERVICES')
        resources = await sync_to_async(Resources)(user_info)
        results = await sync_to_async(resources.ping_resources)()
        print('--> PING RESULTS:', results)
        await self.send_json({
            'type': 'ping',
            'status': results
        })
        return True

    async def start_ga(self, user_info: UserInformation, identifier, objectives):
        print('--> STARTING GA')
        resources = await sync_to_async(Resources)(user_info)
        results = await sync_to_async(resources.start_GAs)([identifier], objectives)
        return True

    async def stop_ga(self, user_info: UserInformation, identifier):
        print('--> STOPPING GA')
        resources = await sync_to_async(Resources)(user_info)
        results = await sync_to_async(resources.stop_GAs)([identifier])
        return True

    async def stop_ga_all(self, user_info: UserInformation):
        print('--> STOPPING GA')
        resources = await sync_to_async(Resources)(user_info)
        results = await sync_to_async(resources.stop_GAs_all)()
        return True
