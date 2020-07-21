import json

import redis
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
        r = redis.Redis()

        # Send a message to the threads with the updated user information
        # user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], self.daphne_version)
        # signal = {'type': 'ws_configuration_update', 'content': user_info}
        signal = {'type': 'ws_configuration_update', 'content': None}
        frontend_to_hub_queue.put(signal)

        print(f"Real telemetry group {r.smembers('seclss-group-users')}")
        print(f"Real telemetry group {r.smembers('fake_telemetry_one')}")
        print(f"Real telemetry group {r.smembers('fake_telemetry_two')}")
        r.delete('seclss-group-users')
        r.delete('fake_telemetry_one')
        r.delete('fake_telemetry_two')
        r.delete('fake_telemetry_three')
        r.delete('fake_telemetry_four')
        print(f"Real telemetry group {r.smembers('seclss-group-users')}")
        print(f"Real telemetry group {r.smembers('fake_telemetry_one')}")
        print(f"Real telemetry group {r.smembers('fake_telemetry_two')}")


    def disconnect(self, close_code):
        # remove user from real telemetry group if they were in it
        r = redis.Redis()
        if r.sismember("seclss-group-users", self.channel_name) == 1:
            async_to_sync(self.channel_layer.group_discard)("sEclss_group", self.channel_name)
            r.srem("seclss-group-users", self.channel_name)
            print(f"Channel {self.channel_name} removed from seclss group")
            # Kill the sEclss thread if no more users are on
            print(r.scard("seclss-group-users"))
            if r.scard("seclss-group-users") == 0:
                global_obj.hub_to_sEclss_queue.put({"type": "stop", "content": None})
                global_obj.hub_to_sEclss_at_queue.put({"type": "stop", "content": None})
                global_obj.sEclss_thread = None
                global_obj.sEclss_at_thread = None
                print("sEclss thread killed because it has no listeners")

        elif r.sismember("fake_telemetry_one", self.channel_name) == 1:
            r.srem("fake_telemetry_one", self.channel_name)
            global_obj.frontend_to_hub_queue.put({"type": "stop_fake_telemetry_one"})
            global_obj.simulator_threads[0] = None
            global_obj.simulator_at_threads[0] = None
            print(f"Channel {self.channel_name} unassigned from fake telemetry one")

        elif r.sismember("fake_telemetry_two", self.channel_name) == 1:
            r.srem("fake_telemetry_two", self.channel_name)
            global_obj.frontend_to_hub_queue.put({"type": "stop_fake_telemetry_two"})
            global_obj.simulator_threads[1] = None
            global_obj.simulator_at_threads[1] = None
            print(f"Channel {self.channel_name} unassigned from fake telemetry two")


        # Then call function from base class, and then add the new behavior
        super(ATConsumer, self).disconnect(close_code)

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
            signal = {'type': 'get_fake_telemetry_params', 'channel_name': user_info.channel_name}
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
