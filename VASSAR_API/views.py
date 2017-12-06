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
                        
            inputs = request.POST['inputs']   
                        
            inputs = json.loads(inputs)
            
            architecture = self.VASSARClient.evaluateArchitecture(inputs)    

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []
                
            if 'archID' not in request.session:
                request.session['archID'] = None

            self.architectures = request.session['data']
            self.archID = request.session['archID'] 
            
            if self.archID is None:
                self.archID = 0
            
            architecture['id'] = self.archID
            
            self.archID += 1
            self.architectures.append(architecture)
            
            request.session['archID'] = self.archID            
            request.session['data'] = self.architectures

            # save data for experiment
            if 'experiment' in request.session:
                if 'start_date2' not in request.session['experiment']:
                    architectures_name = 'architectures1'
                else:
                    architectures_name = 'architectures2'
                request.session['experiment'][architectures_name].append({
                    'arch': architecture,
                    'time': datetime.datetime.now().isoformat()
                })

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
                        
            inputs = request.POST['inputs']   
                        
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