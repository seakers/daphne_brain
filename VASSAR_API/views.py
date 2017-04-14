from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv


# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)

sys.path.append("/Users/bang/workspace/daphne/daphne-brain/VASSAR_API/")
from api import VASSARClient



class GetOrbitList(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getOrbitList()
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            print('Exception in getting the orbit list')
            self.VASSARClient.endConnection()
            return Response('')


class GetInstrumentList(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getInstrumentList()
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            print('Exception in getting the instrument list')
            self.VASSARClient.endConnection()
            return Response('')


class InitializeJess(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            message = self.VASSARClient.initializeJess()
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(message)
        
        except Exception:
            print('Exception in initializing jess')
            self.VASSARClient.endConnection()
            return Response('')


class EvaluateArchitecture(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            architecture = self.VASSARClient.evaluateArchitecture()
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architecture)
        
        except Exception:
            print('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')



