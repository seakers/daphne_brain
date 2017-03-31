from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

from config.loader import ConfigurationLoader


sys.path.append("/Users/bang/workspace/daphne/daphne-brain/data_mining_API/")

# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)



config = ConfigurationLoader().load()


class importData(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        try:
            output = None
            # Set the path of the file containing data
            file_path = config['iFEED']['path'] + request.POST['path']
            # Open the file
            with open(file_path) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=',')
                self.architectures = []
                # For each row, store the information
                for ind, row in enumerate(read):
                    # Change boolean string to boolean array
                    bitString = booleanString2booleanArray(row[0])
                    science = float(row[1])
                    cost = float(row[2])
                    self.architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})
            output = self.architectures
            request.session['data']=self.architectures
            return Response(output)
        
        except Exception:
            print('Exception in importing data for iFEED')
            return Response('')





def booleanString2booleanArray(booleanString):
    leng = len(booleanString)
    boolArray = []
    for i in range(leng):
        if booleanString[i]=='0':
            boolArray.append(False)
        else:
            boolArray.append(True)
    return boolArray


