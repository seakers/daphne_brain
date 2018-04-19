from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import daphne_API.command_processing as command_processing
from daphne_brain.nlp_object import nlp
import daphne_API.command_lists as command_lists

import pandas as pd
import numpy as np


class ADWindowedStats(APIView):

    def post(self, request, format=None):

        """
        Windowed Gaussian anomaly detection
        :param w: Window size
        :param tstd: Gauss Threshold
        :param data:
        :return: the output consists on the datetimes for which the algoritm detects an anomaly
        """

        w = 100
        if 'w' in request.data:
            if int(request.data['w']) > 0:
                w = int(request.data['w'])
            else:
                return Response({"error": "Window parameter must be integer greater than 0"})

        tstd = 3
        if 'tstd' in request.data:
            tstd = float(request.data['tstd'])
            if tstd <= 0:
                return Response({"error": "Threshold parameter must be number grater than 0"})

        if 'data' in request.data:
            data = pd.read_json(request.data['data'], orient='records').set_index('timestamp')

        else:
            data = pd.read_csv('anomaly_API/Time series example/sample.csv', parse_dates=True,
                               index_col='timestamp')

        one_var = data[data.columns[0]]

        data['Flag_Anomaly'] = False

        for x in range(len(one_var)):

            if x > w / 2:
                window = one_var[max(0, x - w):x - 1]
                mean = np.mean(window)
                std = np.std(window)
                data.iat[x, -1] = abs(one_var[x] - mean) > std * tstd

        # data['Anomaly_val_Norm'] = data['value'] * data['Flag_Anomaly']
        # plt.plot(data['value'])
        # plt.plot(data[data.Anomaly_val_Norm != 0]['Anomaly_val_Norm'], 'ro')

        data['timestamp'] = data.index
        out = data[data.Flag_Anomaly][['timestamp', data.columns[0]]].to_json(orient='records', date_format='iso')

        return Response(out)
