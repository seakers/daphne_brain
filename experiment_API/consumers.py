import datetime
import json
from channels.generic.websocket import JsonWebsocketConsumer
from importlib import import_module
from django.conf import settings
from daphne_brain.session_lock import session_lock

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

class ExperimentConsumer(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()


    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        if content.get('msg_type') == 'add_action':
            action = content['action']
            action['date'] = datetime.datetime.utcnow().isoformat()
            # Lock the threads to modify sessions without problems
            with session_lock:
                store = SessionStore(self.scope['session'].session_key)
                store['experiment']['stages'][content['stage']]['actions'].append(action)
                store.save()
            self.send(json.dumps(store['experiment']))
        elif content.get('msg_type') == 'update_state':
            # Lock the threads to modify sessions without problems
            with session_lock:
                store = SessionStore(self.scope['session'].session_key)
                store['experiment']['state'] = content['state']
                store.save()
            self.send(json.dumps(store['experiment']))
