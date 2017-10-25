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
import hashlib
from channels import Group

from messagebus.message import Message
from iFEED_API.venn_diagram.intersection import optimize_distance
from config.loader import ConfigurationLoader
#from util.log import getLogger

# Get an instance of a logger
logger = logging.getLogger('iFEED')

config = ConfigurationLoader().load()

class ImportData(APIView):
    
    """ Imports data from a csv file. To be deprecated in the future.

    Request Args:
        path: Relative path to a csv file residing inside iFEED project folder
        
    Returns:
        architectures: a list of python dict containing the basic architecture information.
        
    """
    def post(self, request, format=None):
        try:
            logger.debug('iFEED import data HTTP request')

            # Set the path of the file containing data
            file_path = os.path.dirname(os.path.abspath(__file__)) + '/data/' + request.POST['filename']
            # Open the file
            with open(file_path) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=',')
                architectures = []
                bit_strings = set()
                # For each row, store the information
                for ind, row in enumerate(read):
                    # Change boolean string to boolean array
                    bitString = self.booleanString2booleanArray(row[0])
                    science = float(row[1])
                    cost = float(row[2])

                    logger.debug(bitString)

                    if row[0] not in bit_strings:
                        architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})
                        bit_strings.add(row[0])

            request.session['data'] = architectures
            return Response(architectures)
        
        except Exception:
            logger.exception('Exception in importing data for iFEED')
            return Response('')

    def booleanString2booleanArray(self, booleanString):
        return [b == "1" for b in booleanString]


class VennDiagramDistance(APIView):
    
    """ Optimizes the distance between two circles in a Venn diagram

    Request Args:
        a1: the area of the first circle
        a2: the area of the second circle
        intersection: the intersecting area of two circles
        
    Returns:
        The distance between two circles
        
    """
    def __init__(self):
        pass
    def post(self, request, format=None):
        a1 = float(request.POST['a1'])
        a2 = float(request.POST['a2'])
        intersection = float(request.POST['intersection'])
        res = optimize_distance(a1,a2,intersection)
        
        distance = res.x[0]
        return Response(distance)


class UpdateUtterance(APIView):

    def __init__(self):
        pass
    def post(self, request, format=None):
        
        key = request.POST['key']
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        utteranceSerialized = request.POST['utterance']
        utterances = json.loads(utteranceSerialized)
        
        print(utterances[0])
        
        Group("mycroft").send({
            "text": utterances[0]
        })

        return Response('')


class UpdateSystemResponse(APIView):
    
    def __init__(self):
        pass
    
    def post(self, request, format=None):
        
        print('Update system response')
        
        utterance = request.POST['utterance']
        
        daphneMessage = Message(target=['chat'],content=[utterance],context=None)
        message = daphneMessage.serialize()
        
        key = '1235419'
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        
        Group(hash_key).send({
            "text": message
        })
        return Response('')
    
#class UpdateFeatureApplicationStatus(APIView):
#    
#    """ Makes an update to the Feature Application Status page
#
#    Request Args:
#        key: the user identifier
#        expression: the feature expression
#        option: options in updating a new feature. Should be one of {'new','add','within','remove','deactivated','temp'}
#
#    """    
#    def post(self,request,format=None):
#        
#        key = request.POST['key']
#        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
#        expression = request.POST['expression']
#        option = request.POST['option']
#        
#        data = {'target':'ifeed.feature_application_status',
#                'id':'update',
#                'expression':expression,
#                'option':option}
#        message = json.dumps(data)
#        
#        Group(hash_key).send({
#            "text": message
#        })
#        return Response('')
#        
#        
#        
#class RequestFeatureApplicationStatus(APIView):
#    
#    """ Makes a request to Feature Application Status page for updates
#
#    Request args:
#        key: the user identifier
#        source: the source name
#    """    
#    def post(self,request):
#        
#        key = request.POST['key']
#        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
#        #source = request.POST['source']
#        
#        data = {'target':'ifeed.feature_application_status',
#                'id':'request'}
#        message = json.dumps(data)
#        
#        Group(hash_key).send({
#            "text": message
#        })
#        return Response('')        

    
class ApplyFeatureExpression(APIView):
    
    """ Applies a feature in the main iFEED GUI

    Request args:
        key: the user identifier
        source: the source name
        expression: expression of the feature
        option: options in applying the feature
    """    
    
    def post(self,request):
        
        key = request.POST['key']
        hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        source = request.POST['source']
        expression = request.POST['expression']
        option = request.POST['option']
        
        if option=='apply':
            id = 'apply_feature'
        elif option=='update':
            id = 'update_feature'
        elif option=='test':
            id = 'test_feature'

        data = {'target':'ifeed',
                'id':id, 
                'expression':expression,
                'source':source}
        message = json.dumps(data)
        
        Group(hash_key).send({
            "text": message
        })
        return Response('')
