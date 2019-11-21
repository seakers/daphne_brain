import datetime
import json

from channels.generic.websocket import JsonWebsocketConsumer

from auth_API.helpers import get_or_create_user_information
from experiment.models import ExperimentAction


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

        # Get an updated session store
        user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], 'EOSS')
        if hasattr(user_info, 'experimentcontext'):
            experiment_context = user_info.experimentcontext

            if content.get('msg_type') == 'add_action':
                experiment_stage = experiment_context.experimentstage_set.all().order_by("id")[content['stage']]
                ExperimentAction.objects.create(experimentstage=experiment_stage, action=json.dumps(content['action']),
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
