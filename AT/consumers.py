import json
import schedule
import AT.global_objects as global_obj
from queue import Queue

from auth_API.helpers import get_user_information, get_or_create_user_information
from daphne_ws.consumers import DaphneConsumer
from AT.global_objects import frontend_to_hub_queue
from asgiref.sync import async_to_sync


class ATConsumer(DaphneConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None
    daphne_version = "AT"

    ##### WebSocket event handlers

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    def connect(self):
        # First call function from base class, and then add the new behavior
        super(ATConsumer, self).connect()

        # Send a message to the threads with the updated user information
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], self.daphne_version)
        signal = {'type': 'ws_configuration_update', 'content': user_info}
        frontend_to_hub_queue.put(signal)

    def disconnect(self, close_code):
        # remove user from real telemetry group if they were in it
        if self.groups.filter(name="sEclss_group").exists():
            async_to_sync(self.channel_layer.group_discard)("sEclss_group", self.channel_name)
            global_obj.users_in_sEclss_group -= 1
            # Kill the sEclss thread if no more users are on
            if global_obj.users_in_sEclss_group == 0:
                global_obj.hub_to_sEclss_queue.put({"type": "stop", "content": None})

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # First call function from base class
        super(ATConsumer, self).receive_json(content, **kwargs)
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
        elif content.get('msg_type') == 'get_real_telemetry_params':
            signal = {'type': 'get_real_telemetry_params', 'content': None}
            frontend_to_hub_queue.put(signal)
        elif content.get('msg_type') == 'get_fake_telemetry_params':
            signal = {'type': 'get_fake_telemetry_params', 'content': None}
            frontend_to_hub_queue.put(signal)
        elif content.get('msg_type') == 'ping':
            signal = {'type': 'ping', 'content': None}
            frontend_to_hub_queue.put(signal)

    def console_text(self, event):
        self.send(json.dumps(event))

    def telemetry_update(self, event):
        self.send(json.dumps(event))

    def initialize_telemetry(self, event):
        self.send(json.dumps(event))

    def symptoms_report(self, event):
        self.send(json.dumps(event))

    def ws_configuration_update(self, event):
        self.send(json.dumps(event))

    def finish_experiment_from_mcc(self, event):
        self.send(json.dumps(event))
