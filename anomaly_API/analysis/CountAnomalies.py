from rest_framework.views import APIView
from rest_framework.response import Response

import pandas as pd
import numpy as np
import json


class CountAnomalies(APIView):

    def post(self, request, format=None):

        anomalyData = request.data['detectedOneVarAnomalies']

        n = request.data['n']

        data = pd.read_json(request.data['data'], orient='records').set_index('timestamp')

        if not request.data['analyzeAllSeries']:
            selectedData = pd.read_json(json.dumps(request.data['selectedData']), orient='records')
            data['selectedData'] = selectedData.values

            if np.sum(data['selectedData']) == 0:
                return Response({'writtenResponse': [{'introduction': 'ERROR: NO SELECTED DATA', 'bulletPoints': []}]})

            data = data[data['selectedData']]

        x = pd.DataFrame(columns=['Variable', 'Algorithm', 'Count'])
        for variable, value in anomalyData.items():
            for algorithm, anomalies in value.items():
                if len(anomalies):
                    pdAnomalies = pd.read_json(json.dumps(anomalies)).set_index('timestamp')
                    count = data.merge(pdAnomalies, left_index=True, right_index=True).shape[0]
                else:
                    count = 0
                x = x.append([{'Variable': variable, 'Algorithm': algorithm, 'Count': count}])  # Does not allow to search in a particular regions

        vector = x['Count'].values

        argOrdered = np.argsort(-vector)

        introduction = 'The ' + str(n) + ' variables with more anomalous in the selected region are:'
        bulletPoints = []

        for i in range(n):
            variable = x.iloc[argOrdered[i]]['Variable']
            algorithm = x.iloc[argOrdered[i]]['Algorithm']
            count = x.iloc[argOrdered[i]]['Count']
            bulletPoints.append('Variable ' + variable + ' counts ' + str(count) + ' anomalies, using algorithm ' + algorithm)

        outJson = {'writtenResponse': [{'introduction': introduction, 'bulletPoints': bulletPoints}]}

        return Response(outJson)


