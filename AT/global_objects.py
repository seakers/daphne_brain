from queue import Queue
from django.contrib.auth.models import Group

# Initialize group for real telemetry group, variable to keep track of number in the group
sEclss_group, created = Group.objects.get_or_create(name="sEclss_group")
users_in_sEclss_group = 0

# Initialize threads
hub_thread = None
sEclss_thread = None
Simulator_thread = None
sEclss_at_thread = None
Simulator_at_thread = None

# Initialize queues
frontend_to_hub_queue = Queue()
sEclss_to_hub_queue = Queue()
Simulator_to_hub_queue = Queue()
hub_to_sEclss_queue = Queue()
hub_to_Simulator_queue = Queue()
hub_to_sEclss_at_queue = Queue()
hub_to_Simulator_at_queue = Queue()
sEclss_at_to_hub_queue = Queue()
Simulator_at_to_hub_queue = Queue()
server_to_sEclss_queue = Queue(maxsize=3600)
