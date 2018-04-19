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
        data['timestamp'] = data.index
        out = data.to_json(orient='records', date_format='iso')
        columns = data.columns
        return_value = {
            "data": json.loads(out),
            "variables": columns
        }
        return Response(return_value)

