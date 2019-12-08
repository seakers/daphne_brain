import hashlib
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import schedule
from auth_API.helpers import get_user_information, get_or_create_user_information
from daphne_context.models import UserInformation
import itertools


class MycroftConsumer(JsonWebsocketConsumer):
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

        # Mycroft session code
        user_info = self.get_mycroft_user_information()
        if not user_info:
            print("BAD MYCROFT SESSION NUMBER")
            # self.close()
            # return
        else:
            user_info.mycroft_channel_name = self.channel_name
            user_info.save()

        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Add to the group
        self.channel_layer.group_add(hash_key, self.channel_name)

    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)

    def get_mycroft_user_information(self):
        for header in self.scope['headers']:
            if str(header[0], 'utf-8') == 'mycroft-session':
                mycroft_session = str(header[1], 'utf-8')
                print('MYCROFT SESSION:', mycroft_session)
                return UserInformation.objects.filter(mycroft_session=mycroft_session)
        return False

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

        # Consumer messages
        if content.get('msg_type') == 'ping':
            print("Ping received")
            self.send_json({'type': 'ping'})

        elif content.get('msg_type') == 'mycroft':
            print("Mycroft message content", content)

        elif content.get('msg_type') == 'mycroft_forward':
            print("Mycroft message content", content)
            channel_layer = get_channel_layer()
            user_info = self.get_mycroft_user_information()
            async_to_sync(channel_layer.send)(user_info.channel_name, {'type': 'ping'})

        elif content.get('msg_type') == 'mycroft_test':
            print("Mycroft message content", content)
            phrase = content.get('phrase')
            self.send_json({'type': 'mycroft.test', 'content': phrase})

    def mycroft_speak(self, event):
        print(event)
        self.send_json(event)

    def mycroft_test(self, event):
        print(event)
        self.send_json(event)

    def mycroft_forward(self, event):
        print(event)
        self.send_json(event)



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


        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'])

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
