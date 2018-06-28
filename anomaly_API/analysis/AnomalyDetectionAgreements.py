import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import numpy as np
import json


def fill_neighbors(series, radius):

    n = series.shape[0]

    out = []
    for i in range(n):
        out.append(max(series[max(0, i-radius):min(n, i+radius+1)]))

    return out


class AgreementMethods(APIView):

    def post(self, request, format=None):

        methodOne = request.data['selectedAlgorithmOne']
        methodTwo = request.data['selectedAlgorithmTwo']
        typeOne = request.data['typeAlgorithmOne']
        typeTwo = request.data['typeAlgorithmTwo']

        variable = request.data['variable']

        t = request.data['radius']  # The threshold imposed to consider related anomalies

        data = pd.read_json(request.data['data'], orient='records').set_index('timestamp')

        if typeOne == 'UniVariate':
            anomaliesOne = pd.read_json(json.dumps(request.data['detectedOneVarAnomalies'][variable][methodOne]), orient='records')
        else:
            anomaliesOne = pd.read_json(json.dumps(request.data['detectedMultiVarAnomalies'][methodOne]), orient='records')

        if typeTwo == 'UniVariate':
            anomaliesTwo = pd.read_json(json.dumps(request.data['detectedOneVarAnomalies'][variable][methodTwo]), orient='records')
        else:
            anomaliesTwo = pd.read_json(json.dumps(request.data['detectedMultiVarAnomalies'][methodTwo]), orient='records')

        anomaliesOne['FlagAnomalyOne'] = 1
        anomaliesTwo['FlagAnomalyTwo'] = 1
        anomaliesOne = anomaliesOne.set_index('timestamp')
        anomaliesTwo = anomaliesTwo.set_index('timestamp')

        # Merges the data with the anomalies, only keeps the flag which indicates which dataPoints
        # correspond with an anomaly
        result = pd.concat([data, anomaliesOne['FlagAnomalyOne'], anomaliesTwo['FlagAnomalyTwo']], axis=1)
        x = result.fillna(0)

        # Compares only the selected Data
        if request.data['useSelectedData']:
            selectedData = pd.read_json(json.dumps(request.data['selectedData']), orient='records')
            x['selectedData'] = selectedData.values

            if np.sum(x['selectedData']) == 0:
                return Response({'writtenResponse': [{'introduction': 'ERROR: NO SELECTED DATA', 'bulletPoints': []}]})

            x = x[x['selectedData']]

        n = x.shape[0]
        x['FlagNeighborOne'] = fill_neighbors(x['FlagAnomalyOne'], t)
        x['FlagNeighborTwo'] = fill_neighbors(x['FlagAnomalyTwo'], t)
        x['Coincidence'] = x['FlagAnomalyOne'] * x['FlagAnomalyTwo']
        x['RelatedOne'] = x['FlagAnomalyOne'] * x['FlagNeighborTwo']
        x['RelatedTwo'] = x['FlagAnomalyTwo'] * x['FlagNeighborOne']

        # Computes the scores
        sumOne= np.sum(np.min(np.asmatrix([np.asanyarray(x['Coincidence'] + x['RelatedOne'] * 0.5), np.ones(n)]), axis=0))
        sumTwo = np.sum(np.min(np.asmatrix([np.asanyarray(x['Coincidence'] + x['RelatedTwo'] * 0.5), np.ones(n)]), axis=0))
        sumFlagOne = sum(x['FlagAnomalyOne'])
        sumFlagTwo = sum(x['FlagAnomalyTwo'])

        score_One = 100 * sumOne / sumFlagOne
        score_Two = 100 * sumTwo / sumFlagTwo
        score_All = 100 * (sumOne + sumTwo) / (sumFlagOne + sumFlagTwo)

        writtenResponseGeneric = {
            'introduction': 'There is a ' + str(score_All) + '% agreement between method ' + methodOne + ' and ' + methodTwo,
            'bulletPoints': [
                'Total number of anomalies detected by ' + methodOne + ' is ' + str(sumFlagOne),
                'Total number of anomalies detected by ' + methodTwo + ' is ' + str(sumFlagTwo)
            ]
        }

        writtenResponseOne = {
            'introduction': 'There is a ' + str(score_One) + '% agreement of the anomalies detected with method ' + methodOne
                            + ' to anomalies detected with' + methodTwo,
            'bulletPoints': [
                'Total number of anomalies detected by ' + methodOne + ' is ' + str(sumFlagOne),
                'The ' + str(100 * sum(x['Coincidence']) / sumFlagOne) + '% coincide with anomalies detected with method ' + methodTwo,
                'The ' + str(100 * sum(x['RelatedOne']) / sumFlagOne) + '%  are near to anomalies detected with method ' + methodTwo,
                ]
        }

        writtenResponseTwo = {
            'introduction': 'There is a ' + str(score_Two) + '% agreement of the anomalies detected with method ' + methodTwo
                            + ' to anomalies detected with' + methodOne,
            'bulletPoints': [
                'Total number of anomalies detected by ' + methodTwo + ' is ' + str(sumFlagTwo),
                'The ' + str(100 * sum(x['Coincidence']) / sumFlagTwo) + '% coincide with anomalies detected with method ' + methodOne,
                'The ' + str(100 * sum(x['RelatedTwo']) / sumFlagTwo) + '%  are near to anomalies detected with method ' + methodOne,
                ]
        }

        outJson = {
            'writtenResponse': [writtenResponseGeneric, writtenResponseOne, writtenResponseTwo]
        }

        return Response(outJson)
