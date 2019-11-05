import schedule
import pika
import json

from auth_API.helpers import get_user_information

from daphne_ws.consumers import DaphneConsumer

from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information
from asgiref.sync import async_to_sync


class ATConsumer(DaphneConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None

    ##### WebSocket event handlers

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
        elif content.get('msg_type') == 'ping':
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            # channel = connection.channel()
            #
            # queue_name = 'thread_queue'
            # channel.queue_declare(queue=queue_name)
            # channel.basic_publish(exchange='', routing_key=queue_name, body='ping')

            channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.send)('superpotato')

            pass

    def console_text(self, event):
        self.send(json.dumps(event))

    def telemetry_update(self, event):
        self.send(json.dumps(event))

    def initialize_telemetry(self, event):
        self.send(json.dumps(event))

