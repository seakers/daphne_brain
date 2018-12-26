import hashlib
import json
import threading
import time
from channels.generic.websocket import JsonWebsocketConsumer
import schedule
from auth_API.helpers import get_user_information
from daphne_API.active import live_recommender


def run_continuously(self, interval=1):
    """Continuously run, while executing pending jobs at each elapsed
    time interval.
    @return cease_continuous_run: threading.Event which can be set to
    cease continuous run.
    Please note that it is *intended behavior that run_continuously()
    does not run missed jobs*. For example, if you've registered a job
    that should run every minute and you set a continuous run interval
    of one hour then your job won't be run 60 times at each interval but
    only once.
    """

    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):

        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run


schedule.Scheduler.run_continuously = run_continuously


class DaphneConsumer(JsonWebsocketConsumer):
    scheduler = schedule.Scheduler()
    sched_stopper = None
    kill_event = None
    is_connected = False

    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()
        self.is_connected = True
        user_info = get_user_information(self.scope['session'], self.scope['user'])
        user_info.channel_name = self.channel_name
        user_info.save()

        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Add to the group
        self.channel_layer.group_add(hash_key, self.channel_name)

        # Start a ping routine every 30 seconds, close channel when ping not answered
        self.scheduler.every(30).seconds.do(self.send_ping)

        # Start a thread to run the events
        self.sched_stopper = self.scheduler.run_continuously()

        print("Hey! Im after the scheduler")

    def send_ping(self):
        # wait 15s more for ping back, if not received, close ws
        self.scheduler.clear("kill-events")
        self.kill_event = self.scheduler.every(15).seconds.do(self.kill_ws).tag("kill-events")

        if self.is_connected:
            self.send(json.dumps({"type": "ping"}))
            print("Ping sent")


    def kill_ws(self):
        print("RIP")
        if self.is_connected:
            self.close()
        return schedule.CancelJob

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

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
            suggestion_list = live_recommender.active_engineer_response(user_info, content.get('genome'))
            suggestion_list = live_recommender.parse_suggestions_list(suggestion_list)
            self.send_json({
                'type': 'active.live_suggestion',
                'agent': 'engineer',
                'suggestion_list': suggestion_list
            })
            pass # TODO: Implement server response to a Live Recommender Engineer request
        elif content.get('msg_type') == 'active_historian':
            pass # TODO: Implement server response to a Live Recommender Historian request
        elif content.get('msg_type') == 'text_msg':
            textMessage = content.get('text', None)
            # Broadcast
            self.channel_layer.group_send(hash_key, { "text": textMessage })
        elif content.get('msg_type') == 'ping':
            print("Ping back")
            # Stop the connection killer
            self.scheduler.cancel_job(self.kill_event)

    def ga_new_archs(self, event):
        print(event)
        self.send(json.dumps(event))

    def ga_started(self, event):
        print(event)
        self.send(json.dumps(event))

    def ga_finished(self, event):
        print(event)
        self.send(json.dumps(event))

    def active_notification(self, event):
        print(event)
        self.send(json.dumps(event))

    def active_modification(self, event):
        print(event)
        self.send(json.dumps(event))

    def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        key = self.scope['path'].lstrip('api/')
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        # Remove from the group on clean disconnect
        self.channel_layer.group_discard(hash_key, self.channel_name)
        self.sched_stopper.set()
        self.is_connected = False
