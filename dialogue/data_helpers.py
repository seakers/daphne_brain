import numpy as np

def clean_str(spacy_doc):
    # Pre-process the strings
    tokens = []
    for token in spacy_doc:

        # If stopword or punctuation, ignore token and continue
        if (token.is_stop and not (token.lemma_ == "which" or token.lemma_ == "how" or token.lemma_ == "what"
                                   or token.lemma_ == "when" or token.lemma_ == "why")) \
                or token.is_punct:
            continue

        # Lemmatize the token and yield
        tokens.append(token.lemma_)
    return " ".join(tokens)


def get_label_using_logits(logits, top_number=1):
    logits = np.ndarray.tolist(logits)
    predicted_labels = []
    for item in logits:
        index_list = np.argsort(item)[-top_number:]
        index_list = index_list[::-1]
        predicted_labels.append(np.ndarray.tolist(index_list))
    return predicted_labels
