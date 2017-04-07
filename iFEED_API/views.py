from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv
from channels import Group


# Print all paths included in sys.path
#from pprint import pprint as p
#p(sys.path)

from iFEED_API.venn_diagram.intersection import optimize_distance
from config.loader import ConfigurationLoader

config = ConfigurationLoader().load()


class ImportData(APIView):
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
                    
                    rep = False
                    for i,a in enumerate(self.architectures):
                        # Check if the current bitString was seen before
                        if a['bitString'] == bitString:
                            rep = True
                            break
                    if rep:
                        pass
                    else:
                        self.architectures.append({'id':ind,'bitString':bitString,'science':science,'cost':cost})
            output = self.architectures
            request.session['data']=self.architectures
            return Response(output)
        
        except Exception:
            print('Exception in importing data for iFEED')
            return Response('')


class ApplyFilter(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        temp = request.POST['content']
        print(temp)
        text = "apply_pareto_filter"
        Group("ifeed").send({
            "text": text
        })
        return Response('')
    
class CancelSelections(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        #text = request.POST['']
        text = "cancel_selections"
        Group("ifeed").send({
            "text": text
        })
        return Response('')
    
class VennDiagramDistance(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        a1 = float(request.POST['a1'])
        a2 = float(request.POST['a2'])
        intersection = float(request.POST['intersection'])
        res = optimize_distance(a1,a2,intersection)
        
        distance = res.x[0]
        return Response(distance)
    
class UpdateFeatureStatusChart(APIView):
    
    def post(self,request,format=None):
        
        expression = request.POST['expression']
        conf_given_f = float(request.POST['conf_given_f'])
        conf_given_s = float(request.POST['conf_given_s'])
        lift = float(request.POST['lift'])
        
        payload = {'expression':expression,
                  'conf_given_f':conf_given_f,
                  'conf_given_s':conf_given_s,
                  'lift':lift}
        message = json.dumps(payload)
        print(message)
        
        Group("ifeed-feature").send({
            "text": message
        })
        return Response('')
    
    
    
        
def booleanString2booleanArray(booleanString):
    leng = len(booleanString)
    boolArray = []
    for i in range(leng):
        if booleanString[i]=='0':
            boolArray.append(False)
        else:
            boolArray.append(True)
    return boolArray
