import hashlib
import json

import pika
from channels.generic.websocket import JsonWebsocketConsumer
import schedule
from auth_API.helpers import get_user_information
from django.conf import settings

if 'EOSS' in settings.ACTIVE_MODULES:
    from daphne_API.active import live_recommender


class DaphneConsumer(JsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None

    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()
        user_info = get_user_information(self.scope['session'], self.scope['user'])
        user_info.channel_name = self.channel_name
        user_info.save()

        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Add to the group
        self.channel_layer.group_add(hash_key, self.channel_name)

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

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
            if user_info.eosscontext.activecontext.show_arch_suggestions:
                suggestion_list = live_recommender.active_engineer_response(user_info, content.get('genome'))
                suggestion_list = live_recommender.parse_suggestions_list(suggestion_list)
                self.send_json({
                    'type': 'active.live_suggestion',
                    'agent': 'engineer',
                    'suggestion_list': suggestion_list
                })
            else:
                self.send_json({
                                'type': 'active.notification',
                                'notification': {
                                    'title': 'Live Recommender System',
                                    'message': 'The Live Recommender System has some suggestions for your modified architecture, but you have chosen to not show them. Do you want to see them now?',
                                    'setting': 'show_arch_suggestions'
                                }
                              })

        elif content.get('msg_type') == 'active_historian':
            if user_info.eosscontext.activecontext.show_arch_suggestions:
                suggestion_list = live_recommender.active_historian_response(user_info, content.get('genome'))
                suggestion_list = live_recommender.parse_suggestions_list(suggestion_list)
                self.send_json({
                    'type': 'active.live_suggestion',
                    'agent': 'historian',
                    'suggestion_list': suggestion_list
                })
            else:
                self.send_json({
                    'type': 'active.notification',
                    'notification': {
                        'title': 'Live Recommender System',
                        'message': 'The Live Recommender System has some suggestions for your modified architecture, but you have chosen to not show them. Do you want to see them now?',
                        'setting': 'show_arch_suggestions'
                    }
                })
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            self.channel_layer.group_send(hash_key, { "text": textMessage })
        elif content.get('msg_type') == 'ping':
            print("Ping received")
            self.send_json({
                'type': 'ping'
            })
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()

            queue_name = self.scope['user'].username + '_brainga'
            channel.queue_declare(queue=queue_name)
            channel.basic_publish(exchange='', routing_key=queue_name, body='ping')


    def ga_new_archs(self, event):
        print(event)
        self.send(json.dumps(event))

    def ga_started(self, event):
        print(event)
        self.send(json.dumps(event))

    def ga_finished(self, event):
        print(event)
        self.send(json.dumps(event))

    def active_notification(self, event):
        print(event)
        self.send(json.dumps(event))

    def active_modification(self, event):
        print(event)
        self.send(json.dumps(event))

    def data_mining_problem_entities(self, event):
        print(event)
        self.send(json.dumps(event))

    def data_mining_search_started(self, event):
        print(event)
        self.send(json.dumps(event))

    def data_mining_search_finished(self, event):
        # print(event)
        self.send(json.dumps(event))

    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)
