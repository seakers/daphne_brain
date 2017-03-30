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

from data_mining_API.data_mining_client import data_mining_client


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
            return Response(output)
        
        except Exception:
            print('Exception in importing data for iFEED')
            return Response('')
        




"""
# Create your views here.
class IFEEDServer(APIView):

    def __init__(self):
        self.data_mining_client = data_mining_client()
        #self.http_method_names = ['get','post'];
        pass
    
    def post(self, request, format=None):
        
        try:
            
            # Start connection with VASSAR
            requestID = request.POST['ID']
            output = ''

                
            elif(requestID=='get_driving_features'):
                
                # Start data mining client
                self.data_mining_client.startConnection()
                
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

                # Temporary implementation of importing architecture data from csv file.
                # Should be changed after implementing database
                # Set the path of the file containing data
                file_path = root_ifeed + '/results/EOSS_data.csv'
                # Open the file
                with open(file_path) as csvfile:
                    # Read the file as a csv file
                    read = csv.reader(csvfile, delimiter=',')
                    self.architectures = []
                    # For each row, store the information
                    for ind, row in enumerate(read):
                        # Change boolean string to boolean array
                        bitString = row[0]
                        science = float(row[1])
                        cost = float(row[2])
                        self.architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})

                drivingFeatures = self.data_mining_client.getDrivingFeatures(behavioral,non_behavioral,self.architectures,supp,conf,lift)
                    
                output = drivingFeatures
                

            # End the connection before return statement
            self.data_mining_client.endConnection() 
            return Response(output)
        
        except Exception:
            print('Exception in IFEED HTTP Request POST')
            self.data_mining_client.endConnection()
            return Response('')
        
    def get(self, request, format=None):
        return Response({'test':'ifeed_get'})





"""













def booleanString2booleanArray(booleanString):
    leng = len(booleanString)
    boolArray = []
    for i in range(leng):
        if booleanString[i]=='0':
            boolArray.append(False)
        else:
            boolArray.append(True)
    return boolArray


