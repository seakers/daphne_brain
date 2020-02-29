import datetime
import json

from channels.generic.websocket import JsonWebsocketConsumer
from auth_API.helpers import get_or_create_user_information
from experiment_at.models import ATExperimentAction


class ATExperimentConsumer(JsonWebsocketConsumer):
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

        # Get an updated session store
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], 'AT')
        if hasattr(user_info, 'atexperimentcontext'):
            experiment_context = user_info.atexperimentcontext

            if content.get('msg_type') == 'add_action':
                experiment_stage = experiment_context.atexperimentstage_set.all().order_by("id")[content['stage']]
                ATExperimentAction.objects.create(atexperimentstage=experiment_stage, action=json.dumps(content['action']),
                                                  date=datetime.datetime.utcnow())
                self.send_json({
                    'action': content['action'],
                    'date': datetime.datetime.utcnow().isoformat()
                })
            elif content.get('msg_type') == 'update_state':
                experiment_context.current_state = json.dumps(content['state'])
                experiment_context.save()
                self.send_json({
                    "state": json.loads(experiment_context.current_state)
                })
