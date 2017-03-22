from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

# Create your views here.
class IFEEDServer(APIView):
    """
    IFEEDServer - testing
    """
    def __init__(self):
        self.root = "/Users/bang/workspace/daphne/iFEED"
        #self.http_method_names = ['get','post'];
        pass
    
    def post(self, request, format=None):
        
        requestID = request.POST['ID']
        
        if(requestID=='import_new_data'):
            # Set the path of the file containing data
            file_path = self.root + request.POST['path']
            # Open the file
            with open(file_path) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=',')
                architectures = []
                # For each row, store the information
                for ind, row in enumerate(read):
                    bitString = booleanString2booleanArray(row[0])
                    science = float(row[1])
                    cost = float(row[2])
                    architectures = np.append(architectures,{'id':ind,'bitString':bitString,'science':science,'cost':cost})
            return Response(architectures.tolist())
        elif(requestID==''):
            pass
        
        
    def get(self, request, format=None):
        return Response({'test':'ifeed_get'})



def booleanString2booleanArray(booleanString):
    leng = len(booleanString)
    boolArray = []
    for i in range(leng):
        if booleanString[i]==0:
            boolArray.append(False)
        else:
            boolArray.append(True)
    return boolArray






class InstrumentList(APIView):
    """
    List all instruments.
    """
    def get(self, request, format=None):
        # Call Java library to get the list of instruments
        # ArrayList<String> instrumentList = new ArrayList<>();
        # String[] instruments = Params.instrument_list;
        # for (String inst:instruments){
        #     instrumentList.add(inst);
        # }
        return Response({'test2':'test2'})
