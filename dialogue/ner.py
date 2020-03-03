# Import Spacy
import spacy
from sys import argv
import os
import en_ner_model

MODEL_USED = "en_daphne_entities-12-0.0.0"

# Returns a list of dicts with the text, label, starting and ending chart of every entity
def ner(text):
    nlp = en_ner_model.load()
    doc = nlp(text.text)
    entities_recognized = []
    extraction_dict = {}
    for index, entity in enumerate(doc.ents):
        entities_recognized.append({"text": entity.text, 
                                    "label": entity.label_, 
                                    "start": entity.start_char, 
                                    "end": entity.start_char + len(entity.text)})
        try:
             extraction_dict[entity.label_.lower()].append(entity.text)
        except KeyError:
            extraction_dict[entity.label_.lower()] = [entity.text]
    print("extraction dict: {}".format(extraction_dict))
    return entities_recognized, extraction_dict

if __name__ == "__main__":
    # Run test.py "model_path" "text_to_evaluate- in the termina"
    model = argv[1]
    text = argv[2]
    print("\nModel: {}\nText: {}\n".format(model, text))
    nlp = spacy.load(model)
    doc = nlp(text)

    # Find named entities, phrases and concepts
    for index, entity in enumerate(doc.ents):
        print("{}: '{}' corresponds to {} from {} to {}".format(index + 1, entity.text, entity.label_, entity.start_char, entity.start_char+len(entity)))