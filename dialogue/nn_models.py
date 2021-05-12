import os

import spacy
from tensorflow.keras.models import load_model

nn_models = {
    "EOSS": {},
    "EDL": {},
    "AT": {}
}

model_folder_path = os.path.join(os.getcwd(), "dialogue", "models")
for file in os.scandir(model_folder_path):
    if file.is_dir():
        daphne_version = file.name
        daphne_model_path = os.path.join(model_folder_path, daphne_version)
        for role_file in os.scandir(daphne_model_path):
            if role_file.is_dir():
                role = role_file.name
                daphne_role_path = os.path.join(daphne_model_path, role)

                if role == 'ner':
                    loaded_model = spacy.load(daphne_role_path)
                else:
                    # load json and create model
                    model_path = os.path.join(daphne_role_path, "model.h5")
                    loaded_model = load_model(model_path)
                nn_models[daphne_version][role] = loaded_model
