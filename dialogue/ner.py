# Import Spacy
import spacy
from sys import argv
import os

MODEL_USED = "ner_model"
nlp = spacy.load(MODEL_USED)

# Returns a list of dicts with the text, label, starting and ending chart of every entity
def ner(text):
    doc = nlp(text)
    entities_recognized = []
    extraction_dict = {}
    for index, entity in enumerate(doc.ents):
        entities_recognized.append({"text": entity.text, 
                                    "label": entity.label_, 
                                    "start": entity.start_char, 
                                    "end": entity.start_char + len(entity.text)})
        if extraction_dict[entity.label_.lower()]:
            extraction_dict[entity.label_.lower()].append(entity.text)
        else:
            extraction_dict[entity.label_.lower()] = [entity.text]

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