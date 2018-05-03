import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import json
import matplotlib.pyplot as plt


class DetectMultivariateAnomaliesThreshold (APIView):

    def post(self, request, format=None):

        method = request.data['selectedMultiVarAlgorithm']

        anomalyScore = pd.read_json(json.dumps(request.data['anomalyScore'][method]), orient='records')

        threshold = request.data['threshold']

        detectedAnomalies = anomalyScore[anomalyScore['anomalyScore'] > threshold]

        detectedAnomaliesJSON = detectedAnomalies.to_json(orient='records', date_format='iso')

        # Elaborate a written Response
        numberAnomalies = detectedAnomalies.shape[0]

        introduction = 'Analysis found ' + str(numberAnomalies) + ' anomalies applying a threshold of ' + str(threshold)
        bulletPoints = []

        writtenResponse = {
            'introduction': introduction,
            'bulletPoints': bulletPoints
        }

        # Final output JSON
        outJson = {
            'writtenResponse': [writtenResponse],
            'detectedAnomalies': detectedAnomaliesJSON
        }

        return Response(outJson)


class DetectMultivariateAnomaliesNumber(APIView):

    def post(self, request, format=None):
        method = request.data['selectedMultiVarAlgorithm']

        anomalyScore = pd.read_json(json.dumps(request.data['anomalyScore'][method]), orient='records')

        n = request.data['n']

        detectedAnomalies = anomalyScore.sort_values('anomalyScore', ascending=False)[:n].sort_values('timestamp')

        detectedAnomaliesJSON = detectedAnomalies.to_json(orient='records', date_format='iso')

        # Elaborate a written Response
        threshold = detectedAnomalies.min(axis=0)['anomalyScore']

        introduction = 'Analysis fixed a' + str(threshold) + ' threshold by restricting the number of anomalies to ' + str(n)
        bulletPoints = []

        writtenResponse = {
            'introduction': introduction,
            'bulletPoints': bulletPoints
        }

        # Final output JSON
        outJson = {
            'writtenResponse': [writtenResponse],
            'detectedAnomalies': detectedAnomaliesJSON
        }

        return Response(outJson)


