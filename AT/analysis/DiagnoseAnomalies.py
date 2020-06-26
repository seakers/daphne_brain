import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import numpy as np
import json

class DiagnoseAnomalies(APIView):

    def post(self, request, format=None):

        writtenResponse = []

        # Load and select anomalies
        data = pd.read_json(request.data['data'], orient='records').set_index('timestamp')

        methodAD = request.data['selectedMultiVarAlgorithm']

        anomaliesDetected = pd.read_json(json.dumps(request.data['detectedMultiVarAnomalies'][methodAD]),
                                         orient='records').set_index('timestamp')

        anomaliesDetected['FlagAnomaly'] = 1

        anomaliesDetected = pd.concat([data, anomaliesDetected['FlagAnomaly']], axis=1)
        anomaliesDetected = anomaliesDetected.fillna(0)

        if request.data['useSelectedData']:
            selectedData = pd.read_json(json.dumps(request.data['selectedData']), orient='records')
            anomaliesDetected['selectedData'] = selectedData.values

            if np.sum(anomaliesDetected['selectedData']) == 0:
                return Response({'writtenResponse': [{'introduction': 'ERROR: NO SELECTED DATA', 'bulletPoints': []}]})

            anomaliesDetected = anomaliesDetected[anomaliesDetected['selectedData']]

        if np.sum(anomaliesDetected['FlagAnomaly']) == 0:
            return Response({'writtenResponse': [{'introduction': 'ERROR: No anomalies in the selection', 'bulletPoints': []}]})

        anomaliesDetected = anomaliesDetected[anomaliesDetected['FlagAnomaly'] == 1]

        # Load anomaly Database

        database = pd.read_json(json.dumps(request.data['database']), orient='records')
        if database.shape[0] == 0:
            return Response({'writtenResponse': [{'introduction': 'ERROR: No Database Loaded / Database is Empty', 'bulletPoints': []}]})

        variablesData = data.columns

        variablesDatabase = database.columns

        variablesCommon = variablesData.join(variablesDatabase, how='inner')

        if len(variablesCommon) != len(variablesData) or len(variablesCommon) != (len(variablesDatabase) - 3):
            writtenResponse.append({
                'introduction': 'WARNING: The variables in the data and in the database do not coincide',
                'bulletPoints': []
            })

        # Perform KNN

        normalizerMean = np.asmatrix(np.mean(data[variablesCommon]))

        normalizerStd = np.asmatrix(np.std(data[variablesCommon]))

        # The training values are the already classified values, the data from the database
        NNTrain = database[variablesCommon]
        NNTrain = NNTrain.values
        NNTrain = (NNTrain - normalizerMean) / normalizerStd
        m = NNTrain.shape[0]
        # The test values are the novel anomalies
        NNTest = anomaliesDetected[variablesCommon]
        NNTest = NNTest.values
        NNTest= (NNTest - normalizerMean) / normalizerStd
        n = NNTest.shape[0]

        # Initialize Distance matrix
        distanceMatrix = np.zeros([n, m])

        for i in range(n):
            for j in range(m):
                distanceMatrix[i, j] = np.linalg.norm(NNTest[i] - NNTrain[j])

        sortedArguments = np.argsort(distanceMatrix, axis=1)

        for i in range(n):
            anomalyIndex = sortedArguments[i][0]
            introduction = 'The closes anomaly to the one detected with timestamp ' + str(anomaliesDetected.index[i]) + \
                           ' has the following characteristics:'
            bulletPoints = [
                'Detected in ' + str(database['timestamp'][anomalyIndex]),
                'Anomaly Type: ' + database['anomalyType'][anomalyIndex],
                'Action Taken: ' + database['anomalyAction'][anomalyIndex]
            ]
            writtenResponse.append({'introduction': introduction, 'bulletPoints': bulletPoints})

        return Response({'writtenResponse': writtenResponse})

