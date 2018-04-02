import datetime, json
from channels.generic.websocket import JsonWebsocketConsumer


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
            if 'experiment' not in self.scope['session']:
                self.scope['session']['experiment'] = {}
            if 'stages' not in self.scope['session']['experiment']:
                self.scope['session']['experiment']['stages'] = {}
            if content['stage'] not in self.scope['session']['experiment']['stages']:
                self.scope['session']['experiment']['stages'][content['stage']] = {}
            if 'actions' not in self.scope['session']['experiment']['stages'][content['stage']]:
                self.scope['session']['experiment']['stages'][content['stage']]['actions'] = []
            self.scope['session']['experiment']['stages'][content['stage']]['actions'].append(action)
            self.send(json.dumps(self.scope['session']['experiment']))
        elif content.get('msg_type') == 'update_state':
            if 'experiment' not in self.scope['session']:
                self.scope['session']['experiment'] = {}
            self.scope['session']['experiment']['state'] = content['state']
            self.send(json.dumps(self.scope['session']['experiment']))
        self.scope['session'].save()
