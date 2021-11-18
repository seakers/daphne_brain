from EOSS.vassar.api import VASSARClient
from queue import Queue
import threading
import time
import json
from datetime import datetime
from asgiref.sync import async_to_sync

from EOSS.sensitivity.api import SensitivityClient
from EOSS.sensitivity.main_effects import MainEffectClient


class FormulationAgent:

    # --> Experiment / User information will be set in the constructor
    def __init__(self, user_info, channel_layer, session, current_objectives):
        self.current_objectives = current_objectives
        self.session = session
        self.data_dir = '/app/daphne/daphne_brain/EOSS/sensitivity/data/'
        self.user_info = user_info
        self.channel_layer = channel_layer
        self.channel_name = self.user_info.channel_name
        self.problem_id = user_info.eosscontext.problem_id
        self.queue = Queue()
        self.sensitivity_client = None
        self.main_effect_client = None
        self.alive_time = 0
        self.thread = None

        self.formulation_start_time = time.time()


        # --> Range Checks
        self.range_1 = False
        self.range_2 = False
        self.range_3 = False
        self.range_4 = False
        self.range_5 = False
        self.range_6 = False




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
        message = {
            'type': 'stop'
        }
        self.queue.put(message)
        self.thread.join()
        print("--> FORMULATION THREAD JOINED")

    def formulation_change(self, instChange, orbChange, stakeChange, objChange, objList):
        self.formulation_start_time = time.time()
        message = {
            'type': 'formulation change',
            'instChange': instChange,
            'orbChange': orbChange,
            'stakeChange': stakeChange,
            'objChange': objChange,
            'objList': objList
        }
        self.queue.put(message)
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
        self.formulation_lifetime += sleep_sec
        print("--> ", self.alive_time)
        self.alive_time += 1

    def write_main_effects(self, main_effects):
        ddate = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        file_name = 'TestProblem' + '_MainEffects_' + ddate + '.json'
        full_path = self.data_dir + file_name
        with open(full_path, 'w+') as f:
            f.write(json.dumps(main_effects))
            f.close()

    def process_queue_msg(self, block=False):
        if self.queue.empty():
            return True

        msg = self.queue.get(block=block)
        print('--> MESSAGE:', msg)
        if msg['type'] == 'stop':
            return False
        if msg['type'] == 'formulation change':
            self.main_effect_client.formulation_change(msg)


        return True

    def process_main_effects(self, main_effects):
        return main_effects

    def process_features(self, features):
        return features

    def send_advice_message(self, main_effects, features, alive_time):
        # Two possible message types: formulation.main_effect | formulation.feature
        msg_type = 'formulation.main_effect'
        data = main_effects

        # --> 1. Determine which type of message you want to send




        # --> 2. Send message to front-end
        self.send_message(msg_type, data)



    def send_message(self, msg_type, data):
        async_to_sync(self.channel_layer.send)(self.channel_name, {
            'type': msg_type,
            'name': '',
            'data': data,
            'speak': '',
            "voice_message": "",
            "visual_message_type": ["objective_space_plot"],
            "visual_message": [""],
            "writer": "daphne"
        })



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
        self.formulation_start_time = time.time()
        continue_running = True
        self.print_start()

        # ----- SENSITIVITY HANDLING -----
        # self.sensitivity_client = SensitivityClient(self.user_info)
        # self.sensitivity_client.calculate_main_effects()

        # ----- MAIN EFFECT HANDLING -----
        self.main_effect_client = MainEffectClient(self.user_info, self.session, self.current_objectives)
        self.main_effect_client.start_main_effect_evaluations()

        while continue_running:
            self.record_loop(sleep_sec=10)

            continue_running = self.process_queue_msg()

            # --> 1. Find current main effects and process
            main_effects = self.main_effect_client.get_current_main_effect_data()
            processed_main_effects = self.process_main_effects(main_effects)

            # --> 2. Find current driving features and process
            features = self.main_effect_client.get_current_driving_features()
            processed_features = self.process_features(features)

            # --> 3. Determine whether to send features or main effects to user (based on formulation_alive_time)
            formulation_alive_time = self.formulation_start_time - time.time()
            # self.send_advice_message(processed_main_effects, processed_features, formulation_alive_time)



        self.main_effect_client.shutdown()
        return 0
