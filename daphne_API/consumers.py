import hashlib
import json
from channels.generic.websocket import JsonWebsocketConsumer


class DaphneConsumer(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()
        self.scope['session']['channel_name'] = self.channel_name
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
            if 'context' not in self.scope['session']:
                self.scope['session']['context'] = {}
            for key, value in content.get('new_context').items():
                self.scope['session']['context'][key] = value
            self.scope['session'].save()
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            self.channel_layer.group_send(hash_key, { "text": textMessage })

    def ga_new_archs(self, event):
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
