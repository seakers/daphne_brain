import hashlib
import json

import pika
from channels.generic.websocket import JsonWebsocketConsumer
import schedule
from auth_API.helpers import get_or_create_user_information
from django.conf import settings

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class DataMiningConsumer(JsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None

    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        session_key = self.scope['session'].session_key

        # Accept the connection
        self.accept()
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], 'EOSS')
        user_info.channel_name = self.channel_name
        user_info.session_key = session_key
        user_info.save()

        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

        # Add to the group
        self.channel_layer.group_add(hash_key, self.channel_name)
        self.send(json.dumps({'type': 'ws_connection_successful'}))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        print('ws message received')
        print(text_data)

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

        # Get an updated session store
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], 'EOSS')

        session_key = self.scope['session'].session_key

        print("ws message received")
        print(content)

    def problem_entities(self, event):
        # print(event)
        self.send(json.dumps(event))

    def search_started(self, event):
        print(event)
        self.send(json.dumps(event))

    def search_finished(self, event):
        print(event)
        self.send(json.dumps(event))

    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        session_key = self.scope['session'].session_key

        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)
