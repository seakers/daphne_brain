import os
from auth_API.helpers import get_user_information
from daphne_context.models import UserInformation
from daphne_ws.consumers import DaphneConsumer
from EOSS.active import live_recommender
from EOSS.vassar.api import VASSARClient

class EOSSConsumer(DaphneConsumer):
    # WebSocket event handlers
    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # First call function from base class
        super(EOSSConsumer, self).receive_json(content, **kwargs)
        # Then add new behavior
        key = self.scope['path'].lstrip('api/')

        # Get an updated session store
        user_info = get_user_information(self.scope['session'], self.scope['user'])

        # Update context to SQL one
        if content.get('msg_type') == 'context_add':
            for subcontext_name, subcontext in content.get('new_context').items():
                for key, value in subcontext.items():
                    setattr(getattr(user_info, subcontext_name), key, value)
                getattr(user_info, subcontext_name).save()
            user_info.save()
        elif content.get('msg_type') == 'active_engineer':
            message = live_recommender.generate_engineer_message(user_info, content.get('genome'),
                                                                 self.scope['session'].session_key)
            if message:
                self.send_json({
                        'type': 'active.message',
                        'message': message
                    })
        elif content.get('msg_type') == 'active_historian':
            message = live_recommender.generate_historian_message(user_info, content.get('genome'),
                                                                  self.scope['session'].session_key)
            if message:
                self.send_json({
                    'type': 'active.message',
                    'message': message
                })
        elif content.get('msg_type') == 'connect_services':
            self.connect_services(user_info)
        elif content.get('msg_type') == 'ping':
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            # Only ping vassar and GA if logged in
            if user_info.user is not None:
                vassar_client = VASSARClient(user_info)
                vassar_client.send_ping_message()
            pass
        # elif content.get('msg_type') == 'mycroft':
        #     self.send_json({
        #         'type': 'mycroft.message',
        #         'message': 'mycroft test'
        #     })

    def mycroft_message(self, event):
        print(event)
        self.send_json(event)

    def ga_new_archs(self, event):
        print(event)
        self.send_json(event)

    def ga_started(self, event):
        print(event)
        self.send_json(event)

    def ga_finished(self, event):
        print(event)
        self.send_json(event)

    def active_message(self, event):
        print(event)
        self.send_json(event)

    def data_mining_problem_entities(self, event):
        print(event)
        self.send_json(event)

    def data_mining_search_started(self, event):
        print(event)
        self.send_json(event)

    def data_mining_search_finished(self, event):
        # print(event)
        self.send_json(event)


    def connect_services(self, user_info: UserInformation):
        vassar_success = self.connect_vassar(user_info)
        if vassar_success:
            self.connect_ga(user_info)

    def connect_vassar(self, user_info: UserInformation):
        vassar_client = VASSARClient(user_info)

        max_retries_vassar_ack = 5
        max_retries_vassar_build = 5
        vassar_connection_success = False
        
        # Obtain queue urls from environment and ensure they exist
        request_queue_url = os.environ["VASSAR_REQUEST_URL"]
        response_queue_url = os.environ["VASSAR_RESPONSE_URL"]
        dead_letter_url, dead_letter_arn = vassar_client.create_dead_queue("dead-letter")
        vassar_client.create_queue(request_queue_url.split("/")[-1], dead_letter_arn)
        vassar_client.create_queue(response_queue_url.split("/")[-1], dead_letter_arn)

        # Check if there is an existing VASSAR connection
        if user_info.eosscontext.vassar_request_queue_url is not None and vassar_client.queue_exists(user_info.eosscontext.vassar_request_queue_url):
            vassar_status = vassar_client.check_status(user_info.eosscontext.vassar_request_queue_url, user_info.eosscontext.vassar_response_queue_url)
        else:
            vassar_status = "waiting_for_user"

        self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })
        print("Initial VASSAR status", vassar_status)

        if vassar_status == "waiting_for_user":
            # Uninitialize VASSAR until reconnection is successful
            user_info.eosscontext.vassar_information = {}
            user_info.eosscontext.save()

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            vassar_client.send_connect_message(request_queue_url)

            vassar_status = "waiting_for_ack"
            self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })

        if vassar_status == "waiting_for_ack":
            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            user_request_queue_url, user_response_queue_url, vassar_container_uuid, vassar_ack_success = vassar_client.connect_to_vassar(request_queue_url, response_queue_url, max_retries_vassar_ack)
            print(user_request_queue_url, user_response_queue_url)

            if vassar_ack_success:
                vassar_status = "uninitialized"
                self.send_json({
                        'type': 'services.vassar_status',
                        'status': vassar_status
                    })
            else:
                vassar_status = "ack_error"
                self.send_json({
                        'type': 'services.vassar_status',
                        'status': vassar_status
                    })

        if vassar_status == "uninitialized":
            # 3. Build the current problem on the container
            print("----> Initializing services")
            vassar_client.send_initialize_message(user_request_queue_url, user_info.eosscontext.group_id, user_info.eosscontext.problem_id)
            vassar_build_success = vassar_client.receive_successful_build(user_response_queue_url, vassar_container_uuid, max_retries_vassar_build)
            vassar_connection_success = True
            if not vassar_build_success:
                vassar_status = "build_error"
                self.send_json({
                        'type': 'services.vassar_status',
                        'status': vassar_status
                    })
            else:
                vassar_status = "ready"
        
        if vassar_status == "ready":
            vassar_connection_success = True # For when it's already done
            self.send_json({
                    'type': 'services.vassar_status',
                    'status': vassar_status
                })

        print("Final VASSAR status", vassar_status)
        return vassar_connection_success

    def connect_ga(self, user_info: UserInformation):
        vassar_client = VASSARClient(user_info)

        max_retries_ga_ack = 5
        
        # Obtain queue urls from environment and ensure they exist
        ga_request_queue_url = os.environ["GA_REQUEST_URL"]
        ga_response_queue_url = os.environ["GA_RESPONSE_URL"]
        dead_letter_url, dead_letter_arn = vassar_client.create_dead_queue("dead-letter")
        vassar_client.create_queue(ga_request_queue_url.split("/")[-1], dead_letter_arn)
        vassar_client.create_queue(ga_response_queue_url.split("/")[-1], dead_letter_arn)

        # Check if there is an existing GA connection
        if user_info.eosscontext.ga_request_queue_url is not None and vassar_client.queue_exists(user_info.eosscontext.ga_request_queue_url):
            ga_status = vassar_client.check_status(user_info.eosscontext.ga_request_queue_url, user_info.eosscontext.ga_response_queue_url)
        else:
            ga_status = "waiting_for_user"

        self.send_json({
                    'type': 'services.ga_status',
                    'status': ga_status
                })
        print("Initial GA status", ga_status)

        if ga_status == "waiting_for_user":
            # Uninitialize GA until reconnection is successful
            user_info.eosscontext.ga_information = {}
            user_info.eosscontext.save()

            # 1. Send connectionRequest to eval queue
            print("----> Sending connection message")
            vassar_client.send_connect_message(ga_request_queue_url)

            ga_status = "waiting_for_ack"
            self.send_json({
                    'type': 'services.ga_status',
                    'status': ga_status
                })

        if ga_status == "waiting_for_ack":
            # 2. Wait for an answer to the connectionRequest and connect to responsive containers
            print("----> Connecting to services")
            vassar_user_request_queue_url = user_info.eosscontext.vassar_request_queue_url
            user_ga_request_queue_url, user_ga_response_queue_url, ack_success = vassar_client.connect_to_ga(ga_request_queue_url, ga_response_queue_url, vassar_user_request_queue_url, max_retries_ga_ack)
            print(user_ga_request_queue_url, user_ga_response_queue_url)

            if ack_success:
                ga_status = "ready"
            else:
                ga_status = "ack_error"
                self.send_json({
                        'type': 'services.ga_status',
                        'status': ga_status
                    })
        
        if ga_status == "ready":
             self.send_json({
                    'type': 'services.ga_status',
                    'status': ga_status
                })
        print("Initial GA status", ga_status)