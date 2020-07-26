import json

import redis
import schedule
import threading
import AT.global_objects as global_obj
from queue import Queue

from auth_API.helpers import get_user_information, get_or_create_user_information
from daphne_ws.consumers import DaphneConsumer
from AT.global_objects import frontend_to_hub_queue
from asgiref.sync import async_to_sync
from AT.automated_at_routines.hub_routine import hub_routine
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.simulator_thread.simulator_routine_by_false_eclss import simulate_by_dummy_eclss
from AT.simulator_thread.simulator_routine_by_real_eclss import handle_eclss_update


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

        # Keep track of everyone that is on
        r = redis.Redis()
        r.sadd("all-users", self.channel_name)
        if r.sismember("all-users", self.channel_name) == 1:
            print(f"{self.channel_name} was successfully added to the all users group.")
        else:
            print(f"{self.channel_name} was not successfully added to the all users group.")

        # Send a message to the threads with the updated user information
        # user_info = get_or_create_user_information(self.scope['session'], self.scope['user'], self.daphne_version)
        # signal = {'type': 'ws_configuration_update', 'content': user_info}
        signal = {'type': 'ws_configuration_update', 'content': None}
        frontend_to_hub_queue.put(signal)

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
                # Ensure the stop queues get processed
                global_obj.sEclss_thread.join(2.0)
                if global_obj.sEclss_thread.is_alive():
                    global_obj.sEclss_thread = None
                    print("sEclss thread didn't get killed.")
                    global_obj.hub_to_sEclss_queue.queue.clear()
                else:
                    global_obj.sEclss_thread = None
                    global_obj.hub_to_sEclss_queue.queue.clear()
                global_obj.sEclss_at_thread.join(2.0)
                if global_obj.sEclss_at_thread.is_alive():
                    global_obj.simulator_at_threads[0] = None
                    print("sEclss at thread didn't get killed.")
                    global_obj.hub_to_sEclss_at_queue.queue.clear()
                else:
                    global_obj.sEclss_at_thread = None
                    global_obj.hub_to_sEclss_at_queue.queue.clear()
                print("sEclss thread killed because it has no listeners")

        elif r.sismember("fake-telemetry-one", self.channel_name) == 1:
            global_obj.frontend_to_hub_queue.put({"type": "stop_fake_telemetry_one", "channel_name": self.channel_name})
            # Ensure the queues get processed
            global_obj.simulator_threads[0].join(2.0)
            if global_obj.simulator_threads[0].is_alive():
                global_obj.simulator_threads[0] = None
                print("Fake telemetry thread didn't get killed.")
                global_obj.hub_to_simulator_queues[0].queue.clear()
            else:
                global_obj.simulator_threads[0] = None
                global_obj.hub_to_simulator_queues[0].queue.clear()
            global_obj.simulator_at_threads[0].join(2.0)
            if global_obj.simulator_at_threads[0].is_alive():
                global_obj.simulator_at_threads[0] = None
                global_obj.hub_to_simulator_at_queues[0].queue.clear()
                print("Fake at thread one didn't get killed.")
            else:
                global_obj.simulator_at_threads[0] = None
                global_obj.hub_to_simulator_at_queues[0].queue.clear()
            r.srem("fake-telemetry-one", self.channel_name)
            print(f"Channel {self.channel_name} unassigned from fake telemetry one.")
            if r.scard("fake-telemetry-one") != 0:
                r.delete("fake-telemetry-one")
        elif r.sismember("fake-telemetry-two", self.channel_name) == 1:
            global_obj.frontend_to_hub_queue.put({"type": "stop_fake_telemetry_two", "channel_name": self.channel_name})
            global_obj.simulator_threads[1].join(2.0)
            if global_obj.simulator_threads[1].is_alive():
                global_obj.simulator_threads[1] = None
                print("Fake telemetry thread two didn't get killed.")
                global_obj.hub_to_simulator_queues[1].queue.clear()
            else:
                global_obj.simulator_threads[1] = None
                global_obj.hub_to_simulator_queues[1].queue.clear()
            global_obj.simulator_at_threads[1].join(2.0)
            if global_obj.simulator_at_threads[1].is_alive():
                global_obj.simulator_at_threads[1] = None
                print("Fake at thread two didn't get killed.")
                global_obj.hub_to_simulator_at_queues[1].queue.clear()
            else:
                global_obj.simulator_at_threads[1] = None
                global_obj.hub_to_simulator_at_queues[1].queue.clear()
            r.srem("fake-telemetry-two", self.channel_name)
            print(f"Channel {self.channel_name} unassigned from fake telemetry two.")
            if r.scard("fake-telemetry-two") != 0:
                r.delete("fake-telemetry-two")

        r.srem("all-users", self.channel_name)
        if r.sismember("all-users", self.channel_name) == 1:
            print(f"Error removing {self.channel_name} from the all users group.")
        else:
            print(f"Success removing {self.channel_name} from the all users group. There are {r.scard('all-users')} "
                  f"left in the all channels group.")
            if r.scard("all-users") == 0:
                # Clear all redis variables if no one is on
                r.delete("seclss-group-users")
                r.delete("fake-telemetry-one")
                r.delete("fake-telemetry-two")
                r.delete("fake-telemetry-three")
                r.delete("fake-telemetry-four")
                r.delete("all-users")
                print("Cleared on redis variables.")

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
        # key = self.scope['path'].lstrip('api/')

        # Get an updated session store
        user_info = get_user_information(self.scope['session'], self.scope['user'])

        r = redis.Redis()

        # Update context to SQL one
        if content.get('msg_type') == 'context_add':
            for subcontext_name, subcontext in content.get('new_context').items():
                for key, value in subcontext.items():
                    setattr(getattr(user_info, subcontext_name), key, value)
                getattr(user_info, subcontext_name).save()
            user_info.save()

        elif content.get('type') == 'start_hub_thread':
            # Check if the hub thread has already started
            if global_obj.hub_thread is not None:
                self.send(json.dumps({
                    'type': 'hub_thread_response',
                    'content': {'status': 'success',
                                'message': 'The hub thread is already started. This is fine if someone else on using '
                                           'Daphne AT.',
                                'attempt': content.get('attempt')}
                }))
            else:
                # Hub thread initialization
                global_obj.hub_thread = threading.Thread(target=hub_routine,
                                                         name="Hub Thread",
                                                         args=(global_obj.frontend_to_hub_queue,
                                                               global_obj.sEclss_to_hub_queue,
                                                               global_obj.simulator_to_hub_queues[0],
                                                               global_obj.simulator_to_hub_queues[1],
                                                               global_obj.simulator_to_hub_queues[2],
                                                               global_obj.simulator_to_hub_queues[3],
                                                               global_obj.hub_to_sEclss_queue,
                                                               global_obj.hub_to_simulator_queues[0],
                                                               global_obj.hub_to_simulator_queues[1],
                                                               global_obj.hub_to_simulator_queues[2],
                                                               global_obj.hub_to_simulator_queues[3],
                                                               global_obj.hub_to_sEclss_at_queue,
                                                               global_obj.hub_to_simulator_at_queues[0],
                                                               global_obj.hub_to_simulator_at_queues[1],
                                                               global_obj.hub_to_simulator_at_queues[2],
                                                               global_obj.hub_to_simulator_at_queues[3],
                                                               global_obj.sEclss_at_to_hub_queue,
                                                               global_obj.simulator_at_to_hub_queues[0],
                                                               global_obj.simulator_at_to_hub_queues[1],
                                                               global_obj.simulator_at_to_hub_queues[2],
                                                               global_obj.simulator_at_to_hub_queues[3]
                                                               ))
                global_obj.hub_thread.start()

                # Ensure the hub thread started
                if global_obj.hub_thread.is_alive():
                    print("Hub thread started.")
                    self.send(json.dumps({
                        'type': 'hub_thread_response',
                        'content': {'status': 'success',
                                    'message': 'Success starting the hub thread.',
                                    'attempt': content.get('attempt')}
                    }))
                else:
                    global_obj.hub_thread = None
                    self.send(json.dumps({
                        'type': 'hub_thread_response',
                        'content': {'status': 'error',
                                    'message': 'Error starting the hub thread.',
                                    'attempt': content.get('attempt')}
                    }))

        elif content.get('type') == 'start_fake_telemetry':
            # Check if this user is already assigned to a fake telemetry
            if r.sismember("fake-telemetry-one", self.channel_name):
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'already_assigned',
                        'message': 'This user is already assigned to fake telemetry one.',
                        'attempt': content.get('attempt')
                    }
                }))
            elif r.sismember("fake-telemetry-two", self.channel_name):
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'already_assigned',
                        'message': 'This user is already assigned to fake telemetry two.',
                        'attempt': content.get('attempt')
                    }
                }))

            # Check if all threads are full, if not then find the first available
            if global_obj.simulator_threads[0] is not None and global_obj.simulator_threads[1] is not None:
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'full',
                        'message': 'All fake telemetries are being used.',
                        'attempt': content.get('attempt')
                    }
                }))
            # Fake telemetry 1 check
            elif global_obj.simulator_threads[0] is None and r.scard('fake-telemetry-one') == 0:
                # Anomaly detection thread initialization
                global_obj.simulator_at_threads[0] = threading.Thread(target=anomaly_treatment_routine,
                                                                      name="Fake AT Thread 1",
                                                                      args=(global_obj.hub_to_simulator_at_queues[0],
                                                                            global_obj.simulator_at_to_hub_queues[0],))
                global_obj.simulator_at_threads[0].start()

                # Telemetry Feed thread initialization
                global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                   name="Fake Telemetry Thread 1",
                                                                   args=(global_obj.simulator_to_hub_queues[0],
                                                                         global_obj.hub_to_simulator_queues[0]))
                global_obj.simulator_threads[0].start()

                # Check that the anomaly detection thread is working
                if global_obj.simulator_at_threads[0].is_alive():
                    print("Fake AT Thread 1 started.")
                    # Check that the telemetry thread has started
                    if global_obj.simulator_threads[0].is_alive():
                        print("Fake Telemetry Thread 1 started.")
                        global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_one",
                                                              "channel_layer": self.channel_layer,
                                                              "channel_name": self.channel_name})

                        r.sadd('fake-telemetry-one', self.channel_name)
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success starting Fake Telemetry Thread 1 and Fake AT Thread 1.',
                                'attempt': content.get('attempt')
                            }
                        }))
                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                   'channel_name': self.channel_name})

                    else:
                        # Stop the AT thread and send error back to frontend
                        global_obj.hub_to_simulator_at_queues[0].put({"type": "stop"})
                        global_obj.simulator_threads[0] = None
                        global_obj.hub_to_simulator_queues[0].queue.clear()
                        global_obj.simulator_at_threads[0].join(2.0)
                        if global_obj.simulator_at_threads[0].is_alive():
                            global_obj.simulator_at_threads[0] = None
                            print("Fake at thread 1 not killed.")
                            global_obj.hub_to_simulator_at_queues[0].queue.clear()
                        else:
                            global_obj.simulator_at_threads[0] = None
                            global_obj.hub_to_simulator_at_queues[0].queue.clear()
                        global_obj.frontend_to_hub_queue.put({"type": "unassign_fake_telemetry_one"})
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Success starting Fake AT Thread 1 but failure starting Fake Telemetry 1.'
                                           'Both threads stopped from running.',
                                'attempt': content.get('attempt')
                            }
                        }))

                else:
                    # Ensure the fake telemetry gets stopped and send back error
                    if global_obj.simulator_threads[0].is_alive():
                        global_obj.hub_to_simulator_queues[0].put({"type": "stop"})
                    global_obj.simulator_threads[0].join(2.0)
                    if global_obj.simulator_threads[0].is_alive():
                        global_obj.simulator_threads[0] = None
                        print("Fake telemetry thread one not stopped.")
                        global_obj.hub_to_simulator_queues[0].queue.clear()
                    else:
                        global_obj.simulator_threads[0] = None
                        global_obj.hub_to_simulator_queues[0].queue.clear()
                    global_obj.simulator_at_threads[0] = None
                    global_obj.hub_to_simulator_at_queues[0].queue.clear()
                    global_obj.frontend_to_hub_queue.put({"type": "unassign_fake_telemetry_one"})
                    self.send(json.dumps({
                        'type': 'fake_telemetry_response',
                        'content': {
                            'status': 'error',
                            'message': 'Error starting Fake AT Thread 1. Try again.',
                            'attempt': content.get('attempt')
                        }
                    }))
            # Fake telemetry 2 check
            elif global_obj.simulator_threads[1] is None and r.scard('fake-telemetry-two') == 0:
                # Anomaly detection thread initialization
                global_obj.simulator_at_threads[1] = threading.Thread(target=anomaly_treatment_routine,
                                                                      name="Fake AT Thread 2",
                                                                      args=(
                                                                      global_obj.hub_to_simulator_at_queues[1],
                                                                      global_obj.simulator_at_to_hub_queues[1],))
                global_obj.simulator_at_threads[1].start()

                # Telemetry Feed thread initialization
                global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                   name="Fake Telemetry Thread 2",
                                                                   args=(global_obj.simulator_to_hub_queues[1],
                                                                         global_obj.hub_to_simulator_queues[1]))
                global_obj.simulator_threads[1].start()

                # Check that the anomaly detection thread is working
                if global_obj.simulator_at_threads[1].is_alive():
                    print("Fake AT Thread 2 started.")
                    # Check that the telemetry thread has started
                    if global_obj.simulator_threads[1].is_alive():
                        print("Fake Telemetry Thread 2 started.")
                        global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_two",
                                                              "channel_layer": self.channel_layer,
                                                              "channel_name": self.channel_name})

                        r.sadd('fake-telemetry-two', self.channel_name)
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success starting Fake Telemetry Thread 2 and Fake AT Thread 2.',
                                'attempt': content.get('attempt')
                            }
                        }))
                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                   'channel_name': self.channel_name})

                    else:
                        # Stop the AT thread and send error back to frontend
                        global_obj.hub_to_simulator_at_queues[1].put({"type": "stop"})
                        global_obj.simulator_at_threads[1].join(2.0)
                        if global_obj.simulator_at_threads[1].is_alive():
                            global_obj.simulator_at_threads[1] = None
                            print("Fake at thread 2 not killed.")
                            global_obj.hub_to_simulator_at_queues[1].queue.clear()
                        else:
                            global_obj.simulator_at_threads[1] = None
                            global_obj.hub_to_simulator_at_queues[1].queue.clear()
                        global_obj.simulator_threads[1] = None
                        global_obj.hub_to_simulator_queues[1].queue.clear()
                        global_obj.frontend_to_hub_queue.put({"type": "unassign_fake_telemetry_two"})
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Success starting Fake AT Thread 2 but failure starting Fake Telemetry 2.'
                                           'Both threads stopped from running.',
                                'attempt': content.get('attempt')
                            }
                        }))

                else:
                    # Ensure the fake telemetry gets stopped and send back error
                    if global_obj.simulator_threads[1].is_alive():
                        global_obj.hub_to_simulator_queues[1].put({"type": "stop"})
                    global_obj.simulator_threads[1].join(2.0)
                    if global_obj.simulator_threads[1].is_alive():
                        global_obj.simulator_threads[1] = None
                        print("Fake telemetry 2 thread not killed.")
                        global_obj.hub_to_simulator_queues[1].queue.clear()
                    else:
                        global_obj.simulator_threads[1] = None
                        global_obj.hub_to_simulator_queues[1].queue.clear()
                    global_obj.simulator_at_threads[1] = None
                    global_obj.hub_to_simulator_at_queues[1].queue.clear()
                    global_obj.frontend_to_hub_queue.put({"type": "unassign_fake_telemetry_two"})
                    self.send(json.dumps({
                        'type': 'fake_telemetry_response',
                        'content': {
                            'status': 'error',
                            'message': 'Error starting Fake AT Thread 2. Try again.',
                            'attempt': content.get('attempt')
                        }
                    }))
            # Should not get to here
            else:
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'error',
                        'message': 'This user did not get assigned a fake telemetry even though not all were full.',
                        'attempt': content.get('attempt')
                    }
                }))

        elif content.get('type') == 'start_real_telemetry':
            # Check to see if the thread is already running, add that user to the group if it is, else start it
            if global_obj.sEclss_thread is not None:
                global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                      "channel_layer": self.channel_layer,
                                                      "channel_name": self.channel_name})
                frontend_to_hub_queue.put({'type': 'get_real_telemetry_params'})
                self.send(json.dumps({
                    'type': 'real_telemetry_response',
                    'content': {'status': 'already_running',
                                'message': 'The real telemetry is already started. This is fine if someone else on '
                                           'using Daphne AT.',
                                'attempt': content.get('attempt')}
                }))
            else:
                # Anomaly detection thread initialization for real telemetry
                global_obj.sEclss_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                               name="Real AT Thread",
                                                               args=(global_obj.hub_to_sEclss_at_queue,
                                                                     global_obj.sEclss_at_to_hub_queue,))
                global_obj.sEclss_at_thread.start()

                # Simulator thread initialization
                global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                            name="Real Telemetry Thread",
                                                            args=(global_obj.sEclss_to_hub_queue,
                                                                  global_obj.hub_to_sEclss_queue,
                                                                  global_obj.server_to_sEclss_queue))
                global_obj.sEclss_thread.start()

                # Check that the anomaly detection thread is working
                if global_obj.sEclss_at_thread.is_alive():
                    print("Real AT Thread started.")
                    # Check that the telemetry thread has started
                    if global_obj.sEclss_thread.is_alive():
                        print("Real telemetry started.")
                        global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                              "channel_layer": self.channel_layer,
                                                              "channel_name": self.channel_name})
                        self.send(json.dumps({
                            'type': 'real_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success starting real telemetry and real AT thread.',
                                'attempt': content.get('attempt')
                            }
                        }))
                        frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                   'channel_name': self.channel_name})

                    else:
                        # Stop the AT thread and send error back to frontend
                        global_obj.hub_to_sEclss_at_queue.put({"type": "stop"})
                        global_obj.sEclss_at_thread.join(2.0)
                        if global_obj.sEclss_at_thread.is_alive():
                            global_obj.sEclss_at_thread = None
                            print("Real at thread not killed.")
                            global_obj.hub_to_sEclss_at_queue.queue.clear()
                        else:
                            global_obj.sEclss_at_thread = None
                            global_obj.hub_to_sEclss_at_queue.queue.clear()
                        global_obj.sEclss_thread = None
                        global_obj.hub_to_sEclss_queue.queue.clear()
                        self.send(json.dumps({
                            'type': 'real_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Success starting real AT Thread but failure starting real Telemetry.'
                                           'Both threads stopped from running.',
                                'attempt': content.get('attempt')
                            }
                        }))

                else:
                    # Ensure the fake telemetry gets stopped and send back error
                    if global_obj.sEclss_thread.is_alive():
                        global_obj.hub_to_sEclss_queue.put({"type": "stop"})
                    global_obj.sEclss_thread.join(2.0)
                    if global_obj.sEclss_thread.is_alive():
                        global_obj.sEclss_thread = None
                        print("Real telemetry thread was not killed.")
                        global_obj.hub_to_sEclss_queue.queue.clear()
                    else:
                        global_obj.sEclss_thread = None
                        global_obj.hub_to_sEclss_queue.queue.clear()
                    global_obj.sEclss_at_thread = None
                    global_obj.hub_to_sEclss_at_queue.queue.clear()
                    self.send(json.dumps({
                        'type': 'real_telemetry_response',
                        'content': {
                            'status': 'error',
                            'message': 'Error starting real AT thread. Try again.',
                            'attempt': content.get('attempt')
                        }
                    }))

        elif content.get('type') == 'stop_telemetry':
            # Find what telemetry this user is assigned to if any
            if r.sismember('seclss-group-users', self.channel_name) == 1:
                # Stop if it is running
                if global_obj.sEclss_thread is None and global_obj.sEclss_at_thread is None:
                    r.srem('seclss-group-users', self.channel_name)
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to real telemetry but it is not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                elif global_obj.sEclss_thread is None:
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)

                    # If no more users are listening to the real telemetry then stop it
                    if r.scard("seclss-group-users") == 0:
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_real_telemetry'})

                        # Ensure that the thread stops
                        successful = True
                        atsEclssMessage = ''

                        global_obj.sEclss_at_thread.join(2.0)
                        if global_obj.sEclss_at_thread.is_alive():
                            successful = False
                            atsEclssMessage = 'There was an error stopping the real at thread.'

                        if successful:
                            global_obj.sEclss_at_thread = None
                            global_obj.hub_to_sEclss_at_queue.queue.clear()
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping the real telemetry. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            r.sadd('seclss-group-users', self.channel_name)
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atsEclssMessage,
                                    'attempt': content.get('attempt')
                                }
                            }))
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
                elif global_obj.sEclss_at_thread is None:
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)

                    # If no more users are listening to the real telemetry then stop it
                    if r.scard("seclss-group-users") == 0:
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_real_telemetry'})

                        # Ensure that the thread stops
                        successful = True
                        sEclssMessage = ''
                        global_obj.sEclss_thread.join(2.0)
                        if global_obj.sEclss_thread.is_alive():
                            successful = False
                            sEclssMessage = 'There was an error stopping the real telemetry thread.'

                        if successful:
                            global_obj.sEclss_thread = None
                            global_obj.hub_to_sEclss_queue.queue.clear()
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping the real telemetry. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            r.sadd('seclss-group-users', self.channel_name)
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': sEclssMessage,
                                    'attempt': content.get('attempt')
                                }
                            }))
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
                else:
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)

                    # If no more users are listening to the real telemetry then stop it
                    if r.scard("seclss-group-users") == 0:
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_real_telemetry'})

                        # Ensure that the thread stops
                        successful = True
                        sEclssMessage = ''
                        atsEclssMessage = ''
                        global_obj.sEclss_thread.join(2.0)
                        if global_obj.sEclss_thread.is_alive():
                            successful = False
                            sEclssMessage = 'There was an error stopping the real telemetry thread.'

                        global_obj.sEclss_at_thread.join(2.0)
                        if global_obj.sEclss_at_thread.is_alive():
                            successful = False
                            atsEclssMessage = 'There was an error stopping the real at thread.'

                        if successful:
                            global_obj.sEclss_thread = None
                            global_obj.sEclss_at_thread = None
                            global_obj.hub_to_sEclss_queue.queue.clear()
                            global_obj.hub_to_sEclss_at_queue.queue.clear()
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping the real telemetry. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            r.sadd('seclss-group-users', self.channel_name)
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': sEclssMessage + ' ' + atsEclssMessage,
                                    'attempt': content.get('attempt')
                                }
                            }))
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
            elif r.sismember('fake-telemetry-one', self.channel_name) == 1:
                # Stop this thread if it is running
                if global_obj.simulator_threads[0] is None and global_obj.simulator_at_threads[0] is None:
                    r.srem('fake-telemetry-one', self.channel_name)
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry one but it is not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                elif global_obj.simulator_threads[0] is None:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_one'})

                    # Ensure it gets stopped
                    successful = True
                    atSimulatorMessage = ''

                    global_obj.simulator_at_threads[0].join(2.0)
                    if global_obj.simulator_at_threads[0].is_alive():
                        successful = False
                        atSimulatorMessage = 'There was an error stopping fake at thread one.'

                    if successful:
                        r.srem('fake-telemetry-one', self.channel_name)
                        global_obj.simulator_at_threads[0] = None
                        global_obj.hub_to_simulator_at_queues[0].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry one. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': atSimulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
                elif global_obj.simulator_at_threads[0] is None:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_one'})

                    # Ensure it gets stopped
                    successful = True
                    simulatorMessage = ''
                    global_obj.simulator_threads[0].join(2.0)
                    if global_obj.simulator_threads[0].is_alive():
                        successful = False
                        simulatorMessage = 'There was an error stopping fake telemetry thread one.'

                    if successful:
                        r.srem('fake-telemetry-one', self.channel_name)
                        global_obj.simulator_threads[0] = None
                        global_obj.hub_to_simulator_queues[0].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry one. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': simulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
                else:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_one'})

                    # Ensure it gets stopped
                    successful = True
                    simulatorMessage = ''
                    atSimulatorMessage = ''
                    global_obj.simulator_threads[0].join(2.0)
                    if global_obj.simulator_threads[0].is_alive():
                        successful = False
                        simulatorMessage = 'There was an error stopping fake telemetry thread one.'

                    global_obj.simulator_at_threads[0].join(2.0)
                    if global_obj.simulator_at_threads[0].is_alive():
                        successful = False
                        atSimulatorMessage = 'There was an error stopping fake at thread one.'

                    if successful:
                        r.srem('fake-telemetry-one', self.channel_name)
                        global_obj.simulator_threads[0] = None
                        global_obj.simulator_at_threads[0] = None
                        global_obj.hub_to_simulator_queues[0].queue.clear()
                        global_obj.hub_to_simulator_at_queues[0].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry one. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': simulatorMessage + '' + atSimulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-two', self.channel_name) == 1:
                # Stop this thread if it is running
                if global_obj.simulator_threads[1] is None and global_obj.simulator_at_threads[1] is None:
                    r.srem('fake-telemetry-two', self.channel_name)
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry two but it is not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                elif global_obj.simulator_threads[1] is None:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_two'})

                    # Ensure it gets stopped
                    successful = True
                    atSimulatorMessage = ''

                    global_obj.simulator_at_threads[1].join(2.0)
                    if global_obj.simulator_at_threads[1].is_alive():
                        successful = False
                        atSimulatorMessage = 'There was an error stopping fake at thread two.'

                    if successful:
                        r.srem('fake-telemetry-two', self.channel_name)
                        global_obj.simulator_at_threads[1] = None
                        global_obj.hub_to_simulator_at_queues[1].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry two. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': atSimulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
                elif global_obj.simulator_at_threads[1] is None:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_two'})

                    # Ensure it gets stopped
                    successful = True
                    simulatorMessage = ''
                    global_obj.simulator_threads[1].join(2.0)
                    if global_obj.simulator_threads[1].is_alive():
                        successful = False
                        simulatorMessage = 'There was an error stopping fake telemetry thread two.'

                    if successful:
                        r.srem('fake-telemetry-two', self.channel_name)
                        global_obj.simulator_threads[1] = None
                        global_obj.hub_to_simulator_queues[1].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry two. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': simulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
                else:
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_two'})

                    # Ensure it gets stopped
                    successful = True
                    simulatorMessage = ''
                    atSimulatorMessage = ''
                    global_obj.simulator_threads[1].join(2.0)
                    if global_obj.simulator_threads[1].is_alive():
                        successful = False
                        simulatorMessage = 'There was an error stopping fake telemetry thread two.'

                    global_obj.simulator_at_threads[1].join(2.0)
                    if global_obj.simulator_at_threads[1].is_alive():
                        successful = False
                        atSimulatorMessage = 'There was an error stopping fake at thread two.'

                    if successful:
                        r.srem('fake-telemetry-two', self.channel_name)
                        global_obj.simulator_threads[1] = None
                        global_obj.simulator_at_threads[1] = None
                        global_obj.hub_to_simulator_queues[1].queue.clear()
                        global_obj.hub_to_simulator_at_queues[1].queue.clear()
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Success stopping fake telemetry two. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                    else:
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': simulatorMessage + '' + atSimulatorMessage,
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-three', self.channel_name) == 1:
                print("fake telemetry three")
            elif r.sismember('fake-telemetry-four', self.channel_name) == 1:
                print("fake telemetry four")
            else:
                self.send(json.dumps({
                    'type': 'stop_telemetry_response',
                    'content': {
                        'status': 'success',
                        'message': 'This user was not assigned a telemetry. Proceed.',
                        'attempt': content.get('attempt')
                    }
                }))

        elif content.get('type') == 'get_parameters':
            if r.sismember('seclss-group-users', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_real_telemetry_params'})
            elif r.sismember('fake-telemetry-one', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})
            elif r.sismember('fake-telemetry-two', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})
            elif r.sismember('fake-telemetry-three', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})
            elif r.sismember('fake-telemetry-four', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})

        elif content.get('msg_type') == 'get_real_telemetry_params':
            frontend_to_hub_queue.put({'type': 'get_real_telemetry_params'})

        elif content.get('msg_type') == 'get_fake_telemetry_params':
            frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})

        elif content.get('type') == 'ping':
            signal = {'type': 'ping', 'content': None}
            frontend_to_hub_queue.put(signal)

    def hub_thread_response(self, event):
        self.send(json.dumps(event))

    def stop_telemetry_response(self, event):
        self.send(json.dumps(event))

    def fake_telemetry_response(self, event):
        self.send(json.dumps(event))

    def real_telemetry_response(self, event):
        self.send(json.dumps(event))

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
