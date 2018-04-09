from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import daphne_API.command_processing as command_processing
from daphne_brain.nlp_object import nlp
import daphne_API.command_lists as command_lists
import json
import datetime
import pandas as pd
import numpy as np


class AD_WGAUSS(APIView):

    def post(self, request, format=None):
        """
        Windowed Gaussian anomaly detection
        :param w: Window size
        :param tstd:
        :return: the output consists on the datetimes for which the algoritm detects an anomaly
        """
        w = 100
        if 'w' in request.data:
            if request.data['w'] > 0 and isinstance(request.data['w'], int):
                w = request.data['w']
            else:
                return Response({"error": ""})

        tstd = 3
        if 'tstd' in request.data:
            tstd = request.data['tstd']

        data = pd.read_csv('anomaly_API/Time series example/sample.csv', parse_dates=True,
                           index_col='timestamp')
        one_var = data['value']

        data['Flag_Anomaly'] = False

        for x in range(len(one_var)):
            # To do: implement a mor intellingent and therefore efficient way to compute the moving average,
            # (without having to compute the mean of the whole vector, bit intead jut adding and subtracting a value)
            if x > w / 2:
                window = one_var[max(0, x - w):x - 1]
                mean = np.mean(window)
                std = np.std(window)
                data.iat[x, -1] = abs(one_var[x] - mean) > std * tstd

        # data['Anomaly_val_Norm'] = data['value'] * data['Flag_Anomaly']
        # plt.plot(data['value'])
        # plt.plot(data[data.Anomaly_val_Norm != 0]['Anomaly_val_Norm'], 'ro')

        data['index'] = data.index
        out = data[data.Flag_Anomaly][['index', 'value']].to_json(orient='records', date_format='iso')

        return Response(out)
