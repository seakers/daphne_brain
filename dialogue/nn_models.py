import os
from pathlib import Path
from transformers import AutoModelForSequenceClassification

nn_models = {
    "EOSS": {},
    "EDL": {},
    "AT": {}
}

model_folder_path = Path("./dialogue/models/")
for file in os.scandir(model_folder_path):
    if file.is_dir():
        daphne_version = file.name
        daphne_model_path = model_folder_path / daphne_version
        for role_file in os.scandir(daphne_model_path):
            if role_file.is_dir():
                role = role_file.name
                daphne_role_path = daphne_model_path / role

                loaded_model = AutoModelForSequenceClassification.from_pretrained(daphne_role_path)
                nn_models[daphne_version][role] = loaded_model
