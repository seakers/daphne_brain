from queue import Queue

frontend_to_hub_queue = Queue()
simulator_to_hub_queue = Queue()
hub_to_simulator_queue = Queue()
hub_to_ad_queue = Queue()
ad_to_diagnosis_queue = Queue()
diagnosis_to_hub_queue = Queue()
