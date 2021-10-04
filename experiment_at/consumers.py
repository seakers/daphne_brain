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
                self.save_json_file(experiment_context)
                self.send_json({
                    'action': content['action'],
                    'date': datetime.datetime.utcnow().isoformat()
                })
            elif content.get('msg_type') == 'update_state':
                experiment_context.current_state = json.dumps(content['state'])
                experiment_context.save()
                self.save_json_file(experiment_context)
                self.send_json({
                    "state": json.loads(experiment_context.current_state)
                })

    def save_json_file(self, experiment_context):
        # Save experiment results to file
        with open('./experiment_at/results/' + str(experiment_context.experiment_id) + '.json', 'w') as f:
            json_experiment = {
                "experiment_id": experiment_context.experiment_id,
                "current_state": json.loads(experiment_context.current_state),
                "stages": []
            }
            for stage in experiment_context.atexperimentstage_set.all():
                end_state = stage.end_state
                if end_state == '':
                    json_end_state = json.loads('' or 'null')
                else:
                    json_end_state = json.loads(end_state)
                json_stage = {
                    "type": stage.type,
                    "start_date": stage.start_date.isoformat(),
                    "end_date": stage.end_date.isoformat(),
                    "end_state": json_end_state,
                    "actions": []
                }
                for action in stage.atexperimentaction_set.all():
                    json_action = {
                        "action": json.loads(action.action),
                        "date": action.date.isoformat()
                    }
                    json_stage["actions"].append(json_action)
                json_experiment["stages"].append(json_stage)
            json.dump(json_experiment, f)