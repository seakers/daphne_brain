import pika
import json

from auth_API.helpers import get_user_information

from daphne_ws.consumers import DaphneConsumer
from EOSS.active import live_recommender

from EOSS.models import ArchitecturesClicked, ArchitecturesUpdated, ArchitecturesEvaluated


class EOSSConsumer(DaphneConsumer):
    # WebSocket event handlers
    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # First call function from base class
        super(EOSSConsumer, self).receive_json(content, **kwargs)
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
        elif content.get('msg_type') == 'active_engineer':
            message = live_recommender.generate_engineer_message(user_info, content.get('genome'),
                                                                 self.scope['session'].session_key)
            self.send_json({
                    'type': 'active.message',
                    'message': message,
                    'from': 'active_engineer',
                })

        elif content.get('msg_type') == 'active_historian':
            message = live_recommender.generate_historian_message(user_info, content.get('genome'),
                                                                  self.scope['session'].session_key)
            self.send_json({
                'type': 'active.message',
                'message': message,
                'from': 'active_historian',
            })
        elif content.get('msg_type') == 'ping':
            # Send keep-alive signal to continuous jobs (GA, Analyst, etc)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()

            queue_name = self.scope['user'].username + '_brainga'
            channel.queue_declare(queue=queue_name)
            channel.basic_publish(exchange='', routing_key=queue_name, body='ping')


        # --> Messages for TeacherAgent Context into Tables
        elif content.get('msg_type') == 'teacher_clicked_arch':
            content = content.get('teacher_context')    # --> Dict
            entry = ArchitecturesClicked(user_information=user_info, arch_clicked=json.dumps(content))
            entry.save()
        elif content.get('msg_type') == 'teacher_clicked_arch_update':
            content = content.get('teacher_context')  # --> List
            entry = ArchitecturesUpdated(user_information=user_info, arch_updated=json.dumps(content))
            entry.save()
        elif content.get('msg_type') == 'teacher_evaluated_arch':
            content = content.get('teacher_context')  # --> Dict
            entry = ArchitecturesEvaluated(user_information=user_info, arch_evaluated=json.dumps(content))
            entry.save()





    def teacher_design_space(self, event):
        self.send(json.dumps(event))
    def teacher_objective_space(self, event):
        self.send(json.dumps(event))
    def teacher_sensitivities(self, event):
        self.send(json.dumps(event))
    def teacher_features(self, event):
        self.send(json.dumps(event))

    def ga_new_archs(self, event):
        print(event)
        self.send_json(event)

    def ga_started(self, event):
        print(event)
        self.send_json(event)

    def ga_finished(self, event):
        print(event)
        self.send_json(event)

    def active_message(self, event):
        print(event)
        self.send_json(event)

    def data_mining_problem_entities(self, event):
        print(event)
        self.send_json(event)

    def data_mining_search_started(self, event):
        print(event)
        self.send_json(event)

    def data_mining_search_finished(self, event):
        # print(event)
        self.send_json(event)
