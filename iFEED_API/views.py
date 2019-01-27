import logging
import os
import csv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv
import hashlib
import datetime
from random import *


from iFEED_API.venn_diagram.intersection import optimize_distance
from config.loader import ConfigurationLoader


# Get an instance of a logger
logger = logging.getLogger('iFEED')

config = ConfigurationLoader().load()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


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
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', request.POST['file_path'])
            
            inputType = request.POST['input_type']
            inputNum = int(request.POST['input_num'])
            outputNum = int(request.POST['output_num'])
            problem = request.POST['problem']

            self.archID = 0

            # Open the file
            with open(file_path) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=',')

                self.architectures = []

                inputs_unique_set = set()
                # For each row, store the information
                for ind, row in enumerate(read):
                    if ind == 0: # Check if the first line is a header
                        header = False
                        for cell in row:
                            if not is_number(cell) and cell != "": 
                                # If one of the entries is not a number or an empty string
                                # First line is a header
                                header = True
                                break
                        if header:
                            continue

                    inputs = []
                    outputs = []

                    if problem == "Constellation_10":
                        # Filter out outliers

                        if float(row[40]) > 22000: # mean_resp
                            continue
                        elif float(row[41]) > 93000: # latency
                            continue
                        else:
                            if random() > 0.1:
                                continue

                    # Import inputs
                    for i in range(inputNum):
                        if inputType == "binary": 
                            # Assumes that there is only one column for the inputs
                            inputs = self.booleanString2booleanArray(row[i])
                        elif inputType == "discrete":
                            inp = row[i]
                            inp = int(inp)
                            inputs.append(inp)
                        else:
                            inp = row[i]
                            if inp == "":
                                inp = -1
                            else:
                                inp = float(inp)
                            inputs.append(inp)

                    for i in range(outputNum):
                        out = row[i + inputNum]
                        if out == "":
                            out = 0
                        else:
                            out = float(out)
                        outputs.append(out)

                    hashedInput = hash(tuple(inputs))
                    if hashedInput not in inputs_unique_set:
                        self.architectures.append({'id':self.archID, 'inputs':inputs, 'outputs':outputs})
                        self.archID += 1
                        inputs_unique_set.add(hashedInput)
                    else:
                        #print(hashedInput)
                        pass

            # Define context and see if it was already defined for this session
            request.session['data'] = self.architectures
            request.session['archID'] = self.archID
            request.session.modified = True

            return Response(self.architectures)
        
        except Exception:
            logger.exception('Exception in importing data for iFEED')
            return Response('')

    def booleanString2booleanArray(self, booleanString):
        return [b == "1" for b in booleanString]
    

    
class SetTargetRegion(APIView):

    def post(self, request, format=None):
        try:
            logger.debug('iFEED set target region')
            
            # Get selected arch id's
            selected = request.POST['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            
            # Convert strings to ints
            behavioral = []
            if selected_arch_ids:
                for s in selected_arch_ids:
                    if not len(s)==0:
                        behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.POST['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')

            # Convert strings to ints
            non_behavioral = []
            if non_selected_arch_ids:
                for s in non_selected_arch_ids:
                    if not len(s)==0:
                        non_behavioral.append(int(s))

            # Define context and see if it was already defined for this session
            if 'context' not in request.session:
                request.session['context'] = {}
            
            # Update context information
            request.session['context']['behavioral'] = behavioral
            request.session['context']['non_behavioral'] = non_behavioral
                        
            return Response('')
        
        except Exception:
            logger.exception('Exception in setting the target region for iFEED')
            return Response('')

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
