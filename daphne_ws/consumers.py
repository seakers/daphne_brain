import hashlib
from channels.generic.websocket import JsonWebsocketConsumer
import schedule
from auth_API.helpers import get_user_information, get_or_create_user_information


class DaphneConsumer(JsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None
    daphne_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], self.daphne_version)
        user_info.channel_name = self.channel_name
        user_info.save()
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

        # Get an updated session store
        user_info = get_user_information(self.scope['session'], self.scope['user'])

        # Update context to SQL one
        if content.get('msg_type') == 'context_add':
            for subcontext_name, subcontext in content.get('new_context').items():
                for key, value in subcontext.items():
                    setattr(getattr(user_info, subcontext_name), key, value)
                getattr(user_info, subcontext_name).save()
            user_info.save()
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            self.channel_layer.group_send(hash_key, { "text": textMessage })
        elif content.get('msg_type') == 'ping':
            print("Ping received")
            self.send_json({
                'type': 'ping'
            })

    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)
