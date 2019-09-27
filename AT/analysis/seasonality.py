from rest_framework.views import APIView
from rest_framework.response import Response

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf


class CheckSeasonality(APIView):

    def post(self, request, format=None):

        data = pd.read_json(request.data['data'], orient='records').set_index('timestamp')
        #
        # data = pd.read_csv('AT/Data/sample.csv', parse_dates=True, index_col='timestamp')

        if 'variable' in request.data:
            variable = request.data['variable']
        else:
            variable = data.columns[0]

        # input: maximum lag allowed
        if 'n' in request.data:
            n = request.data['n']
        else:
            n = 100

        m = int(n/2)  # margin

        probability_threshold = 0.5
        probability_threshold2 = 0.8

        series = data[variable]
        acfOut = np.abs(acf(series, nlags=(n+m)))

        # to asses the probability
        seasonality_probability = np.zeros(n)
        for i in range(n):

            if i > 0:  # do not compute 0 all acf will have a maximum on

                k = -1
                x = acfOut[i]
                local_max = True
                while local_max:
                    k += 1
                    if k > int(i/2):
                        break
                    else:
                        xki = acfOut[i - k - 1]
                        xik = acfOut[i + k + 1]
                        local_max = (x > xki and x > xik)
                seasonality_probability[i] = min(2*k/i, 1)

        season = pd.DataFrame()
        season['probability'] = -np.sort(-seasonality_probability)
        season['index'] = np.argsort(-seasonality_probability)

        out = season[season.probability > probability_threshold]

        # Generates the written response
        outL = out.shape[0]
        introduction = 'Analysis have found ' + str(outL) + ' significant Seasonalities'
        bulletPoints = []
        for i in range(outL):
            if out['probability'][i] > probability_threshold2:
                bulletPoints.append('Lag ' + str(out['index'][i]) + ' with high probability')
            else:
                bulletPoints.append('Lag ' + str(out['index'][i]))
        postData = "Note that Multiple seasonalities must be ignored, they reinforce the first value"

        writtenResponse = {
            'introduction': introduction,
            'bulletPoints': bulletPoints,
            'postData': postData
        }

        # Final output JSON
        outJson = {
            'writtenResponse': [writtenResponse]
        }

        return Response(outJson)

