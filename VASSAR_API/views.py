import logging

from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

from VASSAR_API.api import VASSARClient

# Get an instance of a logger
logger = logging.getLogger('VASSAR')


class GetOrbitList(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def get(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getOrbitList()
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            logger.exception('Exception in getting the orbit list')
            self.VASSARClient.endConnection()
            return Response('')


class GetInstrumentList(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def get(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getInstrumentList()
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            logger.exception('Exception in getting the instrument list')
            self.VASSARClient.endConnection()
            return Response('')


class EvaluateArchitecture(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
                        
            inputs = request.POST['inputs']   
                        
            inputs = json.loads(inputs)
            
            architecture = self.VASSARClient.evaluateArchitecture(inputs)            
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architecture)
        
        except Exception:
            logger.exception('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')
