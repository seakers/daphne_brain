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
import datetime

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
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            if 'special' in request.data:
                special = request.data['special']
            else:
                special = 'False'
            if special == 'True':
                architecture = self.VASSARClient.evaluateSpecialArchitecture(inputs)
            elif special == 'False':
                architecture = self.VASSARClient.evaluateArchitecture(inputs)
            else:
                return Response('Error parsing special field.')

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []

            if 'context' not in request.session:
                request.session['context'] = {}
            if 'current_design_id' not in request.session['context']:
                request.session['context']['current_design_id'] = None
            
            architecture['id'] = len(request.session['data'])
            request.session['context']['current_design_id'] = architecture['id']
            request.session['data'].append(architecture)

            request.session.modified = True
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architecture)
        
        except Exception:
            logger.exception('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')
        
        
        
class RunLocalSearch(APIView):
    def __init__(self):
        self.VASSARClient = VASSARClient()
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architectures = self.VASSARClient.runLocalSearch(inputs)    

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []
                
            if 'archID' not in request.session:
                request.session['archID'] = None

            self.architectures = request.session['data']
            self.archID = request.session['archID'] 
            
            if self.archID is None:
                self.archID = 0
                
            for arch in architectures:                
                arch['id'] = self.archID
                self.archID += 1
                self.architectures.append(arch)
            
            request.session['archID'] = self.archID            
            request.session['data'] = self.architectures
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architectures)
        
        except Exception:
            logger.exception('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')


class ChangeLoadedFiles(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.VASSARClient = VASSARClient()

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            param_map = json.loads(request.data['loaded_files'])
            result = self.VASSARClient.changeLoadedFiles(param_map)
            self.VASSARClient.endConnection()
            return Response({ 'result': result })

        except Exception:
            logger.exception('Exception in changing some parameters')
            self.VASSARClient.endConnection()
            return Response('')