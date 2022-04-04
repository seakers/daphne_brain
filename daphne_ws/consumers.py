import hashlib
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from daphne_ws.async_db_methods import _get_or_create_user_information, _save_subcontext, _save_user_info
import schedule
from auth_API.helpers import get_user_information, get_or_create_user_information
from daphne_context.models import UserInformation


from daphne_context.models import MycroftUser


class MycroftConsumer(AsyncJsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None

    # ----------------------------
    # --- Connect / Disconnect ---
    # ----------------------------

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        print('--> CONNECTING TO MYCROFT')
        await self.accept()

        #   Query UserInformation database for mycroft access
        # key found in websocket header
        user_info: UserInformation = await self._get_user_info()
        if not user_info:
            print("BAD MYCROFT SESSION NUMBER")
            # self.close()
            # return
        else:
            user_info.mycroft_channel_name = self.channel_name
            user_info.mycroft_connection = True
            await _save_user_info(user_info)

        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Add to the group
        await self.channel_layer.group_add(hash_key, self.channel_name)

        # --> Front-end connection signal
        await self.send_to_frontend({'type': 'mycroft.message', 'subject': 'connection', 'status': 'true'})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Set Mycroft connection bool to False
        print("---- ATTEMPTING TO CLOSE CONNECTION")
        user_info = await self._get_user_info()
        user_info.mycroft_connection = False
        await _save_user_info(user_info)
        await self.send_to_frontend({'type': 'mycroft.message', 'subject': 'connection', 'status': 'false'})

        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        await self.channel_layer.group_discard(hash_key, self.channel_name)




    # ----------------------
    # --- Send / Receive ---
    # ----------------------

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

        # Messages received
        if content.get('msg_type') == 'ping':
            print("Ping received")
            await self.send_json({'type': 'ping'})
        elif content.get('msg_type') == 'mycroft_test':
            phrase = content.get('phrase')
            await self.send_json({'type': 'mycroft.test', 'content': phrase})
        elif content.get('msg_type') == 'mycroft_message':
            await self.send_to_frontend({'type': 'mycroft.message', 'subject': 'command', 'command': content.get('command')})

    async def mycroft_speak(self, event):
        print('mycroft_speak', event)
        await self.send_json(event)

    async def mycroft_test(self, event):
        print('mycroft_test', event)
        await self.send_json(event)

    async def mycroft_forward(self, event):
        print('mycroft_forward', event)
        await self.send_json(event)


    # ---------------
    # --- Helpers ---
    # ---------------

    async def _get_user_info(self):
        for header in self.scope['headers']:
            if str(header[0], 'utf-8') == 'mycroft-session':
                mycroft_session = str(header[1], 'utf-8')
                print('MYCROFT SESSION:', mycroft_session)
                return await sync_to_async(self._get_user_info_objects)(mycroft_session)
        return False

    def _get_user_info_objects(self, mycroft_session):
        return UserInformation.objects.get(mycroft_session=mycroft_session)

    async def send_to_frontend(self, message):
        user_info = await self._get_user_info()
        if not user_info:
            print("Can't send to frontend, no mycroft user found")
            return
        channel_layer = get_channel_layer()
        # Message must have 'type' filed that is a funciton in EOSS consumers
        await channel_layer.send(user_info.channel_name, message)
        # async_to_sync(channel_layer.send)(user_info.channel_name, message)



class DaphneConsumer(AsyncJsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None

    ##### WebSocket event handlers
    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        await self.accept()

        user_information: UserInformation = await _get_or_create_user_information(self.scope['session'], self.scope['user'])
        print(user_information, self.scope['session'], self.scope['user'])
        print(self.channel_name)

        user_information.channel_name = self.channel_name
        await _save_user_info(user_information)
    
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Add to the group
        await self.channel_layer.group_add(hash_key, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

        # Get an updated session store
        user_info: UserInformation = await _get_or_create_user_information(self.scope['session'], self.scope['user'])

        # Update context to SQL one
        if content.get('msg_type') == 'context_add':
            for subcontext_name, subcontext in content.get('new_context').items():
                for key, value in subcontext.items():
                    setattr(getattr(user_info, subcontext_name), key, value)
                await _save_subcontext(user_info, subcontext_name)
            await _save_user_info(user_info)
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            await self.channel_layer.group_send(hash_key, { "text": textMessage })
        elif content.get('msg_type') == 'ping':
            print("Ping received")
            await self.send_json({
                'type': 'ping'
            })

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        await self.channel_layer.group_discard(hash_key, self.channel_name)
