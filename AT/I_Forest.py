import hashlib

from django.conf import settings

from channels.generic.websocket import JsonWebsocketConsumer

import pandas as pd
import numpy as np
import random


# Nodes classes definition
# Internal node
class InNode:
    def __init__(self, left, right, att, val):
        self.left = left
        self.right = right
        self.s_atr = att
        self.s_val = val


# External node
class ExNode:
    def __init__(self, size):
        self.size = size


# Generates the isolation forest
def i_forest(X, t, psi):
    """
    :param X: input data
    :param t: number of trees
    :param psi: subsampling size
    :return: Returns an isolation forest
    """

    forest = []
    height_limit = int(np.ceil(np.log2(psi)))
    n = X.shape[0]

    for i in range(t):
        sample = X.iloc[np.random.choice(n, psi, replace=False)]
        forest.append(i_tree(sample, 0, height_limit))

    return forest


# Generates a random isolation tree
def i_tree(x, e, l):
    """
    Generates an isolation tree
    :param x: Input data
    :param e: Current Tree Height
    :param l: Height limit
    :return: Inner Node/ Extreme node
    """

    if e >= l or x.size <= 1:
        return ExNode(x.shape[0])

    else:
        q = random.choice(x.columns)
        [v_max, v_min] = [max(x[q]), min(x[q])]
        p = np.random.uniform(v_min, v_max)
        # Filtering
        xl = x[x[q] < p]
        xr = x[x[q] >= p]
        return InNode(i_tree(xl, e+1, l), i_tree(xr, e+1, l), q, p)


def c(size):
    if size <= 1:
        return 0
    else:
        h = np.log(size-1) + np.euler_gamma
        return 2*h - (2*(size-1)/size)


# Computes the leght of the path of the tree provided
def path_length(x, T, e):
    """
    :param x: An instance
    :param T: An isolation Tree
    :param e: The current path lenght
    :return:
    """
    if isinstance(T, ExNode):
        return e + c(T.size)

    attribute = T.s_atr
    if x[attribute] < T.s_val:
        return path_length(x, T.left, e+1)
    else:
        return path_length(x, T.right, e+1)


class iForest(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()

    def receive_json(self, content, **kwargs):

        if 'data' in content:
            data = pd.read_json(content['data'], orient='records').set_index('timestamp')
        else:
            data = pd.read_csv('anomaly_API/Data/sample_3.csv', parse_dates=True, index_col='timestamp')
        if 't' in content:  # Number of trees
            t = content['t']
        else:
            t = 20
        if 'sp' in content:
            sp = content['sp']
        else:
            sp = 0.1

        # Calculates the sampling size
        n = data.shape[0]
        m = int(n * sp)

        forest = i_forest(data, t, m)

        meanPathLength = []

        for i in range(n):
            sumPL = 0
            for tree in forest:
                sumPL += path_length(data.iloc[i], tree, 0)

            meanPathLength.append(sumPL / t)

        minPL = np.min(meanPathLength)
        maxPL = np.max(meanPathLength)
        out = pd.DataFrame()
        out["anomalyScore"] = 1 + ((meanPathLength - minPL) / (minPL - maxPL))
        out['timestamp'] = data.index

        self.send_json(out.to_json(date_format='iso', orient='records'))


