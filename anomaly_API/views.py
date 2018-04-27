import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import pandas as pd
import sys, os
import json
import csv
import hashlib
import datetime


# Get an instance of a logger


def obtain_features(data):
    """
    Obtains features of the data:
        Seasonality
        Correlation
    :param Data:
    :return:
    """
    correlation = data.corr()
    correlation['Variable'] = correlation.index
    correlation_json = correlation.to_json(orient='records')

    columns = data.columns
    data['timestamp'] = data.index
    out = data.to_json(orient='records', date_format='iso')
    return_value = {
        "data": json.loads(out),
        "variables": columns,
        "correlation": json.loads(correlation_json )
    }

    return return_value



class ImportData(APIView):
    """ Imports data from a csv file. To be deprecated in the future.

    Request Args:
        filename: Name of the sample data file

    Returns:
        data: Json string with the read data
        columns: array with the columns of the data

    """

    def post(self, request, format=None):

        # Set the path of the file containing data
        file_path = 'anomaly_API/Data/' + request.data['filename']

        data = pd.read_csv(file_path, parse_dates=True, index_col='timestamp')

        return Response(obtain_features(data))


class ReadUploadedData(APIView):

    def post(self, request, format=None):

        data = pd.read_csv(request.data['file'], parse_dates=True, index_col='timestamp')

        return Response(obtain_features(data))

