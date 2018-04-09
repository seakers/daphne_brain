import hashlib
from channels.generic.websocket import JsonWebsocketConsumer
from importlib import import_module
from django.conf import settings
from daphne_brain.session_lock import session_lock

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

class DaphneConsumer(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()
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
        if content.get('msg_type') == 'context_add':
            with session_lock:
                store = SessionStore(self.scope['session'].session_key)
                if 'context' not in store:
                    store['context'] = {}
                for key, value in content.get('new_context').items():
                    store['context'][key] = value
                store.save()
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            self.channel_layer.group_send(hash_key, { "text": textMessage })


    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)
