import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import numpy as np
import json


class Correlation(APIView):

    def post(self, request, format=None):

        nc = request.data['n']

        variable = request.data['variable']

        analyzeAllVariables = request.data['analyzeAllVariables']

        if request.data['Spearman']:
            correlations = pd.read_json(json.dumps(request.data['correlationSpearman'])).set_index('Variable')
        else:
            correlations = pd.read_json(json.dumps(request.data['correlation'])).set_index('Variable')

        correlationsAbs = np.abs(correlations)

        nvar = correlationsAbs.shape[0]

        for i in range(nvar):
            correlationsAbs.iloc[i, i] = float('nan')

        nval = correlationsAbs.size

        if analyzeAllVariables:
            correlationsArray = correlationsAbs.values.reshape(nval)
            orderedCorrelationIndexes = np.argsort(correlationsArray)[::-1][nvar:][::2]
        else:
            correlationsArray = correlationsAbs[variable].values
            orderedCorrelationIndexes = np.argsort(correlationsArray)[::-1][1:]

        introduction = 'The mean absolute correlation of the variables is ' + str(np.mean(correlationsArray[~np.isnan(correlationsArray)]))

        introductionMostCorrelated = 'The ' + str(nc) + ' most correlated variables are:'
        bulletPointsMostCorrelated = []
        for i in range(nc):
            arg = orderedCorrelationIndexes[i]
            if analyzeAllVariables:
                index1 = int(arg / nvar)
            else:
                index1 = correlations.columns.get_loc(variable)
            index2 = arg % nvar
            column1 = correlations.columns[index1]
            column2 = correlations.columns[index2]
            bulletPointsMostCorrelated.append('Variables ' + column1 + ' and ' + column2 + ' with a ' +
                                              str(correlations.iloc[index1, index2]) + ' correlation')

        writtenResponse1 = {
            'introduction':  introduction,
            'bulletPoints': []
        }

        writtenResponse2 = {
            'introduction': introductionMostCorrelated,
            'bulletPoints': bulletPointsMostCorrelated
        }

        outJson = {
            'writtenResponse': [writtenResponse1, writtenResponse2]
        }

        return Response(outJson)


