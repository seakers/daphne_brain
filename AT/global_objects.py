from queue import Queue


hub_thread = None
simulator_thread = None
at_thread = None


frontend_to_hub_queue = Queue()
simulator_to_hub_queue = Queue()
hub_to_simulator_queue = Queue()
hub_to_at_queue = Queue()
at_to_hub_queue = Queue()
server_to_simulator_queue = Queue(maxsize=3600)
