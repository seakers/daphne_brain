from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv


sys.path.append("/Users/bang/workspace/daphne/daphne-brain/data_mining_API/")
# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)

from data_mining_API.api import DataMiningClient



# Create your views here.
class getDrivingFeatures(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass
    
    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get threshold values for the metrics
            supp = float(request.POST['supp'])
            conf = float(request.POST['conf'])
            lift = float(request.POST['lift'])
            
            # Get selected arch id's
            selected = request.POST['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))
            
            # Get non-selected arch id's
            non_selected = request.POST['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            architectures = request.session['data']
            for a in architectures:
                temp = a['bitString']
                a['bitString'] = booleanArray2booleanString(temp)

            drivingFeatures = self.DataMiningClient.getDrivingFeatures(behavioral,non_behavioral,architectures,supp,conf,lift)
                
            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            print('Exception in getDrivingFeatures: ' + detail)
            self.DataMiningClient.endConnection()
            return Response('')



def booleanArray2booleanString(booleanArray):
    leng = len(booleanArray)
    boolString = ''
    for i in range(leng):
        if booleanArray[i]==True:
            boolString = boolString + '1';
        else:
            boolString = boolString + '0';
    return boolString

