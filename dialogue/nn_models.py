import os

from keras.engine.saving import model_from_json

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

                # load json and create model
                model_path = os.path.join(daphne_role_path, "model.json")
                with open(model_path, mode="r") as model_json:
                    loaded_model = model_from_json(model_json.read())
                # load weights into new model
                weights_path = os.path.join(daphne_role_path, "model.h5")
                loaded_model.load_weights(weights_path)
                print("Loaded model from disk")

                loaded_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['binary_accuracy'])
                loaded_model._make_predict_function()
                nn_models[daphne_version][role] = loaded_model
