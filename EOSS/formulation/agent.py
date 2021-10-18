from EOSS.vassar.api import VASSARClient
from queue import Queue
import threading
import time

from EOSS.sensitivity.api import SensitivityClient




class FormulationAgent:

    # --> Experiment / User information will be set in the constructor
    def __init__(self, user_info, channel_layer):
        self.user_info = user_info
        self.channel_layer = channel_layer
        self.problem_id = user_info.eosscontext.problem_id
        self.queue = Queue()
        self.sensitivity_client = None
        self.alive_time = 0
        self.thread = None




    """
      _______ _                        _   _____       _             __               
     |__   __| |                      | | |_   _|     | |           / _|              
        | |  | |__  _ __ ___  __ _  __| |   | |  _ __ | |_ ___ _ __| |_ __ _  ___ ___ 
        | |  | '_ \| '__/ _ \/ _` |/ _` |   | | | '_ \| __/ _ \ '__|  _/ _` |/ __/ _ \
        | |  | | | | | |  __/ (_| | (_| |  _| |_| | | | ||  __/ |  | || (_| | (_|  __/
        |_|  |_| |_|_|  \___|\__,_|\__,_| |_____|_| |_|\__\___|_|  |_| \__,_|\___\___|                                                                             
    """

    def start(self):
        self.thread = threading.Thread(target=self.agent)
        self.thread.start()
        return self

    def stop(self):
        self.queue.put("stop")
        self.thread.join()
        print("--> FORMULATION THREAD JOINED")

    def formulation_change(self, instChange, orbChange, stakeChange, objChange):
        return 0




    """
      _______ _                        _   ______                _   _                 
     |__   __| |                      | | |  ____|              | | (_)                
        | |  | |__  _ __ ___  __ _  __| | | |__ _   _ _ __   ___| |_ _  ___  _ __  ___ 
        | |  | '_ \| '__/ _ \/ _` |/ _` | |  __| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
        | |  | | | | | |  __/ (_| | (_| | | |  | |_| | | | | (__| |_| | (_) | | | \__ \
        |_|  |_| |_|_|  \___|\__,_|\__,_| |_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
    """

    def print_start(self):
        print('\n----- Formulation Thread -----')
        print('----> session:', self.user_info.session)
        print('----> user:', self.user_info.user)
        print('----> channel name:', self.channel_layer)
        print('--------- Problem ID', self.problem_id)
        print('--------------------------', '\n')

    def record_loop(self, sleep_sec=1):
        time.sleep(sleep_sec)
        print("--> ", self.alive_time)
        self.alive_time += 1

    def process_queue_msg(self, block=False):
        if not self.queue.empty():
            msg = self.queue.get(block=block)
            print('--> AGENT MESSAGE', msg)
            return msg
        return None

    """                        _     _______ _                        _ 
         /\                   | |   |__   __| |                      | |
        /  \   __ _  ___ _ __ | |_     | |  | |__  _ __ ___  __ _  __| |
       / /\ \ / _` |/ _ \ '_ \| __|    | |  | '_ \| '__/ _ \/ _` |/ _` |
      / ____ \ (_| |  __/ | | | |_     | |  | | | | | |  __/ (_| | (_| |
     /_/    \_\__, |\___|_| |_|\__|    |_|  |_| |_|_|  \___|\__,_|\__,_|
               __/ |                                                    
              |___/                                                     
    """

    def agent(self):
        self.print_start()
        self.sensitivity_client = SensitivityClient(self.user_info)

        continue_running = True

        # 1. Calculate sensitivities for initial problem formulation
        self.sensitivity_client.calculate_sensitivities()


        while continue_running:
            self.record_loop(sleep_sec=2)

            # --> 1. Process queue messages
            msg = self.process_queue_msg()
            if msg == 'stop':
                continue_running = False
                break



        self.sensitivity_client.shutdown()
        return 0






