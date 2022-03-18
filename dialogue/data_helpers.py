import numpy as np


def get_label_using_logits(logits, top_number=1):
    logits_list = logits.tolist()
    predicted_labels = []
    for item in logits_list:
        index_list = np.argsort(item)[-top_number:]
        index_list = index_list[::-1]
        predicted_labels.append(np.ndarray.tolist(index_list))
    return predicted_labels
