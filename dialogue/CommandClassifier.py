import numpy as np
import pickle
import os
from tensorflow.keras.models import load_model

from EOSS.graphql.api import GraphqlClient

classifier_models = {
    'EOSS': '/app/daphne/daphne_brain/dialogue/models/EOSS',
    'CA': '/app/daphne/daphne_brain/dialogue/models/CA'
}

classifier_command_types = {
    'EOSS': '/app/daphne/daphne_brain/EOSS/dialogue/command_types',
    'CA': '/app/daphne/daphne_brain/CA/dialogue/command_types'
}



class CommandClassifier:

    def __init__(self, command, daphne_version='EOSS'):
        self.user_info = command.user_info
        self.command = command
        self.graphql_client = GraphqlClient()

        # --> Classification Variables
        self.role_logits = None
        self.type_logits = None

        # --> Models Paths
        self.models_path = classifier_models[daphne_version]
        self.types_path = classifier_command_types[daphne_version]

        # --> Confidence Store
        self.confidence = []


    def classify(self, max_role_matches=1):
        results = []

        # --> 1. Classify Roles (e.g. VASSAR)
        self.classify_roles()
        roles = self.get_role_prediction(top_number=max_role_matches)
        for role in roles:

            # --> 2. Classify Types (e.g. 1001)
            self.classify_types(role)
            confidence = self.get_type_confidence(self.type_logits)
            types = self.get_type_prediction(role, top_number=3)

            # --> 3. Add appropriate command intent
            self.command.add_intent(role, types, confidence)  # e.g. ( 'VASSAR', '[ 1001, 1002 ]', 0.94 )
            results.append('--> ' + str(role) + ' : ' + str(types) + ' : ' + str(confidence))

        # --> 2. Print results
        for result in results:
            print(result)


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
        vocab_path = os.path.join(self.models_path, "general", "tokenizer.pickle")
        with open(vocab_path, 'rb') as handle:
            tokenizer = pickle.load(handle)

        # --> 3. Map command into vocabulary
        expected_input_length = loaded_model.layers[0].input_shape[0][1]
        x = tokenizer.texts_to_sequences([self.command.cmd_clean])
        x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])

        # --> 4. Classify
        self.role_logits = loaded_model.predict(x)
        print('--> ROLE LOGITS:', self.role_logits)

        # --> 5. Build confidence object
        self.confidence = []
        logits_list = np.ndarray.tolist(self.role_logits)[0]
        for idx, logit in enumerate(logits_list):
            module_obj = {
                'name': self.command.daphne_roles[idx],
                'id': self.graphql_client.get_learning_module_id(self.command.daphne_roles[idx]),
                'confidence': round(logit, 3),
                'slides': [],
            }
            self.confidence.append(module_obj)
        self.confidence.sort(key=lambda itenz: itenz['confidence'], reverse=True)








        # --> 6. Return logits
        return self.role_logits


    def classify_types(self, role):

        # --> 1. Load Model
        loaded_model = self._get_model(role)

        # --> 2. Get tokenizer vocabulary
        vocab_path = os.path.join(self.models_path, role, "tokenizer.pickle")
        with open(vocab_path, 'rb') as handle:
            tokenizer = pickle.load(handle)

        # --> 3. Map command into vocabulary
        expected_input_length = loaded_model.layers[0].input_shape[0][1]
        x = tokenizer.texts_to_sequences([self.command.cmd_clean])
        x = np.array([x[0] + [0] * (expected_input_length - len(x[0]))])

        # --> 4. Classify
        self.type_logits = loaded_model.predict(x)

        # --> 5. Build confidence object
        slide_list = []
        logits_list = np.ndarray.tolist(self.type_logits)[0]
        for idx, logit in enumerate(logits_list):
            slide_list.append({
                'id': idx,
                'confidence': round(logit, 3)
            })
        slide_list.sort(key=lambda itenz: itenz['confidence'], reverse=True)
        for item in self.confidence:
            if item['name'] == role:
                item['slides'] = slide_list




        # --> 6. Return logits
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
        roles_list = [self.command.daphne_roles[idx] for idx in roles_idx]
        return roles_list


    def get_type_prediction(self, role, top_number=1):
        numerical_labels = self.get_prediction_idx(self.type_logits, top_number)

        named_labels = []
        type_info_folder = os.path.join(self.types_path, role)
        for filename in sorted(os.listdir(type_info_folder)):
            specific_label = int(filename.split('.', 1)[0])
            named_labels.append(specific_label)
        command_types = []


        for label in numerical_labels:
            command_types.append(named_labels[label])
        return command_types


    def get_type_confidence(self, logits):
        return np.amax(logits)


    def get_prediction_confidence(self):
        return self.confidence
