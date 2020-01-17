from queue import Queue

frontend_to_hub_queue = Queue()
simulator_to_hub_queue = Queue()
hub_to_simulator_queue = Queue()
hub_to_at_queue = Queue()
at_to_hub_queue = Queue()

global_hub_is_alive = False
