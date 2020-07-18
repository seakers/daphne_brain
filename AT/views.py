import json
import threading

import redis
from rest_framework.response import Response
from rest_framework.views import APIView
from AT.automated_at_routines.at_routine import anomaly_treatment_routine
from AT.automated_at_routines.hub_routine import hub_routine
from AT.simulator_thread.simulator_routine_by_false_eclss import simulate_by_dummy_eclss
from AT.simulator_thread.simulator_routine_by_real_eclss import handle_eclss_update
from AT.neo4j_queries.query_functions import diagnose_symptoms_by_intersection_with_anomaly
from AT.neo4j_queries.query_functions import retrieve_all_anomalies
from AT.neo4j_queries.query_functions import retrieve_procedures_from_anomaly
from AT.neo4j_queries.query_functions import retrieve_fancy_steps_from_procedure
from AT.neo4j_queries.query_functions import retrieve_objective_from_procedure
from AT.neo4j_queries.query_functions import retrieve_equipment_from_procedure
from AT.neo4j_queries.query_functions import retrieve_figures_from_procedure
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information

# THREADS + QUEUES
import AT.global_objects as global_obj


def check_threads_status():
    hub_is_alive = global_obj.hub_thread.is_alive()
    sEclss_is_alive = global_obj.sEclss_thread.is_alive()
    sim_is_alive_one = global_obj.simulator_threads[0].is_alive()
    sim_is_alive_two = global_obj.simulator_threads[1].is_alive()
    sim_is_alive_three = global_obj.simulator_threads[2].is_alive()
    sim_is_alive_four = global_obj.simulator_threads[3].is_alive()
    sEclss_at_is_alive = global_obj.sEclss_at_thread.is_alive()
    sim_at_is_alive_one = global_obj.simulator_at_threads[0].is_alive()
    sim_at_is_alive_two = global_obj.simulator_at_threads[1].is_alive()
    sim_at_is_alive_three = global_obj.simulator_at_threads[2].is_alive()
    sim_at_is_alive_four = global_obj.simulator_at_threads[3].is_alive()

    # Check if all the treads are in a healthy status. Display a message according to the result.
    if hub_is_alive and sEclss_is_alive and sim_is_alive_one and sim_is_alive_two and sim_is_alive_three \
            and sim_is_alive_four and sEclss_at_is_alive and sim_at_is_alive_one and sim_at_is_alive_two \
            and sim_at_is_alive_three and sim_at_is_alive_four:
        print('**********\nAll AT threads started successfully.\n**********')
    else:
        print('**********')
        if not hub_is_alive:
            print('Hub thread start failure.')
        if not sEclss_is_alive:
            print('sEclss thread start failure.')
        if not sim_is_alive_one:
            print('Simulator thread 1 start failure.')
        if not sim_is_alive_two:
            print('Simulator thread 2 start failure.')
        if not sim_is_alive_three:
            print('Simulator thread 3 start failure.')
        if not sim_is_alive_four:
            print('Simulator thread 4 start failure.')
        if not sEclss_at_is_alive:
            print('Anomaly treatment thread for sEclss start failure.')
        if not sim_at_is_alive_one:
            print('Anomaly treatment thread 1 for the simulator thread start failure.')
        if not sim_at_is_alive_two:
            print('Anomaly treatment thread 2 for the simulator thread start failure.')
        if not sim_at_is_alive_three:
            print('Anomaly treatment thread 3 for the simulator thread start failure.')
        if not sim_at_is_alive_four:
            print('Anomaly treatment thread 4 for the simulator thread start failure.')
        print('**********')
    return


def convert_threshold_tag_to_neo4j_relationship(threshold_tag):
    relationship = ''
    if threshold_tag == 'LCL' or threshold_tag == 'LWL':
        relationship = 'Exceeds_LWL'
    elif threshold_tag == 'UCL' or threshold_tag == 'UWL':
        relationship = 'Exceeds_UWL'
    else:
        print('Invalid threshold tag')
        raise

    return relationship


class SimulateTelemetry(APIView):
    def post(self, request):
        # Get the user information and channel layer
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_layer = get_channel_layer()
        channel_name = user_info.channel_name

        # Check if all threads are full
        if global_obj.simulator_threads[0] is not None and global_obj.simulator_threads[1] is not None and \
                global_obj.simulator_threads[2] is not None and global_obj.simulator_threads[3] is not None:
            return Response({
                "status": "already_running",
                "message": "All fake telemetry threads are in use. This is okay if there are four users"
                           "in the tutorial currently but no one users can get a fake telemetry."
            })

        # If threads aren't full then find the first available empty thread
        # Simulator thread initialization
        if global_obj.simulator_threads[0] is None:
            global_obj.simulator_threads[0] = threading.Thread(target=simulate_by_dummy_eclss,
                                                               name="Fake Telemetry Thread 1",
                                                               args=(global_obj.simulator_to_hub_queues[0],
                                                                     global_obj.hub_to_simulator_queues[0]))
            global_obj.simulator_threads[0].start()

            # Thread status check
            if global_obj.simulator_threads[0].is_alive():
                print("Fake Telemetry Thread 1 started.")
                r = redis.Redis()
                r.sadd("fake_telemetry_one", channel_name)
                print(f"Channel {channel_name} assigned to fake telemetry 1")
                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_one", "channel_layer": channel_layer,
                                                      "channel_name": channel_name})
                return Response({
                    "status": "success",
                    "message": "Success starting Fake Telemetry Thread 1. Proceed with initialization."
                })

            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Fake Telemetry Thread 1. Try again."
                })
        elif global_obj.simulator_threads[1] is None:
            global_obj.simulator_threads[1] = threading.Thread(target=simulate_by_dummy_eclss,
                                                               name="Fake Telemetry Thread 2",
                                                               args=(global_obj.simulator_to_hub_queues[1],
                                                                     global_obj.hub_to_simulator_queues[1]))
            global_obj.simulator_threads[1].start()

            # Thread status check
            if global_obj.simulator_threads[1].is_alive():
                print("Fake Telemetry Thread 2 started.")
                r = redis.Redis()
                r.sadd("fake_telemetry_two", channel_name)
                print(f"Channel {channel_name} assigned to fake telemetry 2")
                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_two", "channel_layer": channel_layer,
                                                      "channel_name": channel_name})
                return Response({
                    "status": "success",
                    "message": "Success starting Fake Telemetry Thread 2. Proceed with initialization."
                })

            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Fake Telemetry Thread 2. Try again."
                })
        elif global_obj.simulator_threads[2] is None:
            global_obj.simulator_threads[2] = threading.Thread(target=simulate_by_dummy_eclss,
                                                               name="Fake Telemetry Thread 3",
                                                               args=(global_obj.simulator_to_hub_queues[2],
                                                                     global_obj.hub_to_simulator_queues[2]))
            global_obj.simulator_threads[2].start()

            # Thread status check
            if global_obj.simulator_threads[2].is_alive():
                print("Fake Telemetry Thread 3 started.")
                r = redis.Redis()
                r.sadd("fake_telemetry_three", channel_name)
                print(f"Channel {channel_name} assigned to fake telemetry 3")
                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_three", "channel_layer": channel_layer,
                                                      "channel_name": channel_name})
                return Response({
                    "status": "success",
                    "message": "Success starting Fake Telemetry Thread 3. Proceed with initialization."
                })

            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Fake Telemetry Thread 3. Try again."
                })
        elif global_obj.simulator_threads[3] is None:
            global_obj.simulator_threads[3] = threading.Thread(target=simulate_by_dummy_eclss,
                                                               name="Fake Telemetry Thread 4",
                                                               args=(global_obj.simulator_to_hub_queues[3],
                                                                     global_obj.hub_to_simulator_queues[3]))
            global_obj.simulator_threads[3].start()

            # Thread status check
            if global_obj.simulator_threads[3].is_alive():
                print("Fake Telemetry Thread 4 started.")
                r = redis.Redis()
                r.sadd("fake_telemetry_four", channel_name)
                print(f"Channel {channel_name} assigned to fake telemetry 4")
                global_obj.frontend_to_hub_queue.put({"type": "add_fake_telemetry_four", "channel_layer": channel_layer,
                                                      "channel_name": channel_name})
                return Response({
                    "status": "success",
                    "message": "Success starting Fake Telemetry Thread 4. Proceed with initialization."
                })

            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Fake Telemetry Thread 4. Try again."
                })

        else:
            return Response({
                "status": "error",
                "message": "User not assigned to fake telemetry but not all were being used."
            })


class StopRealTelemetry(APIView):
    def post(self, request):
        # Get the user information and channel layer
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_layer = get_channel_layer()
        channel_name = user_info.channel_name

        # Check if the real telemetry thread is even running
        if global_obj.sEclss_thread is not None and global_obj.sEclss_thread.is_alive():
            # Check if user is in this group
            r = redis.Redis()
            if r.sismember("seclss-group-users", channel_name) == 1:
                async_to_sync(channel_layer.group_discard)("sEclss_group", channel_name)
                r.srem("seclss-group-users", channel_name)
                # Check if this was the only user on the thread
                if r.scard("seclss-group-users") == 0:
                    signal = {'type': 'stop_real_telemetry', 'content': None}
                    global_obj.frontend_to_hub_queue.put(signal)

                    # Wait 2 seconds for simulator thread to terminate
                    thread_name = global_obj.sEclss_thread.name
                    global_obj.sEclss_thread.join(2.0)
                    if global_obj.sEclss_thread.is_alive():
                        return Response({
                            "status": "error",
                            "message": "The Real Telemetry Thread did not stop in 2 seconds but the user was "
                                       "disconnected from the real telemetry group. Please try again."
                        })
                    else:
                        global_obj.hub_to_sEclss_at_queue.put({'type': 'stop', 'content': ''})
                        return Response({
                            "status": "success",
                            "message": "The " + thread_name + " has stopped correctly and the user was disconnected"
                                                              " from the real telemetry group. Please proceed."
                        })
                else:
                    if r.sismember("seclss-group-users", channel_name) == 1:
                        return Response({
                            "status": "error",
                            "message": "The user was not removed from the real telemetry group. Please try again."
                        })
                    else:
                        return Response({
                            "status": "success",
                            "message": "The user was removed from the real telemetry group but there were other users"
                                       "on so the real telemetry thread is continuing to run."
                        })
            else:
                return Response({
                    "status": "success",
                    "message": "This user is not in the real telemetry group."
                })

        else:
            if global_obj.sEclss_thread is not None and global_obj.sEclss_at_thread.is_alive():
                global_obj.hub_to_sEclss_at_queue.put({'type': 'stop', 'content': ''})
            return Response({
                "status": "success",
                "message": "No Real Telemetry Thread was running."
            })


class StopFakeTelemetry(APIView):
    def post(self, request):
        # Get the user information and channel layer
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_name = user_info.channel_name
        r = redis.Redis()

        # Find if the user is on a fake telemetry thread
        if r.sismember("fake_telemetry_one", channel_name) == 1:
            # Only stop fake telemetry if there was a telemetry running
            if global_obj.simulator_threads[0] is not None and global_obj.simulator_threads[0].is_alive():
                signal = {'type': 'stop_fake_telemetry_one', 'content': None}
                global_obj.frontend_to_hub_queue.put(signal)

                # Wait 2 seconds for simulator thread to terminate
                thread_name = global_obj.simulator_threads[0].name
                global_obj.simulator_threads[0].join(2.0)
                if global_obj.simulator_threads[0].is_alive():
                    return Response({
                        "status": "error",
                        "message": "The Fake Telemetry Thread 1 did not stop in 2 seconds. Please try again."
                    })
                else:
                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[0] = None
                    global_obj.simulator_at_threads[0] = None
                    r.srem("fake_telemetry_one", channel_name)
                    return Response({
                        "status": "success",
                        "message": "The " + thread_name + " has stopped correctly. Please proceed."
                    })
            else:
                if global_obj.simulator_threads[0] is not None and global_obj.simulator_at_threads[0].is_alive():
                    global_obj.hub_to_simulator_at_queues[0].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[0] = None
                    global_obj.simulator_at_threads[0] = None
                return Response({
                    "status": "success",
                    "message": "Fake Telemetry Thread 1 was not running."
                })
        elif r.sismember("fake_telemetry_two", channel_name) == 1:
            # Only stop fake telemetry if there was a telemetry running
            if global_obj.simulator_threads[1] is not None and global_obj.simulator_threads[1].is_alive():
                signal = {'type': 'stop_fake_telemetry_two', 'content': None}
                global_obj.frontend_to_hub_queue.put(signal)

                # Wait 2 seconds for simulator thread to terminate
                thread_name = global_obj.simulator_threads[1].name
                global_obj.simulator_threads[1].join(2.0)
                if global_obj.simulator_threads[1].is_alive():
                    return Response({
                        "status": "error",
                        "message": "The Fake Telemetry Thread 2 did not stop in 2 seconds. Please try again."
                    })
                else:
                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[1] = None
                    global_obj.simulator_at_threads[1] = None
                    r.srem("fake_telemetry_two", channel_name)
                    return Response({
                        "status": "success",
                        "message": "The " + thread_name + " has stopped correctly. Please proceed."
                    })
            else:
                if global_obj.simulator_threads[1] is not None and global_obj.simulator_at_threads[1].is_alive():
                    global_obj.hub_to_simulator_at_queues[1].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[1] = None
                    global_obj.simulator_at_threads[1] = None
                return Response({
                    "status": "success",
                    "message": "Fake Telemetry Thread 2 was not running."
                })
        elif r.sismember("fake_telemetry_three", channel_name) == 1:
            # Only stop fake telemetry if there was a telemetry running
            if global_obj.simulator_threads[2] is not None and global_obj.simulator_threads[2].is_alive():
                signal = {'type': 'stop_fake_telemetry_three', 'content': None}
                global_obj.frontend_to_hub_queue.put(signal)

                # Wait 2 seconds for simulator thread to terminate
                thread_name = global_obj.simulator_threads[2].name
                global_obj.simulator_threads[2].join(2.0)
                if global_obj.simulator_threads[2].is_alive():
                    return Response({
                        "status": "error",
                        "message": "The Fake Telemetry Thread 3 did not stop in 2 seconds. Please try again."
                    })
                else:
                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[2] = None
                    global_obj.simulator_at_threads[2] = None
                    r.srem("fake_telemetry_three", channel_name)
                    return Response({
                        "status": "success",
                        "message": "The " + thread_name + " has stopped correctly. Please proceed."
                    })
            else:
                if global_obj.simulator_threads[2] is not None and global_obj.simulator_at_threads[2].is_alive():
                    global_obj.hub_to_simulator_at_queues[2].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[2] = None
                    global_obj.simulator_at_threads[2] = None
                return Response({
                    "status": "success",
                    "message": "Fake Telemetry Thread 3 was not running."
                })
        elif r.sismember("fake_telemetry_four", channel_name) == 1:
            # Only stop fake telemetry if there was a telemetry running
            if global_obj.simulator_threads[3] is not None and global_obj.simulator_threads[3].is_alive():
                signal = {'type': 'stop_fake_telemetry_four', 'content': None}
                global_obj.frontend_to_hub_queue.put(signal)

                # Wait 2 seconds for simulator thread to terminate
                thread_name = global_obj.simulator_threads[3].name
                global_obj.simulator_threads[3].join(2.0)
                if global_obj.simulator_threads[3].is_alive():
                    return Response({
                        "status": "error",
                        "message": "The Fake Telemetry Thread 4 did not stop in 2 seconds. Please try again."
                    })
                else:
                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[3] = None
                    global_obj.simulator_at_threads[3] = None
                    r.srem("fake_telemetry_four", channel_name)
                    return Response({
                        "status": "success",
                        "message": "The " + thread_name + " has stopped correctly. Please proceed."
                    })
            else:
                if global_obj.simulator_threads[3] is not None and global_obj.simulator_at_threads[3].is_alive():
                    global_obj.hub_to_simulator_at_queues[3].put({'type': 'stop', 'content': ''})
                    global_obj.simulator_threads[3] = None
                    global_obj.simulator_at_threads[3] = None
                return Response({
                    "status": "success",
                    "message": "Fake Telemetry Thread 4 was not running."
                })
        else:
            return Response({
                "status": "success",
                "message": "No fake telemetry threads were running or error stopping one."
            })


class StartSeclssFeed(APIView):
    def post(self, request):
        if global_obj.sEclss_thread is not None and global_obj.sEclss_thread.is_alive():
            if global_obj.sEclss_thread.name == "Real Telemetry Thread":
                global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group", "content": None})
                return Response({
                    "status": "already_running",
                    "message": "Real Telemetry Thread was already running, this is fine if someone else is using "
                               "Daphne-AT."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "Real Telemetry Thread has an error. Ensure this thread only involves real"
                               " telemetry. Check for other errors."
                })

        # Simulator thread initialization
        global_obj.sEclss_thread = threading.Thread(target=handle_eclss_update,
                                                    name="Real Telemetry Thread",
                                                    args=(global_obj.sEclss_to_hub_queue,
                                                          global_obj.hub_to_sEclss_queue,
                                                          global_obj.server_to_sEclss_queue))
        global_obj.sEclss_thread.start()

        # Thread status check
        if global_obj.sEclss_thread.is_alive():
            print("Real Telemetry Thread started.")
            global_obj.frontend_to_hub_queue.put({"type": "add_to_sEclss_group", "content": None})
            return Response({
                "status": "success",
                "message": "Success starting Real Telemetry Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Real Telemetry Thread. Try again."
            })


class StartHubThread(APIView):
    def post(self, request):
        if global_obj.hub_thread is not None and global_obj.hub_thread.is_alive():
            return Response({
                "status": "already_running",
                "message": "Hub Thread was already running, this is fine if someone else is using Daphne-AT."
            })

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
                                                       global_obj.simulator_at_to_hub_queues[3],
                                                       request))
        global_obj.hub_thread.start()

        # Thread status check
        if global_obj.hub_thread.is_alive():
            print("Hub Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting Hub Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Hub Thread. Try again."
            })


class StartRealATThread(APIView):
    def post(self, request):
        if global_obj.sEclss_at_thread is not None and global_obj.sEclss_at_thread.is_alive():
            return Response({
                "status": "already_running",
                "message": "Real AT Thread was already running, this is fine if someone else is using Daphne-AT and"
                           " is on the real telemetry feed."
            })

        # Anomaly detection thread initialization
        global_obj.sEclss_at_thread = threading.Thread(target=anomaly_treatment_routine,
                                                       name="Real AT Thread",
                                                       args=(global_obj.hub_to_sEclss_at_queue,
                                                             global_obj.sEclss_at_to_hub_queue,))
        global_obj.sEclss_at_thread.start()

        # Thread status check
        if global_obj.sEclss_at_thread.is_alive():
            print("Real AT Thread started.")
            return Response({
                "status": "success",
                "message": "Success starting Real AT Thread. Proceed with initialization."
            })
        else:
            return Response({
                "status": "error",
                "message": "Error starting Real AT Thread. Try again."
            })


class StartFakeATThread(APIView):
    def post(self, request):
        # Get the user information and channel layer
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        channel_name = user_info.channel_name
        r = redis.Redis()

        if global_obj.simulator_at_threads[0] is not None and global_obj.simulator_at_threads[1] is not None and \
                global_obj.simulator_at_threads[2] is not None and global_obj.simulator_at_threads[3] is not None and \
                global_obj.simulator_at_threads[0].is_alive() and global_obj.simulator_at_threads[1].is_alive() and \
                global_obj.simulator_at_threads[2].is_alive() and global_obj.simulator_at_threads[3].is_alive():
            return Response({
                "status": "already_running",
                "message": "All fake telemetry at threads are in use. This is okay if there are four users"
                           "in the tutorial currently but no one users can get a fake telemetry."
            })

        if r.sismember("fake_telemetry_one", channel_name) == 1:
            # Anomaly detection thread initialization
            global_obj.simulator_at_threads[0] = threading.Thread(target=anomaly_treatment_routine,
                                                                  name="Fake AT Thread 1",
                                                                  args=(global_obj.hub_to_simulator_at_queues[0],
                                                                        global_obj.simulator_at_to_hub_queues[0],))
            global_obj.simulator_at_threads[0].start()

            # Thread status check
            if global_obj.simulator_at_threads[0].is_alive():
                print("Fake AT Thread 1 started.")
                return Response({
                    "status": "success",
                    "message": "Success starting Fake AT 1 Thread. Proceed with initialization."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Real AT Thread 1. Try again."
                })
        elif r.sismember("fake_telemetry_two", channel_name) == 1:
            global_obj.simulator_at_threads[1] = threading.Thread(target=anomaly_treatment_routine,
                                                                  name="Fake AT Thread 2",
                                                                  args=(global_obj.hub_to_simulator_at_queues[1],
                                                                        global_obj.simulator_at_to_hub_queues[1],))
            global_obj.simulator_at_threads[1].start()

            # Thread status check
            if global_obj.simulator_at_threads[1].is_alive():
                print("Fake AT Thread 2 started.")
                return Response({
                    "status": "success",
                    "message": "Success starting Fake AT 2 Thread. Proceed with initialization."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Real AT Thread 2. Try again."
                })
        elif r.sismember("fake_telemetry_three", channel_name) == 1:
            global_obj.simulator_at_threads[2] = threading.Thread(target=anomaly_treatment_routine,
                                                                  name="Fake AT Thread 3",
                                                                  args=(global_obj.hub_to_simulator_at_queues[2],
                                                                        global_obj.simulator_at_to_hub_queues[2],))
            global_obj.simulator_at_threads[2].start()

            # Thread status check
            if global_obj.simulator_at_threads[2].is_alive():
                print("Fake AT Thread 3 started.")
                return Response({
                    "status": "success",
                    "message": "Success starting Fake AT 3 Thread. Proceed with initialization."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Real AT Thread 3. Try again."
                })
        elif r.sismember("fake_telemetry_four", channel_name) == 1:
            # Anomaly detection thread initialization
            global_obj.simulator_at_threads[3] = threading.Thread(target=anomaly_treatment_routine,
                                                                  name="Fake AT Thread 4",
                                                                  args=(global_obj.hub_to_simulator_at_queues[3],
                                                                        global_obj.simulator_at_to_hub_queues[3],))
            global_obj.simulator_at_threads[3].start()

            # Thread status check
            if global_obj.simulator_at_threads[3].is_alive():
                print("Fake AT Thread 4 started.")
                return Response({
                    "status": "success",
                    "message": "Success starting Fake AT 4 Thread. Proceed with initialization."
                })
            else:
                return Response({
                    "status": "error",
                    "message": "Error starting Real AT Thread 4. Try again."
                })
        else:
            return Response({
                "status": "error",
                "message": "User not assigned to at thread even though not all were full."
            })


class SeclssFeed(APIView):
    def post(self, request):
        if 'parameters' in request.data:
            sensor_data = request.data['parameters']
            # print(sensor_data)
            parsed_sensor_data = json.loads(sensor_data)
            if global_obj.sEclss_thread is not None \
                    and global_obj.sEclss_thread.is_alive() \
                    and global_obj.sEclss_thread.name == "Real Telemetry Thread":
                global_obj.server_to_sEclss_queue.put({'type': 'sensor_data', 'content': parsed_sensor_data})
            return Response(parsed_sensor_data)
        else:
            print('ERROR retrieving the sensor data from the ECLSS simulator')
            return Response({
                "status": "error",
                "message": "ERROR retrieving the sensor data from the ECLSS simulator"
            })


class RequestDiagnosis(APIView):
    def post(self, request):
        # Retrieve the symptoms list from the request
        symptoms_list = json.loads(request.data['symptomsList'])

        # Parse the symptoms list to meet the neo4j query function requirements
        parsed_symptoms_list = []
        for item in symptoms_list:
            threshold_tag = item['threshold_tag']
            relationship = convert_threshold_tag_to_neo4j_relationship(threshold_tag)
            symptom = {'measurement': item['measurement'],
                       'display_name': item['display_name'],
                       'relationship': relationship}
            parsed_symptoms_list.append(symptom)

        # Query the neo4j graph (do not delete first line until second one is tested)
        # diagnosis_list = diagnose_symptoms_by_subset_of_anomaly(parsed_symptoms_list)
        diagnosis_list = diagnose_symptoms_by_intersection_with_anomaly(parsed_symptoms_list)

        # Build the diagnosis report and send it to the frontend
        diagnosis_report = {'symptoms_list': symptoms_list, 'diagnosis_list': diagnosis_list}

        return Response(diagnosis_report)


class LoadAllAnomalies(APIView):
    def post(self, request):
        # Query the neo4j graph
        anomaly_list = retrieve_all_anomalies()

        return Response(anomaly_list)


class RetrieveProcedureFromAnomaly(APIView):
    def post(self, request):
        # Retrieve the anomaly name list from the request
        anomaly_name = json.loads(request.data['anomaly_name'])

        # Obtain all the procedures related to the anomaly
        procedure_names = retrieve_procedures_from_anomaly(anomaly_name)

        return Response(procedure_names)


class RetrieveInfoFromProcedure(APIView):
    def post(self, request):
        # Retrieve the procedure name from the request
        procedure_name = json.loads(request.data['procedure_name'])

        # Query the neo4j to retrieve the procedure information
        steps_list = retrieve_fancy_steps_from_procedure(procedure_name)
        objective = retrieve_objective_from_procedure(procedure_name)
        equipment = retrieve_equipment_from_procedure(procedure_name)
        figures = retrieve_figures_from_procedure(procedure_name)

        # Build the output dictionary
        info = {
            'procedureStepsList': steps_list,
            'procedureObjective': objective,
            'procedureEquipment': equipment,
            'procedureFigures': figures,
        }

        return Response(info)
