from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv


sys.path.append("/Users/bang/workspace/daphne/daphne-brain/VASSAR_API/")
# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)

from VASSAR_API.VASSAR_client import VASSAR_client



class getOrbitList(APIView):
    def __init__(self):
        self.VASSAR_client = VASSAR_client()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSAR_client.startConnection()
            list = self.VASSAR_client.getOrbitList()
            
            # End the connection before return statement
            self.VASSAR_client.endConnection()
            return Response(list)
        
        except Exception:
            print('Exception in getting the orbit list')
            self.VASSAR_client.endConnection()
            return Response('')


class getInstrumentList(APIView):
    def __init__(self):
        self.VASSAR_client = VASSAR_client()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSAR_client.startConnection()
            list = self.VASSAR_client.getInstrumentList()
            
            # End the connection before return statement
            self.VASSAR_client.endConnection()
            return Response(list)
        
        except Exception:
            print('Exception in getting the orbit list')
            self.VASSAR_client.endConnection()
            return Response('')


class initializeJess(APIView):
    def __init__(self):
        self.VASSAR_client = VASSAR_client()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSAR_client.startConnection()
            message = self.VASSAR_client.initializeJess()
            # End the connection before return statement
            self.VASSAR_client.endConnection()
            return Response(message)
        
        except Exception:
            print('Exception in initializing jess')
            self.VASSAR_client.endConnection()
            return Response('')


class evaluateArchitecture(APIView):
    def __init__(self):
        self.VASSAR_client = VASSAR_client()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSAR_client.startConnection()
            architecture = self.VASSAR_client.evaluateArchitecture()
            # End the connection before return statement
            self.VASSAR_client.endConnection()
            return Response(architecture)
        
        except Exception:
            print('Exception in initializing jess')
            self.VASSAR_client.endConnection()
            return Response('')



