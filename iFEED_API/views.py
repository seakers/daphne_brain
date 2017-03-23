from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

root = "/Users/bang/workspace/daphne/daphne-brain"
root_ifeed = "/Users/bang/workspace/daphne/iFEED"
sys.path.append(root+'/VASSAR_API')

from PythonClient import pyClient

# Create your views here.
class IFEEDServer(APIView):
    """
    IFEEDServer
    """
    def __init__(self):
        self.VASSARClient = pyClient()
        #self.http_method_names = ['get','post'];
        pass
    
    def post(self, request, format=None):
        
        # Start connection with VASSAR
        self.VASSARClient.startConnection()
        requestID = request.POST['ID']
        output = ''
        
        if(requestID=='import_new_data'):
            # Set the path of the file containing data
            file_path = root_ifeed + request.POST['path']
            # Open the file
            with open(file_path) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=',')
                architectures = []
                # For each row, store the information
                for ind, row in enumerate(read):
                    # Change boolean string to boolean array
                    bitString = booleanString2booleanArray(row[0])
                    science = float(row[1])
                    cost = float(row[2])
                    architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})
            output = architectures

        
        elif(requestID=='get_orbit_list'):
            list = self.VASSARClient.getOrbitList()
            output = list
        
        elif(requestID=='get_instrument_list'):
            list = self.VASSARClient.getInstrumentList()
            output = list

        elif(requestID=='extract_info_from_bitString'):
            bitString = request.POST['bitString']
            orbitList = self.VASSARClient.getOrbitList()
            instrList = self.VASSARClient.getInstrumentList()
            # Compute the number of orbits and instruments
            norb = len(orbitList)
            ninstr = len(instrList)
            
            architecture = []
            for i in range(norb):
                orbit = orbitList[i]
                assigned = []
                for j in range(ninstr):
                    if bitString[i*ninstr+j]=='1':
                        instrument = instrList[j]
                        # Store the instrument names assigned to jth orbit
                        assigned.append(instrument)
                # Store the name of the orbit and the assigned instruments
                architecture.append({'orbit':orbit,'children':assigned})
            output = architecture
        
        # End the connection before return statement
        self.VASSARClient.endConnection()
        return Response(output)
        
    def get(self, request, format=None):
        return Response({'test':'ifeed_get'})



def booleanString2booleanArray(booleanString):
    leng = len(booleanString)
    boolArray = []
    for i in range(leng):
        if booleanString[i]=='0':
            boolArray.append(False)
        else:
            boolArray.append(True)
    return boolArray


