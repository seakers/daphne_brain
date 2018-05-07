import hashlib

from django.conf import settings

from channels.generic.websocket import JsonWebsocketConsumer

import pandas as pd
import numpy as np


class adaptiveKNN(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()

    def receive_json(self, content, **kwargs):

        # Reads the data if available in content
        if 'data' in content:
            data = pd.read_json(content['data'], orient='records').set_index('timestamp')
        else:
            # Read Sample CSV
            data = pd.read_csv('anomaly_API/Data/sample_3.csv', parse_dates=True, index_col='timestamp')

        if 'k' in content:  # Number of nearest Neighbors
            k = content['k']
        else:
            k = 10

        if 'c' in content:  # Overall smoothing parameter
            c = content['c']
        else:
            c = 10

        if 'eps' in content:  # Epsilon to avoid per zero division
            eps = content['eps']
        else:
            eps = 10e-5

        if 'sp' in content:  # Random sampling fraction parameters
            sp = content['sp']
        else:
            sp = 1

        # Transfer data to matrix
        x = np.asmatrix(data.values)

        # This parameters must be entered
        n = len(x)
        m = int(n*sp)   # Random samples a percentage of the data: training data

        # Set the training data
        x_train = x[np.random.choice(x.shape[0], m, replace=False)]
        x_train_mean = x_train.mean(axis=0)
        x_train_std = x_train.std(axis=0)

        # Normalizes the data
        x_train = (x_train - x_train_mean) / x_train_std
        x = (x - x_train_mean) / x_train_std

        # TODO must also Consider if there is a provided training set
        matD = np.ones((n, m)) * np.inf
        for i in range(n):
            for j in range(m):
                d = np.linalg.norm(x[i] - x_train[j])
                if d > 0:  # We avoid having distances = 0 (Which correspond with the sampled points)
                    matD[i, j] = d

        # Finds the nearest neighbors
        near_neigh = np.argsort(matD, axis=1)
        # Selects only the k nearest neighbors
#        k_near = near_neigh[:, 1:k]  # The number one is to avoid matching them with themselves
        k_near = near_neigh[:, :k]

        # Create distance matrix
        dist_k = np.zeros((n, k))
        for i in range(n):
            dist_k[i] = matD[i, k_near[i]]

        # dist_k is an ordered vector
        dk_mean = np.mean(dist_k, axis=1)
        dk_max = np.max(dk_mean)
        dk_min = np.min(dk_mean)

        ri = c * (eps + dk_min + dk_max - dk_mean)  # Computes the kernel radius
        # Note that we are only using the k nearest neighbors to compute the kernel radius

        d_all = np.sort(matD, axis=1)[:, :-1]
        # We avoid taking the last distance as is not 'fair' for the sampled elements

        aux = np.zeros((n, m - 1))
        for i in range(n):
            aux[i] = d_all[i] / ri[i]

        ro = np.mean(np.exp(-(aux ** 2)), axis=1)  # Computes the density

        localOutlierScore = np.log(np.divide(np.mean(ro[k_near]), ro))  # Returns the local outlier score,
        # it might be interesting to normalize it or to be able to compare it with different outlier scores

        out = pd.DataFrame()
        out['anomalyScore'] = localOutlierScore
        out['timestamp'] = data.index

        self.send_json(
            out.to_json(date_format='iso', orient='records'))
