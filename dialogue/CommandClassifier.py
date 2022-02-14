from daphne_brain.utils import _proc
import numpy as np
import pickle
import os
from tensorflow.keras.models import load_model
from daphne_brain.nlp_object import nlp
from asgiref.sync import async_to_sync, sync_to_async

from dialogue import qa_pipeline







class CommandClassifier:

    def __init__(self, user_info, command):
        self.user_info = user_info
        self.command = command

        # --> Classification Variables
        self.role_logits = None
        self.type_logits = None


    def clarify(self):
        return 0




    def classify(self):

        # --> 1. Classify Roles (e.g. VASSAR)
        self.classify_roles()
        roles = self.get_role_prediction(top_number=1)
        for role in roles:

            # --> 2. Classify Types (e.g. 1001)
            self.classify_types(role)
            confidence = self.get_type_confidence(self.type_logits)
            types = self.get_type_prediction(role, top_number=3)

            # --> 3. Add appropriate command intent
            self.command.add_intent(role, types, confidence)  # e.g. ( 'VASSAR', '[ 1001, 1002 ]', 0.94 )





    """
       _____  _                   _   __  _              _    _               
      / ____|| |                 (_) / _|(_)            | |  (_)              
     | |     | |  __ _  ___  ___  _ | |_  _   ___  __ _ | |_  _   ___   _ __  
     | |     | | / _` |/ __|/ __|| ||  _|| | / __|/ _` || __|| | / _ \ | '_ \ 
     | |____ | || (_| |\__ \\__ \| || |  | || (__| (_| || |_ | || (_) || | | |
      \_____||_| \__,_||___/|___/|_||_|  |_| \___|\__,_| \__||_| \___/ |_| |_|
                   
        - The idea is that each classify function will set and return logits for post-processing
                                                                            
    """

    def classify_roles(self):

        # --> 1. Load Model
        loaded_model = self._get_model('general')

        # --> 2. Get tokenizer vocabulary
        vocab_path = os.path.join(os.getcwd(), "dialogue", "models", self.command.daphne_version, "general", "tokenizer.pickle")
        with open(vocab_path, 'rb') as handle:
            tokenizer = pickle.load(handle)

        # --> 3. Map command into vocabulary
        expected_input_length = loaded_model.layers[0].input_shape[0][1]
        x = tokenizer.texts_to_sequences([self.command.cmd])
        x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])

        # --> 4. Classify
        self.role_logits = loaded_model.predict(x)

        # --> 5. Return logits
        return self.role_logits


    def classify_types(self, role):

        # --> 1. Load Model
        loaded_model = self._get_model(role)

        # --> 2. Get tokenizer vocabulary
        vocab_path = os.path.join(os.getcwd(), "dialogue", "models", self.command.daphne_version, role, "tokenizer.pickle")
        with open(vocab_path, 'rb') as handle:
            tokenizer = pickle.load(handle)

        # --> 3. Map command into vocabulary
        expected_input_length = loaded_model.layers[0].input_shape[0][1]
        x = tokenizer.texts_to_sequences([self.command.cmd])
        x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])

        # --> 4. Classify
        self.type_logits = loaded_model.predict(x)

        # --> 5. Return logits
        return self.type_logits


    def _get_model(self, role):
        model_folder_path = os.path.join(os.getcwd(), "dialogue", "models")
        for file in os.scandir(model_folder_path):
            if file.is_dir():
                daphne_version = file.name
                daphne_model_path = os.path.join(model_folder_path, daphne_version)
                for role_file in os.scandir(daphne_model_path):
                    if role_file.is_dir():
                        if role != role_file.name:
                            continue

                        daphne_role_path = os.path.join(daphne_model_path, role)

                        # load json and create model
                        model_path = os.path.join(daphne_role_path, "model.h5")
                        return load_model(model_path)


    """
      _                    _  _     _____                                   _               
     | |                  (_)| |   |  __ \                                 (_)              
     | |      ___    __ _  _ | |_  | |__) |_ __  ___    ___  ___  ___  ___  _  _ __    __ _ 
     | |     / _ \  / _` || || __| |  ___/| '__|/ _ \  / __|/ _ \/ __|/ __|| || '_ \  / _` |
     | |____| (_) || (_| || || |_  | |    | |  | (_) || (__|  __/\__ \\__ \| || | | || (_| |
     |______|\___/  \__, ||_| \__| |_|    |_|   \___/  \___|\___||___/|___/|_||_| |_| \__, |
                     __/ |                                                             __/ |
                    |___/                                                             |___/     
    """

    def get_prediction_idx(self, logits, top_number=1):
        logits = np.ndarray.tolist(logits)
        predicted_labels = []
        for item in logits:
            index_list = np.argsort(item)[-top_number:]
            index_list = index_list[::-1]
            predicted_labels.append(np.ndarray.tolist(index_list))
        return predicted_labels[0]


    def get_role_prediction(self, top_number=1):
        roles_idx = self.get_prediction_idx(self.role_logits, top_number)
        return [self.command.daphne_roles[idx] for idx in roles_idx]


    def get_type_prediction(self, role, top_number=1):
        numerical_labels = self.get_prediction_idx(self.type_logits, top_number)

        named_labels = []
        type_info_folder = os.path.join(os.getcwd(), self.command.daphne_version, "dialogue", "command_types", role)
        for filename in sorted(os.listdir(type_info_folder)):
            specific_label = int(filename.split('.', 1)[0])
            named_labels.append(specific_label)
        command_types = []
        for label in numerical_labels:
            command_types.append(named_labels[label])
        return command_types


    def get_type_confidence(self, logits):
        return np.amax(logits)


    """
                                                  
         /\                                      
        /  \    _ __   ___ __      __ ___  _ __  
       / /\ \  | '_ \ / __|\ \ /\ / // _ \| '__| 
      / ____ \ | | | |\__ \ \ V  V /|  __/| |    
     /_/    \_\|_| |_||___/  \_/\_/  \___||_|    
                                                                                                      
            
    """

    def answer(self, role, condition):
        answer = None

        # --> 1. Get top command type (return list of length 1)
        command_type = self.get_type_prediction(role, top_number=1)

        # --> 2. Create new dialogue context
        dialogue_context = self.command.create_dialogue_contexts()

        # --> 3. Validate conditions
        if self._check_conditions(condition, command_type) is False:
            answer = {
                'voice_answer': 'This command is restricted right now.',
                'visual_answer_type': ['text'],
                'visual_answer': ['This command is restricted right now.']
            }
            return answer

        # --> 4. Load type info
        information = qa_pipeline.load_type_info(command_type, self.command.daphne_version, role)








        return 0



    def _check_conditions(self, command_condition, command_type):
        if len(self.user_info.allowedcommand_set.all()) == 0:
            return False
        for allowed_command in self.user_info.allowedcommand_set.all():
            if command_condition == allowed_command.command_type and command_type == str(
                    allowed_command.command_descriptor):
                return False






