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

sys.path.append("/Users/bang/workspace/daphne/daphne-brain/data_mining_API/")
sys.path.append("/Users/bang/workspace/daphne/daphne-brain/VASSAR_API/")

# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)

from data_mining_API.data_mining_client import data_mining_client as DataMiningClient
from VASSAR_API.VASSAR_client import VASSAR_client as VASSARClient


# Create your views here.
class IFEEDServer(APIView):
    """
    IFEEDServer
    """
    def __init__(self):
        self.VASSARClient = VASSARClient()
        self.DataMiningClient = DataMiningClient()
        print('...IFEEDServer init')
        #self.http_method_names = ['get','post'];
        pass
    
    def post(self, request, format=None):
        
        try:
            
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
                    self.architectures = []
                    # For each row, store the information
                    for ind, row in enumerate(read):
                        # Change boolean string to boolean array
                        bitString = booleanString2booleanArray(row[0])
                        science = float(row[1])
                        cost = float(row[2])
                        self.architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})
                output = self.architectures
    
            
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
                
            elif(requestID=='get_driving_features'):
                
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
                
                
                drivingFeatures = self.DataMiningClient.getDrivingFeatures(behavioral,non_behavioral,self.architectures,supp,conf,lift)
                output = drivingFeatures
                self.DataMiningClient.endConnection()

            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(output)
        
        except Exception:
            print('Exception in IFEED HTTP Request POST')
            self.VASSARClient.endConnection()
            self.DataMiningClient.endConnection()
            return Response('')
        
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


