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
            print(f"{self.channel_name} was successfully added to the all users group. The all users group contains "
                  f"{r.smembers('all-users')}")
        else:
            print(f"{self.channel_name} was not successfully added to the all users group.")

        """ In the event daphne at needs to have all variables and queues cleared and threads killed
        # Kill all the threads if they are running so that a stop message doesn't get left in the queue
        if global_obj.sEclss_thread is not None:
            if global_obj.sEclss_thread.is_alive():
                global_obj.hub_to_sEclss_queue.put({'type': 'stop'})
        if global_obj.sEclss_at_thread is not None:
            if global_obj.sEclss_at_thread.is_alive():
                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
        if global_obj.simulator_threads[0] is not None:
            if global_obj.simulator_threads[0].is_alive():
                global_obj.hub_to_simulator_queues[0].put({'type': 'stop'})
        if global_obj.simulator_at_threads[0] is not None:
            if global_obj.simulator_at_threads[0].is_alive():
                global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
        if global_obj.simulator_threads[1] is not None:
            if global_obj.simulator_threads[1].is_alive():
                global_obj.hub_to_simulator_queues[1].put({'type': 'stop'})
        if global_obj.simulator_at_threads[1] is not None:
            if global_obj.simulator_at_threads[1].is_alive():
                global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
        if global_obj.simulator_threads[2] is not None:
            if global_obj.simulator_threads[2].is_alive():
                global_obj.hub_to_simulator_queues[2].put({'type': 'stop'})
        if global_obj.simulator_at_threads[2] is not None:
            if global_obj.simulator_at_threads[2].is_alive():
                global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
        if global_obj.simulator_threads[3] is not None:
            if global_obj.simulator_threads[3].is_alive():
                global_obj.hub_to_simulator_queues[3].put({'type': 'stop'})
        if global_obj.simulator_at_threads[3] is not None:
            if global_obj.simulator_at_threads[3].is_alive():
                global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})

        # Clear all redis variables if no one is on
        r.delete("seclss-group-users")
        r.delete("fake-telemetry-one")
        r.delete("fake-telemetry-two")
        r.delete("fake-telemetry-three")
        r.delete("fake-telemetry-four")
        r.delete("all-users")
        print("Cleared on redis variables.")

        # Clear the queues and print a stop message, queues between hub and other threads get cleared in their threads
        # But ensure all get cleared anyway to ensure everything starts on a clean slate
        global_obj.frontend_to_hub_queue.queue.clear()
        global_obj.sEclss_to_hub_queue.queue.clear()
        global_obj.simulator_to_hub_queues[0].queue.clear()
        global_obj.simulator_to_hub_queues[1].queue.clear()
        global_obj.simulator_to_hub_queues[2].queue.clear()
        global_obj.simulator_to_hub_queues[3].queue.clear()
        global_obj.hub_to_sEclss_queue.queue.clear()
        global_obj.hub_to_simulator_queues[0].queue.clear()
        global_obj.hub_to_simulator_queues[1].queue.clear()
        global_obj.hub_to_simulator_queues[2].queue.clear()
        global_obj.hub_to_simulator_queues[3].queue.clear()
        global_obj.hub_to_sEclss_at_queue.queue.clear()
        global_obj.hub_to_simulator_at_queues[0].queue.clear()
        global_obj.hub_to_simulator_at_queues[1].queue.clear()
        global_obj.hub_to_simulator_at_queues[2].queue.clear()
        global_obj.hub_to_simulator_at_queues[3].queue.clear()
        global_obj.sEclss_at_to_hub_queue.queue.clear()
        global_obj.simulator_at_to_hub_queues[0].queue.clear()
        global_obj.simulator_at_to_hub_queues[1].queue.clear()
        global_obj.simulator_at_to_hub_queues[2].queue.clear()
        global_obj.simulator_at_to_hub_queues[3].queue.clear()
        print("Cleared all queues.")"""

        # Reset ping timer
        signal = {'type': 'ws_configuration_update', 'content': None}
        frontend_to_hub_queue.put(signal)

    def disconnect(self, close_code):
        r = redis.Redis()

        # remove user from real telemetry group if they were in it
        if r.sismember('seclss-group-users', self.channel_name) == 1:
            # Check if both telemetry and at thread are not initialized
            if global_obj.sEclss_thread is None and global_obj.sEclss_at_thread is None:
                r.srem('seclss-group-users', self.channel_name)
                async_to_sync(self.channel_layer.group_discard)("sEclss_group", self.channel_name)
                print(f"{self.channel_name} removed from the seclss group users.")
                print(f"{r.scard('seclss-group-users')}")

            # Check if only telemetry thread is not initialized
            elif global_obj.sEclss_thread is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.sEclss_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    if r.scard("seclss-group-users") == 0:
                        global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.sEclss_at_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.sEclss_at_thread.is_alive():
                            print('There was an error stopping real at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                # If it is not alive then it is already stopped, send back success
                else:
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the seclss group users.")
                    print(f"{r.scard('seclss-group-users')}")

            # Check if only telemetry thread is not initialized
            elif global_obj.sEclss_at_thread is None:
                # Check if telemetry thread is alive, then kill that thread
                if global_obj.sEclss_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    if r.scard("seclss-group-users") == 0:
                        global_obj.hub_to_sEclss_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.sEclss_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.sEclss_thread.is_alive():
                            print('There was an error stopping real telemetry thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                # If it is not alive then it is already stopped, send back success
                else:
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the seclss group users.")
                    print(f"{r.scard('seclss-group-users')}")
            # Check if both have been initialized
            else:
                # Check if both are alive then kill both
                if global_obj.sEclss_thread.is_alive() and global_obj.sEclss_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    # If no more users are listening to the real telemetry then stop it
                    if r.scard("seclss-group-users") == 0:
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_real_telemetry'})

                        # Ensure that the thread stops
                        global_obj.sEclss_thread.join(2.0)
                        if global_obj.sEclss_thread.is_alive():
                            print('There was an error stopping the real telemetry thread.')

                        global_obj.sEclss_at_thread.join(2.0)
                        if global_obj.sEclss_at_thread.is_alive():
                            print('There was an error stopping the real at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                # Check if only sEclss thread is alive
                elif global_obj.sEclss_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    if r.scard("seclss-group-users") == 0:
                        global_obj.hub_to_sEclss_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.sEclss_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.sEclss_thread.is_alive():
                            print('There was an error stopping real telemetry thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")
                # Check if only at thread is alive
                elif global_obj.sEclss_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    if r.scard("seclss-group-users") == 0:
                        global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.sEclss_at_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.sEclss_at_thread.is_alive():
                            print('There was an error stopping real at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the seclss group users.")
                        print(f"{r.scard('seclss-group-users')}")
                # Check if both are not running
                else:
                    async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                    r.srem("seclss-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the seclss group users.")
                    print(f"{r.scard('seclss-group-users')}")
        elif r.sismember('hera-group-users', self.channel_name) == 1:
            # Check if both telemetry and at thread are not initialized
            if global_obj.hera_thread is None and global_obj.hera_at_thread is None:
                r.srem('hera-group-users', self.channel_name)
                async_to_sync(self.channel_layer.group_discard)("hera_group", self.channel_name)
                print(f"{self.channel_name} removed from the hera group users.")
                print(f"{r.scard('hera-group-users')}")

            # Check if only telemetry thread is not initialized
            elif global_obj.hera_thread is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.hera_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    if r.scard("hera-group-users") == 0:
                        global_obj.hub_to_hera_at_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.hera_at_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.hera_at_thread.is_alive():
                            print('There was an error stopping hera at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                # If it is not alive then it is already stopped, send back success
                else:
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the hera group users.")
                    print(f"{r.scard('hera-group-users')}")

            # Check if only telemetry thread is not initialized
            elif global_obj.hera_at_thread is None:
                # Check if telemetry thread is alive, then kill that thread
                if global_obj.hera_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    if r.scard("hera-group-users") == 0:
                        global_obj.hub_to_hera_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.hera_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.hera_thread.is_alive():
                            print('There was an error stopping hera telemetry thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                # If it is not alive then it is already stopped, send back success
                else:
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the hera group users.")
                    print(f"{r.scard('hera-group-users')}")
            # Check if both have been initialized
            else:
                # Check if both are alive then kill both
                if global_obj.hera_thread.is_alive() and global_obj.hera_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    # If no more users are listening to the real telemetry then stop it
                    if r.scard("hera-group-users") == 0:
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_real_telemetry'})

                        # Ensure that the thread stops
                        global_obj.hera_thread.join(2.0)
                        if global_obj.hera_thread.is_alive():
                            print('There was an error stopping the hera telemetry thread.')

                        global_obj.hera_at_thread.join(2.0)
                        if global_obj.hera_at_thread.is_alive():
                            print('There was an error stopping the hera at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                # Check if only sEclss thread is alive
                elif global_obj.hera_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    if r.scard("hera-group-users") == 0:
                        global_obj.hub_to_hera_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.hera_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.hera_thread.is_alive():
                            print('There was an error stopping hera telemetry thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")
                # Check if only at thread is alive
                elif global_obj.hera_at_thread.is_alive():
                    # Remove user from listening to the real telemetry
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    if r.scard("hera-group-users") == 0:
                        global_obj.hub_to_hera_at_queue.put({'type': 'stop'})

                        # Ensure it gets stopped
                        global_obj.hera_at_thread.join(2.0)

                        # If not successful send back error message
                        if global_obj.hera_at_thread.is_alive():
                            print('There was an error stopping real at thread.')

                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")

                    else:
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        print(f"{self.channel_name} removed from the hera group users.")
                        print(f"{r.scard('hera-group-users')}")
                # Check if both are not running
                else:
                    async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                    r.srem("hera-group-users", self.channel_name)
                    global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                          'channel_layer': self.channel_layer})
                    print(f"{self.channel_name} removed from the hera group users.")
                    print(f"{r.scard('hera-group-users')}")

        # remove the user from the fake telemetry group if they were in one
        elif r.sismember('fake-telemetry-one', self.channel_name) == 1:
            # Check if both simulator and at threads are not initialized
            if global_obj.simulator_threads[0] is None and global_obj.simulator_at_threads[0] is None:
                r.srem('fake-telemetry-one', self.channel_name)
                if r.scard("fake-telemetry-one") != 0:
                    r.delete("fake-telemetry-one")
                global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

            # Check if only simulator thread is not initialized
            elif global_obj.simulator_threads[0] is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.simulator_at_threads[0].is_alive():
                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[0].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[0].is_alive():
                        print('There was an error stopping fake at thread one.')

                    # Unassign anyway
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

            # Check if only at thread is not initialized
            elif global_obj.simulator_at_threads[0] is None:
                # Check if simulator thread is alive, then kill that thread
                if global_obj.simulator_threads[0].is_alive():
                    global_obj.hub_to_simulator_queues[0].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[0].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[0].is_alive():
                        print('There was an error stopping fake simulator thread one.')

                    # unassign anyway
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

            # Check if both have been initialized
            else:
                # Check if both are alive, then kill both
                if global_obj.simulator_threads[0].is_alive and global_obj.simulator_at_threads[0].is_alive():
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_one'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[0].join(2.0)
                    if global_obj.simulator_threads[0].is_alive():
                        print('There was an error stopping fake telemetry thread one.')

                    global_obj.simulator_at_threads[0].join(2.0)
                    if global_obj.simulator_at_threads[0].is_alive():
                        print('There was an error stopping fake at thread one.')

                    # Unassign anyway
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

                # Check if only simulator thread is alive, then only kill simulator thread
                elif global_obj.simulator_threads[0].is_alive():
                    global_obj.hub_to_simulator_queues[0].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[0].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[0].is_alive():
                        print('There was an error stopping fake simulator thread one.')

                    # Unassign anyway
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

                # Check if only at thread is alive, then only kill at thread
                elif global_obj.simulator_at_threads[0].is_alive():
                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[0].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[0].is_alive():
                        print('There was an error stopping fake at thread one.')

                    # Unassign anyway
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})

                # Check if both are dead then unassign
                else:
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
        elif r.sismember('fake-telemetry-two', self.channel_name) == 1:
            # Check if both simulator and at threads are not initialized
            if global_obj.simulator_threads[1] is None and global_obj.simulator_at_threads[1] is None:
                r.srem('fake-telemetry-two', self.channel_name)
                if r.scard("fake-telemetry-two") != 0:
                    r.delete("fake-telemetry-two")
                global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

            # Check if only simulator thread is not initialized
            elif global_obj.simulator_threads[1] is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.simulator_at_threads[1].is_alive():
                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[1].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[1].is_alive():
                        print('There was an error stopping fake at thread two.')

                    # Unassign anyway
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

            # Check if only at thread is not initialized
            elif global_obj.simulator_at_threads[1] is None:
                # Check if simulator thread is alive, then kill that thread
                if global_obj.simulator_threads[1].is_alive():
                    global_obj.hub_to_simulator_queues[1].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[1].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[1].is_alive():
                        print('There was an error stopping fake simulator thread two.')

                    # unassign anyway
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

            # Check if both have been initialized
            else:
                # Check if both are alive, then kill both
                if global_obj.simulator_threads[1].is_alive and global_obj.simulator_at_threads[1].is_alive():
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_two'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[1].join(2.0)
                    if global_obj.simulator_threads[1].is_alive():
                        print('There was an error stopping fake telemetry thread two.')

                    global_obj.simulator_at_threads[1].join(2.0)
                    if global_obj.simulator_at_threads[1].is_alive():
                        print('There was an error stopping fake at thread two.')

                    # Unassign anyway
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

                # Check if only simulator thread is alive, then only kill simulator thread
                elif global_obj.simulator_threads[1].is_alive():
                    global_obj.hub_to_simulator_queues[1].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[1].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[1].is_alive():
                        print('There was an error stopping fake simulator thread two.')

                    # Unassign anyway
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

                # Check if only at thread is alive, then only kill at thread
                elif global_obj.simulator_at_threads[1].is_alive():
                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[1].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[1].is_alive():
                        print('There was an error stopping fake at thread two.')

                    # Unassign anyway
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})

                # Check if both are dead then unassign
                else:
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
        elif r.sismember('fake-telemetry-three', self.channel_name) == 1:
            # Check if both simulator and at threads are not initialized
            if global_obj.simulator_threads[2] is None and global_obj.simulator_at_threads[2] is None:
                r.srem('fake-telemetry-three', self.channel_name)
                if r.scard("fake-telemetry-three") != 0:
                    r.delete("fake-telemetry-three")
                global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

            # Check if only simulator thread is not initialized
            elif global_obj.simulator_threads[2] is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.simulator_at_threads[2].is_alive():
                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[2].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[2].is_alive():
                        print('There was an error stopping fake at thread three.')

                    # Unassign anyway
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

            # Check if only at thread is not initialized
            elif global_obj.simulator_at_threads[2] is None:
                # Check if simulator thread is alive, then kill that thread
                if global_obj.simulator_threads[2].is_alive():
                    global_obj.hub_to_simulator_queues[2].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[2].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[2].is_alive():
                        print('There was an error stopping fake simulator thread three.')

                    # unassign anyway
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

            # Check if both have been initialized
            else:
                # Check if both are alive, then kill both
                if global_obj.simulator_threads[2].is_alive and global_obj.simulator_at_threads[2].is_alive():
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_three'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[2].join(2.0)
                    if global_obj.simulator_threads[2].is_alive():
                        print('There was an error stopping fake telemetry thread three.')

                    global_obj.simulator_at_threads[2].join(2.0)
                    if global_obj.simulator_at_threads[2].is_alive():
                        print('There was an error stopping fake at thread three.')

                    # Unassign anyway
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

                # Check if only simulator thread is alive, then only kill simulator thread
                elif global_obj.simulator_threads[2].is_alive():
                    global_obj.hub_to_simulator_queues[2].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[2].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[2].is_alive():
                        print('There was an error stopping fake simulator thread three.')

                    # Unassign anyway
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

                # Check if only at thread is alive, then only kill at thread
                elif global_obj.simulator_at_threads[2].is_alive():
                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[2].join(2.0)
                    # If not successful send back error message
                    if global_obj.simulator_at_threads[2].is_alive():
                        print('There was an error stopping fake at thread three.')

                    # Unassign anyway
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})

                # Check if both are dead then unassign
                else:
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
        elif r.sismember('fake-telemetry-four', self.channel_name) == 1:
            # Check if both simulator and at threads are not initialized
            if global_obj.simulator_threads[3] is None and global_obj.simulator_at_threads[3] is None:
                r.srem('fake-telemetry-four', self.channel_name)
                if r.scard("fake-telemetry-four") != 0:
                    r.delete("fake-telemetry-four")
                global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

            # Check if only simulator thread is not initialized
            elif global_obj.simulator_threads[3] is None:
                # Check if at thread is alive, then kill that thread
                if global_obj.simulator_at_threads[3].is_alive():
                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[3].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[3].is_alive():
                        print('There was an error stopping fake at thread four.')

                    # Unassign anyway
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

            # Check if only at thread is not initialized
            elif global_obj.simulator_at_threads[3] is None:
                # Check if simulator thread is alive, then kill that thread
                if global_obj.simulator_threads[3].is_alive():
                    global_obj.hub_to_simulator_queues[3].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[3].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[3].is_alive():
                        print('There was an error stopping fake simulator thread four.')

                    # unassign anyway
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

                # If it is not alive then it is already stopped
                else:
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

            # Check if both have been initialized
            else:
                # Check if both are alive, then kill both
                if global_obj.simulator_threads[3].is_alive and global_obj.simulator_at_threads[3].is_alive():
                    global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_four'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[3].join(2.0)
                    if global_obj.simulator_threads[3].is_alive():
                        print('There was an error stopping fake telemetry thread four.')

                    global_obj.simulator_at_threads[3].join(2.0)
                    if global_obj.simulator_at_threads[3].is_alive():
                        print('There was an error stopping fake at thread four.')

                    # Unassign anyway
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

                # Check if only simulator thread is alive, then only kill simulator thread
                elif global_obj.simulator_threads[3].is_alive():
                    global_obj.hub_to_simulator_queues[3].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_threads[3].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_threads[3].is_alive():
                        print('There was an error stopping fake simulator thread four.')

                    # Unassign anyway
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

                # Check if only at thread is alive, then only kill at thread
                elif global_obj.simulator_at_threads[3].is_alive():
                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})

                    # Ensure it gets stopped
                    global_obj.simulator_at_threads[3].join(2.0)

                    # If not successful send back error message
                    if global_obj.simulator_at_threads[3].is_alive():
                        print('There was an error stopping fake at thread four.')

                    # Unassign anyway
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

                # Check if both are dead then unassign
                else:
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})

        # Remove the user from the all users group
        r.srem("all-users", self.channel_name)
        if r.sismember("all-users", self.channel_name) == 1:
            print(f"Error removing {self.channel_name} from the all users group.")
        else:
            print(f"Success removing {self.channel_name} from the all users group. There are {r.scard('all-users')} "
                  f"left in the all channels group. The all users group contains {r.smembers('all-users')}")
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
            # If the hub thread is none then it has never been started so start it
            if global_obj.hub_thread is None:
                # Hub thread initialization
                global_obj.hub_thread = threading.Thread(target=hub_routine,
                                                         name="Hub Thread",
                                                         args=(global_obj.frontend_to_hub_queue,
                                                               global_obj.sEclss_to_hub_queue,
                                                               global_obj.hera_to_hub_queue,
                                                               global_obj.simulator_to_hub_queues[0],
                                                               global_obj.simulator_to_hub_queues[1],
                                                               global_obj.simulator_to_hub_queues[2],
                                                               global_obj.simulator_to_hub_queues[3],
                                                               global_obj.hub_to_sEclss_queue,
                                                               global_obj.hub_to_hera_queue,
                                                               global_obj.hub_to_simulator_queues[0],
                                                               global_obj.hub_to_simulator_queues[1],
                                                               global_obj.hub_to_simulator_queues[2],
                                                               global_obj.hub_to_simulator_queues[3],
                                                               global_obj.hub_to_sEclss_at_queue,
                                                               global_obj.hub_to_hera_at_queue,
                                                               global_obj.hub_to_simulator_at_queues[0],
                                                               global_obj.hub_to_simulator_at_queues[1],
                                                               global_obj.hub_to_simulator_at_queues[2],
                                                               global_obj.hub_to_simulator_at_queues[3],
                                                               global_obj.sEclss_at_to_hub_queue,
                                                               global_obj.hera_at_to_hub_queue,
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
                # If it hasn't started then send back an error
                else:
                    self.send(json.dumps({
                        'type': 'hub_thread_response',
                        'content': {'status': 'error',
                                    'message': 'Error starting the hub thread.',
                                    'attempt': content.get('attempt')}
                    }))
            # If the hub thread is not None then check to see if it is alive or not
            else:
                # If it is alive then send back already running
                if global_obj.hub_thread.is_alive():
                    self.send(json.dumps({
                        'type': 'hub_thread_response',
                        'content': {'status': 'already_running',
                                    'message': 'The hub thread was already running. This is fine if someone else is '
                                               'using Daphne at.',
                                    'attempt': content.get('attempt')}
                    }))
                # If it is not alive then reinitialize it and restart it
                else:
                    # Hub thread initialization
                    global_obj.hub_thread = threading.Thread(target=hub_routine,
                                                             name="Hub Thread",
                                                             args=(global_obj.frontend_to_hub_queue,
                                                               global_obj.sEclss_to_hub_queue,
                                                               global_obj.hera_to_hub_queue,
                                                               global_obj.simulator_to_hub_queues[0],
                                                               global_obj.simulator_to_hub_queues[1],
                                                               global_obj.simulator_to_hub_queues[2],
                                                               global_obj.simulator_to_hub_queues[3],
                                                               global_obj.hub_to_sEclss_queue,
                                                               global_obj.hub_to_hera_queue,
                                                               global_obj.hub_to_simulator_queues[0],
                                                               global_obj.hub_to_simulator_queues[1],
                                                               global_obj.hub_to_simulator_queues[2],
                                                               global_obj.hub_to_simulator_queues[3],
                                                               global_obj.hub_to_sEclss_at_queue,
                                                               global_obj.hub_to_hera_at_queue,
                                                               global_obj.hub_to_simulator_at_queues[0],
                                                               global_obj.hub_to_simulator_at_queues[1],
                                                               global_obj.hub_to_simulator_at_queues[2],
                                                               global_obj.hub_to_simulator_at_queues[3],
                                                               global_obj.sEclss_at_to_hub_queue,
                                                               global_obj.hera_at_to_hub_queue,
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
                    # If it hasn't started then send back an error
                    else:
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
            elif r.sismember("fake-telemetry-three", self.channel_name):
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'already_assigned',
                        'message': 'This user is already assigned to fake telemetry three.',
                        'attempt': content.get('attempt')
                    }
                }))
            elif r.sismember("fake-telemetry-four", self.channel_name):
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'already_assigned',
                        'message': 'This user is already assigned to fake telemetry four.',
                        'attempt': content.get('attempt')
                    }
                }))
            # Check if simulator 1 is assigned to a user
            elif r.scard('fake-telemetry-one') == 0:
                # Check if simulator at thread 1 has not been initialized, then initialize it
                if global_obj.simulator_at_threads[0] is None:
                    # Anomaly detection thread initialization
                    global_obj.simulator_at_threads[0] = threading.Thread(target=anomaly_treatment_routine,
                                                                          name="Fake AT Thread 1",
                                                                          args=(
                                                                              global_obj.hub_to_simulator_at_queues[0],
                                                                              global_obj.simulator_at_to_hub_queues[0],
                                                                          ))
                    global_obj.simulator_at_threads[0].start()

                    # If simulator at thread 1 start was successful then proceed to start the telemetry thread
                    if global_obj.simulator_at_threads[0].is_alive():
                        print("Fake AT Thread 1 started.")
                        # Check if simulator thread 1 has not been initialized, then initialize it
                        if global_obj.simulator_threads[0] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 1",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       0],
                                                                                   global_obj.hub_to_simulator_queues[0]
                                                                               ))
                            global_obj.simulator_threads[0].start()

                            # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                            # give the channel name and layer to the hub thread
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
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 1 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Fake AT Thread 1 but failure to start fake'
                                                   'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 1 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[0].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_one",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-one', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting fake at thread 1 and fake telemetry thread 1 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 1",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           0],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           0]
                                                                                   ))
                                global_obj.simulator_threads[0].start()

                                # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                                # give the channel name and layer to the hub thread
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
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 1 but failure to start fake'
                                                       'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))

                    # If simulator at thread 1 start was a failure then don't start the fake telemetry thread
                    # and send error
                    else:
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting fake at thread 1. Fake telemetry 1 was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Simulator at thread 1 has already been initialized
                else:
                    # Check if alive then handle telemetry feed normally
                    if global_obj.simulator_at_threads[0].is_alive():
                        # Check if simulator thread 1 has not been initialized, then initialize it
                        if global_obj.simulator_threads[0] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 1",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       0],
                                                                                   global_obj.hub_to_simulator_queues[0]
                                                                               ))
                            global_obj.simulator_threads[0].start()

                            # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                            # give the channel name and layer to the hub thread
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
                                        'message': 'Success starting Fake Telemetry Thread 1 and Fake AT Thread 1 was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 1 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Fake at thread 1 was already running but failure to start fake'
                                                   'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 1 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[0].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_one",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-one', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Fake at thread 1 and fake telemetry thread 1 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 1",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           0],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           0]
                                                                                   ))
                                global_obj.simulator_threads[0].start()

                                # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                                # give the channel name and layer to the hub thread
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
                                            'message': 'Success starting Fake Telemetry Thread 1 and Fake AT Thread 1 '
                                                       'was already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Fake at thread 1 was already running but failure to start fake'
                                                       'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If not alive then reinitialize it and handle telemetry feed normally
                    else:
                        # Anomaly detection thread initialization
                        global_obj.simulator_at_threads[0] = threading.Thread(target=anomaly_treatment_routine,
                                                                              name="Fake AT Thread 1",
                                                                              args=(
                                                                                  global_obj.hub_to_simulator_at_queues[
                                                                                      0],
                                                                                  global_obj.simulator_at_to_hub_queues[
                                                                                      0],
                                                                              ))
                        global_obj.simulator_at_threads[0].start()

                        # If simulator at thread 1 start was successful then proceed to start the telemetry thread
                        if global_obj.simulator_at_threads[0].is_alive():
                            print("Fake AT Thread 1 started.")
                            # Check if simulator thread 1 has not been initialized, then initialize it
                            if global_obj.simulator_threads[0] is None:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 1",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           0],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           0]
                                                                                   ))
                                global_obj.simulator_threads[0].start()

                                # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                                # give the channel name and layer to the hub thread
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
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 1 but failure to start fake'
                                                       'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                            # Simulator thread 1 has been initialized before
                            else:
                                # Check if the thread is alive then send already running message
                                if global_obj.simulator_threads[0].is_alive():
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_one",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-one', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'already_running',
                                            'message': 'Success starting fake at thread 1 and fake telemetry thread 1 was'
                                                       ' already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # If not running, then reinitialize
                                else:
                                    # Telemetry Feed thread initialization
                                    global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                       name="Fake Telemetry Thread 1",
                                                                                       args=(
                                                                                           global_obj.simulator_to_hub_queues[
                                                                                               0],
                                                                                           global_obj.hub_to_simulator_queues[
                                                                                               0]
                                                                                       ))
                                    global_obj.simulator_threads[0].start()

                                    # If simulator thread 1 start was successful then assign it to fake telemetry 1 and
                                    # give the channel name and layer to the hub thread
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
                                        # Get telemetry parameters
                                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                                   'channel_name': self.channel_name})
                                    # Else stop the fake at thread 1 and send back error message
                                    else:
                                        global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'error',
                                                'message': 'Success starting Fake AT Thread 1 but failure to start fake'
                                                           'telemetry thread 1. Fake AT Thread stopped. Try again.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                        # If simulator at thread 1 start was a failure then don't start the fake telemetry thread
                        # and send error
                        else:
                            self.send(json.dumps({
                                'type': 'fake_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Error starting fake at thread 1. Fake telemetry 1 was not started.',
                                    'attempt': content.get('attempt')
                                }
                            }))
            # Fake telemetry 2 check
            elif r.scard('fake-telemetry-two') == 0:
                # Check if simulator at thread 2 has not been initialized, then initialize it
                if global_obj.simulator_at_threads[1] is None:
                    # Anomaly detection thread initialization
                    global_obj.simulator_at_threads[1] = threading.Thread(target=anomaly_treatment_routine,
                                                                          name="Fake AT Thread 2",
                                                                          args=(
                                                                              global_obj.hub_to_simulator_at_queues[1],
                                                                              global_obj.simulator_at_to_hub_queues[1],
                                                                          ))
                    global_obj.simulator_at_threads[1].start()

                    # If simulator at thread 2 start was successful then proceed to start the telemetry thread
                    if global_obj.simulator_at_threads[1].is_alive():
                        print("Fake AT Thread 2 started.")
                        # Check if simulator thread 2 has not been initialized, then initialize it
                        if global_obj.simulator_threads[1] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 2",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       1],
                                                                                   global_obj.hub_to_simulator_queues[1]
                                                                               ))
                            global_obj.simulator_threads[1].start()

                            # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                            # give the channel name and layer to the hub thread
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
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 2 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Fake AT Thread 2 but failure to start fake'
                                                   'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 2 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[1].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_two",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-two', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting fake at thread 2 and fake telemetry thread 2 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 2",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           1],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           1]
                                                                                   ))
                                global_obj.simulator_threads[1].start()

                                # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                                # give the channel name and layer to the hub thread
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
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 2 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 2 but failure to start fake'
                                                       'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))

                    # If simulator at thread 2 start was a failure then don't start the fake telemetry thread
                    # and send error
                    else:
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting fake at thread 2. Fake telemetry 2 was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Simulator at thread 2 has already been initialized
                else:
                    # Check if alive then handle telemetry feed normally
                    if global_obj.simulator_at_threads[1].is_alive():
                        # Check if simulator thread 2 has not been initialized, then initialize it
                        if global_obj.simulator_threads[1] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 2",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       1],
                                                                                   global_obj.hub_to_simulator_queues[1]
                                                                               ))
                            global_obj.simulator_threads[1].start()

                            # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                            # give the channel name and layer to the hub thread
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
                                        'message': 'Success starting Fake Telemetry Thread 2 and Fake AT Thread 2 was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 2 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Fake at thread 2 was already running but failure to start fake'
                                                   'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 2 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[1].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_two",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-two', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Fake at thread 2 and fake telemetry thread 2 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 2",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           1],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           1]
                                                                                   ))
                                global_obj.simulator_threads[1].start()

                                # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                                # give the channel name and layer to the hub thread
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
                                            'message': 'Success starting Fake Telemetry Thread 2 and Fake AT Thread 2 '
                                                       'was already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 2 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Fake at thread 2 was already running but failure to start fake'
                                                       'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If not alive then reinitialize it and handle telemetry feed normally
                    else:
                        # Anomaly detection thread initialization
                        global_obj.simulator_at_threads[1] = threading.Thread(target=anomaly_treatment_routine,
                                                                              name="Fake AT Thread 2",
                                                                              args=(
                                                                                  global_obj.hub_to_simulator_at_queues[
                                                                                      1],
                                                                                  global_obj.simulator_at_to_hub_queues[
                                                                                      1],
                                                                              ))
                        global_obj.simulator_at_threads[1].start()

                        # If simulator at thread 2 start was successful then proceed to start the telemetry thread
                        if global_obj.simulator_at_threads[1].is_alive():
                            print("Fake AT Thread 2 started.")
                            # Check if simulator thread 2 has not been initialized, then initialize it
                            if global_obj.simulator_threads[1] is None:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 2",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           1],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           1]
                                                                                   ))
                                global_obj.simulator_threads[1].start()

                                # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                                # give the channel name and layer to the hub thread
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
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 2 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 2 but failure to start fake'
                                                       'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                            # Simulator thread 2 has been initialized before
                            else:
                                # Check if the thread is alive then send already running message
                                if global_obj.simulator_threads[1].is_alive():
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_two",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-two', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'already_running',
                                            'message': 'Success starting fake at thread 2 and fake telemetry thread 2 was'
                                                       ' already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # If not running, then reinitialize
                                else:
                                    # Telemetry Feed thread initialization
                                    global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                       name="Fake Telemetry Thread 2",
                                                                                       args=(
                                                                                           global_obj.simulator_to_hub_queues[
                                                                                               1],
                                                                                           global_obj.hub_to_simulator_queues[
                                                                                               1]
                                                                                       ))
                                    global_obj.simulator_threads[1].start()

                                    # If simulator thread 2 start was successful then assign it to fake telemetry 2 and
                                    # give the channel name and layer to the hub thread
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
                                        # Get telemetry parameters
                                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                                   'channel_name': self.channel_name})
                                    # Else stop the fake at thread 2 and send back error message
                                    else:
                                        global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'error',
                                                'message': 'Success starting Fake AT Thread 2 but failure to start fake'
                                                           'telemetry thread 2. Fake AT Thread stopped. Try again.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                        # If simulator at thread 2 start was a failure then don't start the fake telemetry thread
                        # and send error
                        else:
                            self.send(json.dumps({
                                'type': 'fake_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Error starting fake at thread 2. Fake telemetry 2 was not started.',
                                    'attempt': content.get('attempt')
                                }
                            }))
            # Fake telemetry 3 check
            elif r.scard('fake-telemetry-three') == 0:
                # Check if simulator at thread 3 has not been initialized, then initialize it
                if global_obj.simulator_at_threads[2] is None:
                    # Anomaly detection thread initialization
                    global_obj.simulator_at_threads[2] = threading.Thread(target=anomaly_treatment_routine,
                                                                          name="Fake AT Thread 3",
                                                                          args=(
                                                                              global_obj.hub_to_simulator_at_queues[2],
                                                                              global_obj.simulator_at_to_hub_queues[2],
                                                                          ))
                    global_obj.simulator_at_threads[2].start()

                    # If simulator at thread 3 start was successful then proceed to start the telemetry thread
                    if global_obj.simulator_at_threads[2].is_alive():
                        print("Fake AT Thread 3 started.")
                        # Check if simulator thread 3 has not been initialized, then initialize it
                        if global_obj.simulator_threads[2] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 3",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       2],
                                                                                   global_obj.hub_to_simulator_queues[2]
                                                                               ))
                            global_obj.simulator_threads[2].start()

                            # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                            # give the channel name and layer to the hub thread
                            if global_obj.simulator_threads[2].is_alive():
                                print("Fake Telemetry Thread 3 started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-three', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 3 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Fake AT Thread 3 but failure to start fake'
                                                   'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 1 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[2].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-three', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting fake at thread 3 and fake telemetry thread 3 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 3",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           2],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           2]
                                                                                   ))
                                global_obj.simulator_threads[2].start()

                                # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[2].is_alive():
                                    print("Fake Telemetry Thread 3 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-three', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 3 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 3 but failure to start fake'
                                                       'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))

                    # If simulator at thread 3 start was a failure then don't start the fake telemetry thread
                    # and send error
                    else:
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting fake at thread 3. Fake telemetry 3 was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Simulator at thread 1 has already been initialized
                else:
                    # Check if alive then handle telemetry feed normally
                    if global_obj.simulator_at_threads[2].is_alive():
                        # Check if simulator thread 3 has not been initialized, then initialize it
                        if global_obj.simulator_threads[2] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 3",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       2],
                                                                                   global_obj.hub_to_simulator_queues[2]
                                                                               ))
                            global_obj.simulator_threads[2].start()

                            # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                            # give the channel name and layer to the hub thread
                            if global_obj.simulator_threads[2].is_alive():
                                print("Fake Telemetry Thread 3 started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-three', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3 was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 3 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Fake at thread 3 was already running but failure to start fake'
                                                   'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 1 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[2].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-three', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Fake at thread 3 and fake telemetry thread 3 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 3",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           2],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           2]
                                                                                   ))
                                global_obj.simulator_threads[2].start()

                                # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[2].is_alive():
                                    print("Fake Telemetry Thread 3 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-three', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3 '
                                                       'was already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Fake at thread 3 was already running but failure to start fake'
                                                       'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If not alive then reinitialize it and handle telemetry feed normally
                    else:
                        # Anomaly detection thread initialization
                        global_obj.simulator_at_threads[2] = threading.Thread(target=anomaly_treatment_routine,
                                                                              name="Fake AT Thread 3",
                                                                              args=(
                                                                                  global_obj.hub_to_simulator_at_queues[
                                                                                      2],
                                                                                  global_obj.simulator_at_to_hub_queues[
                                                                                      2],
                                                                              ))
                        global_obj.simulator_at_threads[2].start()

                        # If simulator at thread 3 start was successful then proceed to start the telemetry thread
                        if global_obj.simulator_at_threads[2].is_alive():
                            print("Fake AT Thread 3 started.")
                            # Check if simulator thread 3 has not been initialized, then initialize it
                            if global_obj.simulator_threads[2] is None:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 3",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           2],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           2]
                                                                                   ))
                                global_obj.simulator_threads[2].start()

                                # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[2].is_alive():
                                    print("Fake Telemetry Thread 3 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-three', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 3 but failure to start fake'
                                                       'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                            # Simulator thread 3 has been initialized before
                            else:
                                # Check if the thread is alive then send already running message
                                if global_obj.simulator_threads[2].is_alive():
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-three', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'already_running',
                                            'message': 'Success starting fake at thread 3 and fake telemetry thread 3 was'
                                                       ' already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # If not running, then reinitialize
                                else:
                                    # Telemetry Feed thread initialization
                                    global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                       name="Fake Telemetry Thread 3",
                                                                                       args=(
                                                                                           global_obj.simulator_to_hub_queues[
                                                                                               2],
                                                                                           global_obj.hub_to_simulator_queues[
                                                                                               2]
                                                                                       ))
                                    global_obj.simulator_threads[2].start()

                                    # If simulator thread 3 start was successful then assign it to fake telemetry 3 and
                                    # give the channel name and layer to the hub thread
                                    if global_obj.simulator_threads[2].is_alive():
                                        print("Fake Telemetry Thread 3 started.")
                                        global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three",
                                                                              "channel_layer": self.channel_layer,
                                                                              "channel_name": self.channel_name})

                                        r.sadd('fake-telemetry-three', self.channel_name)
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'success',
                                                'message': 'Success starting Fake Telemetry Thread 3 and Fake AT Thread 3.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                                        # Get telemetry parameters
                                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                                   'channel_name': self.channel_name})
                                    # Else stop the fake at thread 3 and send back error message
                                    else:
                                        global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'error',
                                                'message': 'Success starting Fake AT Thread 3 but failure to start fake'
                                                           'telemetry thread 3. Fake AT Thread stopped. Try again.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                        # If simulator at thread 3 start was a failure then don't start the fake telemetry thread
                        # and send error
                        else:
                            self.send(json.dumps({
                                'type': 'fake_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Error starting fake at thread 3. Fake telemetry 3 was not started.',
                                    'attempt': content.get('attempt')
                                }
                            }))
            # Fake telemtry 4 check
            elif r.scard('fake-telemetry-four') == 0:
                # Check if simulator at thread 4 has not been initialized, then initialize it
                if global_obj.simulator_at_threads[3] is None:
                    # Anomaly detection thread initialization
                    global_obj.simulator_at_threads[3] = threading.Thread(target=anomaly_treatment_routine,
                                                                          name="Fake AT Thread 4",
                                                                          args=(
                                                                              global_obj.hub_to_simulator_at_queues[3],
                                                                              global_obj.simulator_at_to_hub_queues[3],
                                                                          ))
                    global_obj.simulator_at_threads[3].start()

                    # If simulator at thread 4 start was successful then proceed to start the telemetry thread
                    if global_obj.simulator_at_threads[3].is_alive():
                        print("Fake AT Thread 4 started.")
                        # Check if simulator thread 4 has not been initialized, then initialize it
                        if global_obj.simulator_threads[3] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 4",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       3],
                                                                                   global_obj.hub_to_simulator_queues[3]
                                                                               ))
                            global_obj.simulator_threads[3].start()

                            # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                            # give the channel name and layer to the hub thread
                            if global_obj.simulator_threads[3].is_alive():
                                print("Fake Telemetry Thread 4 started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-four', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 1 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Fake AT Thread 4 but failure to start fake'
                                                   'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 4 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[3].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-four', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting fake at thread 4 and fake telemetry thread 4 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 4",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           3],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           3]
                                                                                   ))
                                global_obj.simulator_threads[3].start()

                                # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[3].is_alive():
                                    print("Fake Telemetry Thread 4 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-four', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 1 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 4 but failure to start fake'
                                                       'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))

                    # If simulator at thread 4 start was a failure then don't start the fake telemetry thread
                    # and send error
                    else:
                        self.send(json.dumps({
                            'type': 'fake_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting fake at thread 4. Fake telemetry 4 was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Simulator at thread 4 has already been initialized
                else:
                    # Check if alive then handle telemetry feed normally
                    if global_obj.simulator_at_threads[3].is_alive():
                        # Check if simulator thread 4 has not been initialized, then initialize it
                        if global_obj.simulator_threads[3] is None:
                            # Telemetry Feed thread initialization
                            global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                               name="Fake Telemetry Thread 4",
                                                                               args=(
                                                                                   global_obj.simulator_to_hub_queues[
                                                                                       3],
                                                                                   global_obj.hub_to_simulator_queues[3]
                                                                               ))
                            global_obj.simulator_threads[3].start()

                            # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                            # give the channel name and layer to the hub thread
                            if global_obj.simulator_threads[3].is_alive():
                                print("Fake Telemetry Thread 4 started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-four', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4 was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # Else stop the fake at thread 1 and send back error message
                            else:
                                global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Fake at thread 4 was already running but failure to start fake'
                                                   'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # Simulator thread 1 has been initialized before
                        else:
                            # Check if the thread is alive then send already running message
                            if global_obj.simulator_threads[3].is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})

                                r.sadd('fake-telemetry-four', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'fake_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Fake at thread 4 and fake telemetry thread 4 was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                # Get telemetry parameters
                                frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                           'channel_name': self.channel_name})
                            # If not running, then reinitialize
                            else:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 4",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           3],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           3]
                                                                                   ))
                                global_obj.simulator_threads[3].start()

                                # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[3].is_alive():
                                    print("Fake Telemetry Thread 4 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-four', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4 '
                                                       'was already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 4 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Fake at thread 4 was already running but failure to start fake'
                                                       'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If not alive then reinitialize it and handle telemetry feed normally
                    else:
                        # Anomaly detection thread initialization
                        global_obj.simulator_at_threads[3] = threading.Thread(target=anomaly_treatment_routine,
                                                                              name="Fake AT Thread 4",
                                                                              args=(
                                                                                  global_obj.hub_to_simulator_at_queues[
                                                                                      3],
                                                                                  global_obj.simulator_at_to_hub_queues[
                                                                                      3],
                                                                              ))
                        global_obj.simulator_at_threads[3].start()

                        # If simulator at thread 4 start was successful then proceed to start the telemetry thread
                        if global_obj.simulator_at_threads[3].is_alive():
                            print("Fake AT Thread 4 started.")
                            # Check if simulator thread 4 has not been initialized, then initialize it
                            if global_obj.simulator_threads[3] is None:
                                # Telemetry Feed thread initialization
                                global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                   name="Fake Telemetry Thread 4",
                                                                                   args=(
                                                                                       global_obj.simulator_to_hub_queues[
                                                                                           3],
                                                                                       global_obj.hub_to_simulator_queues[
                                                                                           3]
                                                                                   ))
                                global_obj.simulator_threads[3].start()

                                # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                                # give the channel name and layer to the hub thread
                                if global_obj.simulator_threads[3].is_alive():
                                    print("Fake Telemetry Thread 4 started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-four', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # Else stop the fake at thread 4 and send back error message
                                else:
                                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Fake AT Thread 4 but failure to start fake'
                                                       'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                            # Simulator thread 4 has been initialized before
                            else:
                                # Check if the thread is alive then send already running message
                                if global_obj.simulator_threads[3].is_alive():
                                    global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})

                                    r.sadd('fake-telemetry-four', self.channel_name)
                                    self.send(json.dumps({
                                        'type': 'fake_telemetry_response',
                                        'content': {
                                            'status': 'already_running',
                                            'message': 'Success starting fake at thread 4 and fake telemetry thread 4 was'
                                                       ' already running.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    # Get telemetry parameters
                                    frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                               'channel_name': self.channel_name})
                                # If not running, then reinitialize
                                else:
                                    # Telemetry Feed thread initialization
                                    global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                                                       name="Fake Telemetry Thread 4",
                                                                                       args=(
                                                                                           global_obj.simulator_to_hub_queues[
                                                                                               3],
                                                                                           global_obj.hub_to_simulator_queues[
                                                                                               3]
                                                                                       ))
                                    global_obj.simulator_threads[3].start()

                                    # If simulator thread 4 start was successful then assign it to fake telemetry 4 and
                                    # give the channel name and layer to the hub thread
                                    if global_obj.simulator_threads[3].is_alive():
                                        print("Fake Telemetry Thread 4 started.")
                                        global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four",
                                                                              "channel_layer": self.channel_layer,
                                                                              "channel_name": self.channel_name})

                                        r.sadd('fake-telemetry-four', self.channel_name)
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'success',
                                                'message': 'Success starting Fake Telemetry Thread 4 and Fake AT Thread 4.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                                        # Get telemetry parameters
                                        frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params',
                                                                   'channel_name': self.channel_name})
                                    # Else stop the fake at thread 1 and send back error message
                                    else:
                                        global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})
                                        self.send(json.dumps({
                                            'type': 'fake_telemetry_response',
                                            'content': {
                                                'status': 'error',
                                                'message': 'Success starting Fake AT Thread 4 but failure to start fake'
                                                           'telemetry thread 4. Fake AT Thread stopped. Try again.',
                                                'attempt': content.get('attempt')
                                            }
                                        }))
                        # If simulator at thread 4 start was a failure then don't start the fake telemetry thread
                        # and send error
                        else:
                            self.send(json.dumps({
                                'type': 'fake_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Error starting fake at thread 4. Fake telemetry 4 was not started.',
                                    'attempt': content.get('attempt')
                                }
                            }))
            # Check if all are full
            elif r.scard('fake-telemetry-one') == 1 and r.scard('fake-telemetry-two') == 1 and \
                    r.scard('fake-telemetry-three') == 1 and r.scard('fake-telemetry-four') == 1:
                self.send(json.dumps({
                    'type': 'fake_telemetry_response',
                    'content': {
                        'status': 'full',
                        'message': 'All fake telemetries are in use.',
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
            # Check if sEclss at thread is not initialized then initialize it and handle sEclss thread
            if global_obj.sEclss_at_thread is None:
                # Anomaly detection thread initialization for real telemetry
                global_obj.sEclss_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                               name="Real AT Thread",
                                                               args=(global_obj.hub_to_sEclss_at_queue,
                                                                     global_obj.sEclss_at_to_hub_queue,))
                global_obj.sEclss_at_thread.start()

                # Check that the anomaly detection thread is working then check sEclss thread
                if global_obj.sEclss_at_thread.is_alive():
                    print("Real AT Thread started.")
                    # Check if sEclss thread has not been initialized, then initialize it
                    if global_obj.sEclss_thread is None:
                        # Simulator thread initialization
                        global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                    name="Real Telemetry Thread",
                                                                    args=(global_obj.sEclss_to_hub_queue,
                                                                          global_obj.hub_to_sEclss_queue,
                                                                          global_obj.server_to_sEclss_queue))
                        global_obj.sEclss_thread.start()

                        # Check that the telemetry thread has started, then send success
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
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If not working then stop at thread and send back error
                        else:
                            global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                            self.send(json.dumps({
                                'type': 'real_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Success starting Real AT Thread but failure to start real'
                                               'telemetry thread. Real AT Thread stopped. Try again.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If sEclss thread has been initialized then handle if it alive or not
                    else:
                        # If it is alive then join it
                        if global_obj.sEclss_thread.is_alive():
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'real_telemetry_response',
                                'content': {
                                    'status': 'already_running',
                                    'message': 'Success starting real at thread and real telemetry was'
                                               ' already running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If it is not alive then reinitialize it
                        else:
                            # Simulator thread initialization
                            global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                        name="Real Telemetry Thread",
                                                                        args=(global_obj.sEclss_to_hub_queue,
                                                                              global_obj.hub_to_sEclss_queue,
                                                                              global_obj.server_to_sEclss_queue))
                            global_obj.sEclss_thread.start()

                            # Check that the telemetry thread has started, then send success
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
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Real AT Thread but failure to start real'
                                                   'telemetry thread. Real AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                # If sEclss at thread does not start then don't start real telemetry and send back error
                else:
                    self.send(json.dumps({
                        'type': 'real_telemetry_response',
                        'content': {
                            'status': 'error',
                            'message': 'Error starting real at thread. Real telemetry was not started.',
                            'attempt': content.get('attempt')
                        }
                    }))
            # If sEclss at thread has been initialized then handle if it is alive or not
            else:
                # If alive then check telemetry as normal
                if global_obj.sEclss_at_thread.is_alive():
                    # Check if sEclss thread has not been initialized, then initialize it
                    if global_obj.sEclss_thread is None:
                        # Simulator thread initialization
                        global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                    name="Real Telemetry Thread",
                                                                    args=(global_obj.sEclss_to_hub_queue,
                                                                          global_obj.hub_to_sEclss_queue,
                                                                          global_obj.server_to_sEclss_queue))
                        global_obj.sEclss_thread.start()

                        # Check that the telemetry thread has started, then send success
                        if global_obj.sEclss_thread.is_alive():
                            print("Real telemetry started.")
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'real_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success starting real telemetry and real AT thread was already'
                                               ' running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If not working then stop at thread and send back error
                        else:
                            global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                            self.send(json.dumps({
                                'type': 'real_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Real at thread was already running but failure to start real'
                                               'telemetry thread. Real AT Thread stopped. Try again.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If sEclss thread has been initialized then handle if it alive or not
                    else:
                        # If it is alive then join it
                        if global_obj.sEclss_thread.is_alive():
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'real_telemetry_response',
                                'content': {
                                    'status': 'already_running',
                                    'message': 'Real at thread and real telemetry was'
                                               ' already running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If it is not alive then reinitialize it
                        else:
                            # Simulator thread initialization
                            global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                        name="Real Telemetry Thread",
                                                                        args=(global_obj.sEclss_to_hub_queue,
                                                                              global_obj.hub_to_sEclss_queue,
                                                                              global_obj.server_to_sEclss_queue))
                            global_obj.sEclss_thread.start()

                            # Check that the telemetry thread has started, then send success
                            if global_obj.sEclss_thread.is_alive():
                                print("Real telemetry started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting real telemetry and real AT thread was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Real AT Thread was already running but failure to start real'
                                                   'telemetry thread. Real AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))

                # If not alive then reinitialize it and handle telemetry normally
                else:
                    # Anomaly detection thread initialization for real telemetry
                    global_obj.sEclss_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                                   name="Real AT Thread",
                                                                   args=(global_obj.hub_to_sEclss_at_queue,
                                                                         global_obj.sEclss_at_to_hub_queue,))
                    global_obj.sEclss_at_thread.start()

                    # Check that the anomaly detection thread is working then check sEclss thread
                    if global_obj.sEclss_at_thread.is_alive():
                        print("Real AT Thread started.")
                        # Check if sEclss thread has not been initialized, then initialize it
                        if global_obj.sEclss_thread is None:
                            # Simulator thread initialization
                            global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                        name="Real Telemetry Thread",
                                                                        args=(global_obj.sEclss_to_hub_queue,
                                                                              global_obj.hub_to_sEclss_queue,
                                                                              global_obj.server_to_sEclss_queue))
                            global_obj.sEclss_thread.start()

                            # Check that the telemetry thread has started, then send success
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
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Real AT Thread but failure to start real'
                                                   'telemetry thread. Real AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # If sEclss thread has been initialized then handle if it alive or not
                        else:
                            # If it is alive then join it
                            if global_obj.sEclss_thread.is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting real at thread and real telemetry was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_real_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If it is not alive then reinitialize it
                            else:
                                # Simulator thread initialization
                                global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                                            name="Real Telemetry Thread",
                                                                            args=(global_obj.sEclss_to_hub_queue,
                                                                                  global_obj.hub_to_sEclss_queue,
                                                                                  global_obj.server_to_sEclss_queue))
                                global_obj.sEclss_thread.start()

                                # Check that the telemetry thread has started, then send success
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
                                                               'channel_layer': self.channel_layer,
                                                               'channel_name': self.channel_name})
                                # If not working then stop at thread and send back error
                                else:
                                    global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'real_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Real AT Thread but failure to start real'
                                                       'telemetry thread. Real AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If sEclss at thread does not start then don't start real telemetry and send back error
                    else:
                        self.send(json.dumps({
                            'type': 'real_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting real at thread. Real telemetry was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))

        elif content.get('type') == 'start_hera_telemetry':
            # Check if sEclss at thread is not initialized then initialize it and handle sEclss thread
            if global_obj.hera_at_thread is None:
                # Anomaly detection thread initialization for real telemetry
                global_obj.hera_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                             name="Hera AT Thread",
                                                             args=(global_obj.hub_to_hera_at_queue,
                                                                   global_obj.hera_at_to_hub_queue,))
                global_obj.hera_at_thread.start()

                # Check that the anomaly detection thread is working then check sEclss thread
                if global_obj.hera_at_thread.is_alive():
                    print("Hera AT Thread started.")
                    # Check if sEclss thread has not been initialized, then initialize it
                    if global_obj.hera_thread is None:
                        # Simulator thread initialization
                        global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                  name="Hera Telemetry Thread",
                                                                  args=(global_obj.hera_to_hub_queue,
                                                                        global_obj.hub_to_hera_queue,
                                                                        global_obj.server_to_hera_queue))
                        global_obj.hera_thread.start()

                        # Check that the telemetry thread has started, then send success
                        if global_obj.hera_thread.is_alive():
                            print("Hera telemetry started.")
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success starting hera telemetry and hera AT thread.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If not working then stop at thread and send back error
                        else:
                            global_obj.hub_to_hera_at_queue.put({'type': 'stop'})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Success starting Hera AT Thread but failure to start hera'
                                               'telemetry thread. Real AT Thread stopped. Try again.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If sEclss thread has been initialized then handle if it alive or not
                    else:
                        # If it is alive then join it
                        if global_obj.hera_thread.is_alive():
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'already_running',
                                    'message': 'Success starting hera at thread and real telemetry was'
                                               ' already running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If it is not alive then reinitialize it
                        else:
                            # Simulator thread initialization
                            global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                      name="Hera Telemetry Thread",
                                                                      args=(global_obj.hera_to_hub_queue,
                                                                            global_obj.hub_to_hera_queue,
                                                                            global_obj.server_to_hera_queue))
                            global_obj.hera_thread.start()

                            # Check that the telemetry thread has started, then send success
                            if global_obj.hera_thread.is_alive():
                                print("Hera telemetry started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting hera telemetry and hera AT thread.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_hera_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Hera AT Thread but failure to start hera'
                                                   'telemetry thread. Real AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                # If sEclss at thread does not start then don't start real telemetry and send back error
                else:
                    self.send(json.dumps({
                        'type': 'hera_telemetry_response',
                        'content': {
                            'status': 'error',
                            'message': 'Error starting hera at thread. Hera telemetry was not started.',
                            'attempt': content.get('attempt')
                        }
                    }))
            # If sEclss at thread has been initialized then handle if it is alive or not
            else:
                # If alive then check telemetry as normal
                if global_obj.hera_at_thread.is_alive():
                    # Check if sEclss thread has not been initialized, then initialize it
                    if global_obj.hera_thread is None:
                        # Simulator thread initialization
                        global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                  name="Hera Telemetry Thread",
                                                                  args=(global_obj.hera_to_hub_queue,
                                                                        global_obj.hub_to_hera_queue,
                                                                        global_obj.server_to_hera_queue))
                        global_obj.hera_thread.start()

                        # Check that the telemetry thread has started, then send success
                        if global_obj.hera_thread.is_alive():
                            print("Hera telemetry started.")
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success starting hera telemetry and hera AT thread was already'
                                               ' running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If not working then stop at thread and send back error
                        else:
                            global_obj.hub_to_hera_at_queue.put({'type': 'stop'})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': 'Hera at thread was already running but failure to start hera'
                                               'telemetry thread. Hera AT Thread stopped. Try again.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If sEclss thread has been initialized then handle if it alive or not
                    else:
                        # If it is alive then join it
                        if global_obj.hera_thread.is_alive():
                            global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                  "channel_layer": self.channel_layer,
                                                                  "channel_name": self.channel_name})
                            self.send(json.dumps({
                                'type': 'hera_telemetry_response',
                                'content': {
                                    'status': 'already_running',
                                    'message': 'Hera at thread and hera telemetry was'
                                               ' already running.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                            frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                       'channel_layer': self.channel_layer,
                                                       'channel_name': self.channel_name})
                        # If it is not alive then reinitialize it
                        else:
                            # Simulator thread initialization
                            global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                      name="Hera Telemetry Thread",
                                                                      args=(global_obj.hera_to_hub_queue,
                                                                            global_obj.hub_to_hera_queue,
                                                                            global_obj.server_to_hera_queue))
                            global_obj.hera_thread.start()

                            # Check that the telemetry thread has started, then send success
                            if global_obj.hera_thread.is_alive():
                                print("Hera telemetry started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting hera telemetry and hera AT thread was '
                                                   'already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_hera_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'real_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Hera AT Thread was already running but failure to start hera'
                                                   'telemetry thread. Hera AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))

                # If not alive then reinitialize it and handle telemetry normally
                else:
                    # Anomaly detection thread initialization for real telemetry
                    global_obj.hera_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                                 name="Hera AT Thread",
                                                                 args=(global_obj.hub_to_hera_at_queue,
                                                                       global_obj.hera_at_to_hub_queue,))
                    global_obj.hera_at_thread.start()

                    # Check that the anomaly detection thread is working then check sEclss thread
                    if global_obj.hera_at_thread.is_alive():
                        print("Hera AT Thread started.")
                        # Check if sEclss thread has not been initialized, then initialize it
                        if global_obj.hera_thread is None:
                            # Simulator thread initialization
                            global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                      name="Hera Telemetry Thread",
                                                                      args=(global_obj.hera_to_hub_queue,
                                                                            global_obj.hub_to_hera_queue,
                                                                            global_obj.server_to_hera_queue))
                            global_obj.hera_thread.start()

                            # Check that the telemetry thread has started, then send success
                            if global_obj.hera_thread.is_alive():
                                print("Hera telemetry started.")
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success starting hera telemetry and hera AT thread.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If not working then stop at thread and send back error
                            else:
                                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': 'Success starting Hera AT Thread but failure to start hera'
                                                   'telemetry thread. hera AT Thread stopped. Try again.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        # If sEclss thread has been initialized then handle if it alive or not
                        else:
                            # If it is alive then join it
                            if global_obj.hera_thread.is_alive():
                                global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                      "channel_layer": self.channel_layer,
                                                                      "channel_name": self.channel_name})
                                self.send(json.dumps({
                                    'type': 'hera_telemetry_response',
                                    'content': {
                                        'status': 'already_running',
                                        'message': 'Success starting hera at thread and hera telemetry was'
                                                   ' already running.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                                frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                           'channel_layer': self.channel_layer,
                                                           'channel_name': self.channel_name})
                            # If it is not alive then reinitialize it
                            else:
                                # Simulator thread initialization
                                global_obj.hera_thread = threading.Thread(target=handle_eclss_update,
                                                                          name="Hera Telemetry Thread",
                                                                          args=(global_obj.hera_to_hub_queue,
                                                                                global_obj.hub_to_hera_queue,
                                                                                global_obj.server_to_hera_queue))
                                global_obj.hera_thread.start()

                                # Check that the telemetry thread has started, then send success
                                if global_obj.hera_thread.is_alive():
                                    print("Hera telemetry started.")
                                    global_obj.frontend_to_hub_queue.put({"type": "add_to_hera_group",
                                                                          "channel_layer": self.channel_layer,
                                                                          "channel_name": self.channel_name})
                                    self.send(json.dumps({
                                        'type': 'hera_telemetry_response',
                                        'content': {
                                            'status': 'success',
                                            'message': 'Success starting hera telemetry and hera AT thread.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                                    frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params',
                                                               'channel_layer': self.channel_layer,
                                                               'channel_name': self.channel_name})
                                # If not working then stop at thread and send back error
                                else:
                                    global_obj.hub_to_hera_at_queue.put({'type': 'stop'})
                                    self.send(json.dumps({
                                        'type': 'real_telemetry_response',
                                        'content': {
                                            'status': 'error',
                                            'message': 'Success starting Hera AT Thread but failure to start hera'
                                                       'telemetry thread. Hera AT Thread stopped. Try again.',
                                            'attempt': content.get('attempt')
                                        }
                                    }))
                    # If sEclss at thread does not start then don't start real telemetry and send back error
                    else:
                        self.send(json.dumps({
                            'type': 'hera_telemetry_response',
                            'content': {
                                'status': 'error',
                                'message': 'Error starting hera at thread. Hera telemetry was not started.',
                                'attempt': content.get('attempt')
                            }
                        }))

        elif content.get('type') == 'stop_telemetry':
            # Find what telemetry this user is assigned to if any
            if r.sismember('seclss-group-users', self.channel_name) == 1:
                # Check if both telemetry and at thread are not initialized
                if global_obj.sEclss_thread is None and global_obj.sEclss_at_thread is None:
                    r.srem('seclss-group-users', self.channel_name)
                    async_to_sync(self.channel_layer.group_discard)("sEclss-group", self.channel_name)
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to real telemetry but real telemetry and real at threads'
                                       ' are not initialized.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only telemetry thread is not initialized
                elif global_obj.sEclss_thread is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.sEclss_at_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        if r.scard("seclss-group-users") == 0:
                            global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            atMessage = ''
                            global_obj.sEclss_at_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.sEclss_at_thread.is_alive():
                                successful = False
                                atMessage = 'There was an error stopping real at thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping real at thread and real telemetry was not '
                                                   'initialized. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('seclss-group', self.channel_name)
                                r.sadd("seclss-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': atMessage + ' Real telemetry thread was never initialized.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from seclss group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Real telemetry thread was not initialized and real at thread was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only telemetry thread is not initialized
                elif global_obj.sEclss_at_thread is None:
                    # Check if telemetry thread is alive, then kill that thread
                    if global_obj.sEclss_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        if r.scard("seclss-group-users") == 0:
                            global_obj.hub_to_sEclss_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            telemetryMessage = ''
                            global_obj.sEclss_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.sEclss_thread.is_alive():
                                successful = False
                                telemetryMessage = 'There was an error stopping real telemetry thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping real telemetry thread and real at was not '
                                                   'initialized. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('seclss-group', self.channel_name)
                                r.sadd("seclss-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': telemetryMessage + ' Real at thread was never initialized.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from seclss group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Real at thread was not initialized and real telemetry thread was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive then kill both
                    if global_obj.sEclss_thread.is_alive() and global_obj.sEclss_at_thread.is_alive():
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
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping the real telemetry. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('seclss-group', self.channel_name)
                                r.sadd('seclss-group-users', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': sEclssMessage + ' ' + atsEclssMessage,
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from seclss group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only sEclss thread is alive
                    elif global_obj.sEclss_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        if r.scard("seclss-group-users") == 0:
                            global_obj.hub_to_sEclss_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            telemetryMessage = ''
                            global_obj.sEclss_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.sEclss_thread.is_alive():
                                successful = False
                                telemetryMessage = 'There was an error stopping real telemetry thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping real telemetry thread and real at was not '
                                                   'alive. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('seclss-group', self.channel_name)
                                r.sadd("seclss-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': telemetryMessage + ' Real at thread was never alive.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from seclss group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive
                    elif global_obj.sEclss_at_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        if r.scard("seclss-group-users") == 0:
                            global_obj.hub_to_sEclss_at_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            atMessage = ''
                            global_obj.sEclss_at_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.sEclss_at_thread.is_alive():
                                successful = False
                                atMessage = 'There was an error stopping real at thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping real at thread and real telemetry was not '
                                                   'alive. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('seclss-group', self.channel_name)
                                r.sadd("seclss-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': atMessage + ' Real telemetry thread was never alive.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from seclss group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are not running
                    else:
                        async_to_sync(self.channel_layer.group_discard)('seclss-group', self.channel_name)
                        r.srem("seclss-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_real',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Real at thread was not alive and real telemetry thread was '
                                           'already alive. Success removing using from seclss group users. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('hera-group-users', self.channel_name) == 1:
                # Check if both telemetry and at thread are not initialized
                if global_obj.hera_thread is None and global_obj.hera_at_thread is None:
                    r.srem('hera-group-users', self.channel_name)
                    async_to_sync(self.channel_layer.group_discard)("hera-group", self.channel_name)
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to hera telemetry but hera telemetry and hera at threads'
                                       ' are not initialized.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only telemetry thread is not initialized
                elif global_obj.hera_thread is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.hera_at_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        if r.scard("hera-group-users") == 0:
                            global_obj.hub_to_hera_at_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            atMessage = ''
                            global_obj.hera_at_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.hera_at_thread.is_alive():
                                successful = False
                                atMessage = 'There was an error stopping hera at thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping hera at thread and hera telemetry was not '
                                                   'initialized. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('hera-group', self.channel_name)
                                r.sadd("hera-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': atMessage + ' Hera telemetry thread was never initialized.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from hera group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Hera telemetry thread was not initialized and hera at thread was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only telemetry thread is not initialized
                elif global_obj.hera_at_thread is None:
                    # Check if telemetry thread is alive, then kill that thread
                    if global_obj.hera_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        if r.scard("hera-group-users") == 0:
                            global_obj.hub_to_hera_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            telemetryMessage = ''
                            global_obj.hera_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.hera_thread.is_alive():
                                successful = False
                                telemetryMessage = 'There was an error stopping hera telemetry thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping hera telemetry thread and hera at was not '
                                                   'initialized. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('hera-group', self.channel_name)
                                r.sadd("hera-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': telemetryMessage + ' Hera at thread was never initialized.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from hera group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Hera at thread was not initialized and hera telemetry thread was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive then kill both
                    if global_obj.hera_thread.is_alive() and global_obj.hera_at_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        # If no more users are listening to the real telemetry then stop it
                        if r.scard("hera-group-users") == 0:
                            global_obj.frontend_to_hub_queue.put({'type': 'stop_hera_telemetry'})

                            # Ensure that the thread stops
                            successful = True
                            sEclssMessage = ''
                            atsEclssMessage = ''
                            global_obj.hera_thread.join(2.0)
                            if global_obj.hera_thread.is_alive():
                                successful = False
                                sEclssMessage = 'There was an error stopping the hera telemetry thread.'

                            global_obj.hera_at_thread.join(2.0)
                            if global_obj.hera_at_thread.is_alive():
                                successful = False
                                atsEclssMessage = 'There was an error stopping the hera at thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping the hera telemetry. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('hera-group', self.channel_name)
                                r.sadd('hera-group-users', self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': sEclssMessage + ' ' + atsEclssMessage,
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from hera group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only sEclss thread is alive
                    elif global_obj.hera_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        if r.scard("hera-group-users") == 0:
                            global_obj.hub_to_hera_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            telemetryMessage = ''
                            global_obj.hera_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.hera_thread.is_alive():
                                successful = False
                                telemetryMessage = 'There was an error stopping hera telemetry thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping hera telemetry thread and hera at was not '
                                                   'alive. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('hera-group', self.channel_name)
                                r.sadd("hera-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': telemetryMessage + 'Hera at thread was never alive.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from hera group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive
                    elif global_obj.hera_at_thread.is_alive():
                        # Remove user from listening to the real telemetry
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        if r.scard("hera-group-users") == 0:
                            global_obj.hub_to_hera_at_queue.put({'type': 'stop'})

                            # Ensure it gets stopped
                            successful = True
                            atMessage = ''
                            global_obj.hera_at_thread.join(2.0)

                            # If not successful send back error message
                            if global_obj.hera_at_thread.is_alive():
                                successful = False
                                atMessage = 'There was an error stopping hera at thread.'

                            if successful:
                                global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                      'channel_layer': self.channel_layer})
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'success',
                                        'message': 'Success stopping hera at thread and hera telemetry was not '
                                                   'alive. Proceed',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                            else:
                                async_to_sync(self.channel_layer.group_add)('hera-group', self.channel_name)
                                r.sadd("hera-group-users", self.channel_name)
                                self.send(json.dumps({
                                    'type': 'stop_telemetry_response',
                                    'content': {
                                        'status': 'error',
                                        'message': atMessage + ' Hera telemetry thread was never alive.',
                                        'attempt': content.get('attempt')
                                    }
                                }))
                        else:
                            global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                                  'channel_layer': self.channel_layer})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success removing user from hera group users. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are not running
                    else:
                        async_to_sync(self.channel_layer.group_discard)('hera-group', self.channel_name)
                        r.srem("hera-group-users", self.channel_name)
                        global_obj.frontend_to_hub_queue.put({'type': 'remove_channel_layer_from_hera',
                                                              'channel_layer': self.channel_layer})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Hera at thread was not alive and hera telemetry thread was '
                                           'already alive. Success removing using from hera group users. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-one', self.channel_name) == 1:
                # Check if both simulator and at threads are not initialized
                if global_obj.simulator_threads[0] is None and global_obj.simulator_at_threads[0] is None:
                    r.srem('fake-telemetry-one', self.channel_name)
                    if r.scard("fake-telemetry-one") != 0:
                        r.delete("fake-telemetry-one")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry one but the fake at thread 1 and fake '
                                       'telemetry thread 1 are not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only simulator thread is not initialized
                elif global_obj.simulator_threads[0] is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.simulator_at_threads[0].is_alive():
                        global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[0].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[0].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread one.'

                        if successful:
                            r.srem('fake-telemetry-one', self.channel_name)
                            if r.scard("fake-telemetry-one") != 0:
                                r.delete("fake-telemetry-one")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 1 and fake telemetry 1 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 1 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-one', self.channel_name)
                        if r.scard("fake-telemetry-one") != 0:
                            r.delete("fake-telemetry-one")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry 1 thread was not initialized and fake at thread 1 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only at thread is not initialized
                elif global_obj.simulator_at_threads[0] is None:
                    # Check if simulator thread is alive, then kill that thread
                    if global_obj.simulator_threads[0].is_alive():
                        global_obj.hub_to_simulator_queues[0].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[0].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[0].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread one.'

                        if successful:
                            r.srem('fake-telemetry-one', self.channel_name)
                            if r.scard("fake-telemetry-one") != 0:
                                r.delete("fake-telemetry-one")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 1 and fake at 1 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 1 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-one', self.channel_name)
                        if r.scard("fake-telemetry-one") != 0:
                            r.delete("fake-telemetry-one")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake at thread 1 thread was not initialized and fake telemetry 1 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive, then kill both
                    if global_obj.simulator_threads[0].is_alive and global_obj.simulator_at_threads[0].is_alive():
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
                            if r.scard("fake-telemetry-one") != 0:
                                r.delete("fake-telemetry-one")
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
                    # Check if only simulator thread is alive, then only kill simulator thread
                    elif global_obj.simulator_threads[0].is_alive():
                        global_obj.hub_to_simulator_queues[0].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[0].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[0].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread one.'

                        if successful:
                            r.srem('fake-telemetry-one', self.channel_name)
                            if r.scard("fake-telemetry-one") != 0:
                                r.delete("fake-telemetry-one")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 1 and fake at 1 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 1 thread was alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive, then only kill at thread
                    elif global_obj.simulator_at_threads[0].is_alive():
                        global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[0].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[0].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread one.'

                        if successful:
                            r.srem('fake-telemetry-one', self.channel_name)
                            if r.scard("fake-telemetry-one") != 0:
                                r.delete("fake-telemetry-one")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 1 and fake telemetry 1 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 1 thread was never alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are dead then said back already killed message
                    else:
                        r.srem('fake-telemetry-one', self.channel_name)
                        if r.scard("fake-telemetry-one") != 0:
                            r.delete("fake-telemetry-one")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_one'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry thread 1 and fake at thread 1 were both dead. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-two', self.channel_name) == 1:
                # Check if both simulator and at threads are not initialized
                if global_obj.simulator_threads[1] is None and global_obj.simulator_at_threads[1] is None:
                    r.srem('fake-telemetry-two', self.channel_name)
                    if r.scard("fake-telemetry-two") != 0:
                        r.delete("fake-telemetry-two")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry two but the fake at thread 2 and fake '
                                       'telemetry thread 2 are not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only simulator thread is not initialized
                elif global_obj.simulator_threads[1] is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.simulator_at_threads[1].is_alive():
                        global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[1].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[1].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread two.'

                        if successful:
                            r.srem('fake-telemetry-two', self.channel_name)
                            if r.scard("fake-telemetry-two") != 0:
                                r.delete("fake-telemetry-two")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 2 and fake telemetry 2 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 2 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-two', self.channel_name)
                        if r.scard("fake-telemetry-two") != 0:
                            r.delete("fake-telemetry-two")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry 2 thread was not initialized and fake at thread 2 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only at thread is not initialized
                elif global_obj.simulator_at_threads[1] is None:
                    # Check if simulator thread is alive, then kill that thread
                    if global_obj.simulator_threads[1].is_alive():
                        global_obj.hub_to_simulator_queues[1].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[1].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[1].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread two.'

                        if successful:
                            r.srem('fake-telemetry-two', self.channel_name)
                            if r.scard("fake-telemetry-two") != 0:
                                r.delete("fake-telemetry-two")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 2 and fake at 2 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 2 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-two', self.channel_name)
                        if r.scard("fake-telemetry-two") != 0:
                            r.delete("fake-telemetry-two")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake at thread 2 thread was not initialized and fake telemetry 2 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive, then kill both
                    if global_obj.simulator_threads[1].is_alive and global_obj.simulator_at_threads[1].is_alive():
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
                            if r.scard("fake-telemetry-two") != 0:
                                r.delete("fake-telemetry-two")
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
                    # Check if only simulator thread is alive, then only kill simulator thread
                    elif global_obj.simulator_threads[1].is_alive():
                        global_obj.hub_to_simulator_queues[1].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[1].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[1].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread two.'

                        if successful:
                            r.srem('fake-telemetry-two', self.channel_name)
                            if r.scard("fake-telemetry-two") != 0:
                                r.delete("fake-telemetry-two")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 2 and fake at 2 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 2 thread was alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive, then only kill at thread
                    elif global_obj.simulator_at_threads[1].is_alive():
                        global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[1].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[1].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread two.'

                        if successful:
                            r.srem('fake-telemetry-two', self.channel_name)
                            if r.scard("fake-telemetry-two") != 0:
                                r.delete("fake-telemetry-two")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 2 and fake telemetry 2 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 2 thread was never alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are dead then said back already killed message
                    else:
                        r.srem('fake-telemetry-two', self.channel_name)
                        if r.scard("fake-telemetry-two") != 0:
                            r.delete("fake-telemetry-two")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_two'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry thread 2 and fake at thread 2 were both dead. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-three', self.channel_name) == 1:
                # Check if both simulator and at threads are not initialized
                if global_obj.simulator_threads[2] is None and global_obj.simulator_at_threads[2] is None:
                    r.srem('fake-telemetry-three', self.channel_name)
                    if r.scard("fake-telemetry-three") != 0:
                        r.delete("fake-telemetry-three")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry three but the fake at thread 3 and fake '
                                       'telemetry thread 3 are not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only simulator thread is not initialized
                elif global_obj.simulator_threads[2] is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.simulator_at_threads[2].is_alive():
                        global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[2].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[2].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread three.'

                        if successful:
                            r.srem('fake-telemetry-three', self.channel_name)
                            if r.scard("fake-telemetry-three") != 0:
                                r.delete("fake-telemetry-three")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 3 and fake telemetry 3 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 3 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-three', self.channel_name)
                        if r.scard("fake-telemetry-three") != 0:
                            r.delete("fake-telemetry-three")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry 3 thread was not initialized and fake at thread 3 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only at thread is not initialized
                elif global_obj.simulator_at_threads[2] is None:
                    # Check if simulator thread is alive, then kill that thread
                    if global_obj.simulator_threads[2].is_alive():
                        global_obj.hub_to_simulator_queues[2].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[2].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[2].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread three.'

                        if successful:
                            r.srem('fake-telemetry-three', self.channel_name)
                            if r.scard("fake-telemetry-three") != 0:
                                r.delete("fake-telemetry-three")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 3 and fake at 3 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 3 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-three', self.channel_name)
                        if r.scard("fake-telemetry-three") != 0:
                            r.delete("fake-telemetry-three")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake at thread 3 thread was not initialized and fake telemetry 3 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive, then kill both
                    if global_obj.simulator_threads[2].is_alive and global_obj.simulator_at_threads[2].is_alive():
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_three'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        atSimulatorMessage = ''
                        global_obj.simulator_threads[2].join(2.0)
                        if global_obj.simulator_threads[2].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake telemetry thread three.'

                        global_obj.simulator_at_threads[2].join(2.0)
                        if global_obj.simulator_at_threads[2].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread three.'

                        if successful:
                            r.srem('fake-telemetry-three', self.channel_name)
                            if r.scard("fake-telemetry-three") != 0:
                                r.delete("fake-telemetry-three")
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry three. Proceed',
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
                    # Check if only simulator thread is alive, then only kill simulator thread
                    elif global_obj.simulator_threads[2].is_alive():
                        global_obj.hub_to_simulator_queues[2].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[2].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[2].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread three.'

                        if successful:
                            r.srem('fake-telemetry-three', self.channel_name)
                            if r.scard("fake-telemetry-three") != 0:
                                r.delete("fake-telemetry-three")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 3 and fake at 3 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 3 thread was alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive, then only kill at thread
                    elif global_obj.simulator_at_threads[2].is_alive():
                        global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[2].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[2].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread three.'

                        if successful:
                            r.srem('fake-telemetry-three', self.channel_name)
                            if r.scard("fake-telemetry-three") != 0:
                                r.delete("fake-telemetry-three")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 3 and fake telemetry 3 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 3 thread was never alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are dead then said back already killed message
                    else:
                        r.srem('fake-telemetry-three', self.channel_name)
                        if r.scard("fake-telemetry-three") != 0:
                            r.delete("fake-telemetry-three")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_three'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry thread 3 and fake at thread 3 were both dead. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
            elif r.sismember('fake-telemetry-four', self.channel_name) == 1:
                # Check if both simulator and at threads are not initialized
                if global_obj.simulator_threads[3] is None and global_obj.simulator_at_threads[3] is None:
                    r.srem('fake-telemetry-four', self.channel_name)
                    if r.scard("fake-telemetry-four") != 0:
                        r.delete("fake-telemetry-four")
                    global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                    self.send(json.dumps({
                        'type': 'stop_telemetry_response',
                        'content': {
                            'status': 'success',
                            'message': 'This user is assigned to telemetry one but the fake at thread 4 and fake '
                                       'telemetry thread 4 are not running currently.',
                            'attempt': content.get('attempt')
                        }
                    }))
                # Check if only simulator thread is not initialized
                elif global_obj.simulator_threads[3] is None:
                    # Check if at thread is alive, then kill that thread
                    if global_obj.simulator_at_threads[3].is_alive():
                        global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[3].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[3].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread four.'

                        if successful:
                            r.srem('fake-telemetry-four', self.channel_name)
                            if r.scard("fake-telemetry-four") != 0:
                                r.delete("fake-telemetry-four")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 4 and fake telemetry 4 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 4 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-four', self.channel_name)
                        if r.scard("fake-telemetry-four") != 0:
                            r.delete("fake-telemetry-four")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry 4 thread was not initialized and fake at thread 4 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if only at thread is not initialized
                elif global_obj.simulator_at_threads[3] is None:
                    # Check if simulator thread is alive, then kill that thread
                    if global_obj.simulator_threads[3].is_alive():
                        global_obj.hub_to_simulator_queues[3].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[3].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[3].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread four.'

                        if successful:
                            r.srem('fake-telemetry-four', self.channel_name)
                            if r.scard("fake-telemetry-four") != 0:
                                r.delete("fake-telemetry-four")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 4 and fake at 4 was not '
                                               'initialized. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 4 thread was never initialized.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # If it is not alive then it is already stopped, send back success
                    else:
                        r.srem('fake-telemetry-four', self.channel_name)
                        if r.scard("fake-telemetry-four") != 0:
                            r.delete("fake-telemetry-four")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake at thread 4 thread was not initialized and fake telemetry 4 was '
                                           'already killed. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
                # Check if both have been initialized
                else:
                    # Check if both are alive, then kill both
                    if global_obj.simulator_threads[3].is_alive and global_obj.simulator_at_threads[3].is_alive():
                        global_obj.frontend_to_hub_queue.put({'type': 'stop_fake_telemetry_four'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        atSimulatorMessage = ''
                        global_obj.simulator_threads[3].join(2.0)
                        if global_obj.simulator_threads[3].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake telemetry thread four.'

                        global_obj.simulator_at_threads[3].join(2.0)
                        if global_obj.simulator_at_threads[3].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread four.'

                        if successful:
                            r.srem('fake-telemetry-four', self.channel_name)
                            if r.scard("fake-telemetry-four") != 0:
                                r.delete("fake-telemetry-four")
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry four. Proceed',
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
                    # Check if only simulator thread is alive, then only kill simulator thread
                    elif global_obj.simulator_threads[3].is_alive():
                        global_obj.hub_to_simulator_queues[3].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        simulatorMessage = ''
                        global_obj.simulator_threads[3].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_threads[3].is_alive():
                            successful = False
                            simulatorMessage = 'There was an error stopping fake simulator thread four.'

                        if successful:
                            r.srem('fake-telemetry-four', self.channel_name)
                            if r.scard("fake-telemetry-four") != 0:
                                r.delete("fake-telemetry-four")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake telemetry thread 4 and fake at 4 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': simulatorMessage + ' Fake telemetry 4 thread was alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if only at thread is alive, then only kill at thread
                    elif global_obj.simulator_at_threads[3].is_alive():
                        global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop'})

                        # Ensure it gets stopped
                        successful = True
                        atSimulatorMessage = ''
                        global_obj.simulator_at_threads[3].join(2.0)

                        # If not successful send back error message
                        if global_obj.simulator_at_threads[3].is_alive():
                            successful = False
                            atSimulatorMessage = 'There was an error stopping fake at thread four.'

                        if successful:
                            r.srem('fake-telemetry-four', self.channel_name)
                            if r.scard("fake-telemetry-four") != 0:
                                r.delete("fake-telemetry-four")
                            global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'success',
                                    'message': 'Success stopping fake at thread 4 and fake telemetry 4 was not '
                                               'alive. Proceed',
                                    'attempt': content.get('attempt')
                                }
                            }))
                        else:
                            self.send(json.dumps({
                                'type': 'stop_telemetry_response',
                                'content': {
                                    'status': 'error',
                                    'message': atSimulatorMessage + ' Fake telemetry 4 thread was never alive.',
                                    'attempt': content.get('attempt')
                                }
                            }))
                    # Check if both are dead then said back already killed message
                    else:
                        r.srem('fake-telemetry-four', self.channel_name)
                        if r.scard("fake-telemetry-four") != 0:
                            r.delete("fake-telemetry-four")
                        global_obj.frontend_to_hub_queue.put({'type': 'unassign_fake_telemetry_four'})
                        self.send(json.dumps({
                            'type': 'stop_telemetry_response',
                            'content': {
                                'status': 'success',
                                'message': 'Fake telemetry thread 4 and fake at thread 4 were both dead. Proceed',
                                'attempt': content.get('attempt')
                            }
                        }))
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
                frontend_to_hub_queue.put({'type': 'get_real_telemetry_params', 'channel_layer': self.channel_layer,
                                           'channel_name': self.channel_name})
            elif r.sismember('hera-group-users', self.channel_name) == 1:
                frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params', 'channel_layer': self.channel_layer,
                                           'channel_name': self.channel_name})
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

        elif content.get('msg_type') == 'get_hera_telemetry_params':
            frontend_to_hub_queue.put({'type': 'get_hera_telemetry_params'})

        elif content.get('msg_type') == 'get_fake_telemetry_params':
            frontend_to_hub_queue.put({'type': 'get_fake_telemetry_params', 'channel_name': self.channel_name})

        elif content.get('type') == 'ping':
            signal = {'type': 'ping', 'channel_name': self.channel_name}
            frontend_to_hub_queue.put(signal)

    def hub_thread_response(self, event):
        self.send(json.dumps(event))

    def stop_telemetry_response(self, event):
        self.send(json.dumps(event))

    def fake_telemetry_response(self, event):
        self.send(json.dumps(event))

    def real_telemetry_response(self, event):
        self.send(json.dumps(event))

    def hera_telemetry_response(self, event):
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

    def turn_off_alarms(self, event):
        self.send(json.dumps(event))
