from queue import Queue

# Match username to channel layer and name
userChannelNames = {}
userChannelLayers = {}

# Initialize threads
hub_thread = None
sEclss_thread = None
sEclss_at_thread = None
hera_thread = None
hera_at_thread = None
simulator_thread_one = None
simulator_thread_two = None
simulator_thread_three = None
simulator_thread_four = None
simulator_threads = [simulator_thread_one, simulator_thread_two, simulator_thread_three, simulator_thread_four]
simulator_at_thread_one = None
simulator_at_thread_two = None
simulator_at_thread_three = None
simulator_at_thread_four = None
simulator_at_threads = [simulator_at_thread_one, simulator_at_thread_two, simulator_at_thread_three,
                        simulator_at_thread_four]

# Initialize queues
frontend_to_hub_queue = Queue()
sEclss_to_hub_queue = Queue()
hub_to_sEclss_queue = Queue()
hub_to_sEclss_at_queue = Queue()
sEclss_at_to_hub_queue = Queue()
server_to_sEclss_queue = Queue(maxsize=3600)
hera_to_hub_queue = Queue()
hub_to_hera_queue = Queue()
hub_to_hera_at_queue = Queue()
hera_at_to_hub_queue = Queue()
server_to_hera_queue = Queue(maxsize=3600)
simulator_to_hub_queue_one = Queue()
simulator_to_hub_queue_two = Queue()
simulator_to_hub_queue_three = Queue()
simulator_to_hub_queue_four = Queue()
simulator_to_hub_queues = [simulator_to_hub_queue_one, simulator_to_hub_queue_two, simulator_to_hub_queue_three,
                           simulator_to_hub_queue_four]
hub_to_simulator_queue_one = Queue()
hub_to_simulator_queue_two = Queue()
hub_to_simulator_queue_three = Queue()
hub_to_simulator_queue_four = Queue()
hub_to_simulator_queues = [hub_to_simulator_queue_one, hub_to_simulator_queue_two, hub_to_simulator_queue_three,
                           hub_to_simulator_queue_four]
hub_to_simulator_at_queue_one = Queue()
hub_to_simulator_at_queue_two = Queue()
hub_to_simulator_at_queue_three = Queue()
hub_to_simulator_at_queue_four = Queue()
hub_to_simulator_at_queues = [hub_to_simulator_at_queue_one, hub_to_simulator_at_queue_two, hub_to_simulator_at_queue_three,
                              hub_to_simulator_at_queue_four]
simulator_at_to_hub_queue_one = Queue()
simulator_at_to_hub_queue_two = Queue()
simulator_at_to_hub_queue_three = Queue()
simulator_at_to_hub_queue_four = Queue()
simulator_at_to_hub_queues = [simulator_at_to_hub_queue_one, simulator_at_to_hub_queue_two, simulator_at_to_hub_queue_three,
                              simulator_at_to_hub_queue_four]

