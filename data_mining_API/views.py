import logging

# Get an instance of a logger
from auth_API.helpers import get_or_create_user_information
from daphne_API.models import Design

logger = logging.getLogger('data-mining')


from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys
import os
import json
import csv

# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)

from data_mining_API.api import DataMiningClient


# Create your views here.
class GetDrivingFeatures(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
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

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.POST['problem']
            inputType = request.POST['input_type']

            drivingFeatures = self.DataMiningClient.getDrivingFeatures(problem, inputType, behavioral, non_behavioral,
                                                                       dataset, supp, conf, lift)

            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetDrivingFeaturesEpsilonMOEA(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
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

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.POST['problem']
            inputType = request.POST['input_type']

            drivingFeatures = self.DataMiningClient.getDrivingFeaturesEpsilonMOEA(problem, inputType, behavioral, non_behavioral, dataset)
            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetDrivingFeaturesWithGeneralization(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
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

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.POST['problem']
            inputType = request.POST['input_type']

            drivingFeatures = self.DataMiningClient.getDrivingFeaturesWithGeneralization(problem, inputType, behavioral, non_behavioral, dataset)

            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetMarginalDrivingFeatures(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
            # Get threshold values for the metrics
            supp = float(request.POST['supp'])
            conf = float(request.POST['conf'])
            lift = float(request.POST['lift'])
            
            # Get selected arch id's
            behavioral = json.loads(request.POST['selected'])
            non_behavioral = json.loads(request.POST['non_selected'])
                
            featureExpression = request.POST['featureExpression']      
            logicalConnective = request.POST['logical_connective']      

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.POST['problem']
            inputType = request.POST['input_type']

            drivingFeatures = self.DataMiningClient.getMarginalDrivingFeatures(problem, inputType, behavioral,non_behavioral,dataset,
                                                                               featureExpression,logicalConnective, supp,conf,lift)            
            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + detail)
            self.DataMiningClient.endConnection()
            return Response('')


class GeneralizeFeature(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
            # Get selected arch id's
            behavioral = json.loads(request.POST['selected'])
            non_behavioral = json.loads(request.POST['non_selected'])
                
            rootFeatureExpression = request.POST['rootFeatureExpression']      
            nodeFeatureExpression = request.POST['nodeFeatureExpression']    

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.POST['problem']
            inputType = request.POST['input_type']

            drivingFeatures = self.DataMiningClient.generalizeFeature(problem, inputType, 
                                                                behavioral,non_behavioral,
                                                                dataset,
                                                                rootFeatureExpression, nodeFeatureExpression)

            output = drivingFeatures

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(output)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + detail)
            self.DataMiningClient.endConnection()
            return Response('')


class ClusterData(APIView):

    def __init__(self):
        pass

    def post(self, request, format=None):
        
        try:

            param = int(request.POST['param'])

            problem = request.POST['problem']
            inputType = request.POST['input_type']

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

            # Load architecture data from the session info
            architectures = request.session['data']

            data = []
            for arch in architectures:
                if arch['id'] in behavioral:
                    data.append(arch['outputs'])
                else:
                    pass

            id_list = behavioral

            # dir_path = os.path.dirname(os.path.realpath(__file__))
            # with open(os.path.join(dir_path,"data.csv"), "w") as file:

            #     for i, row in enumerate(data):
            #         out = []
            #         out.append(str(id_list[i]))

            #         for val in row:
            #             out.append(str(val))
            #         out = ",".join(out)
            #         file.write(out + "\n")

            from cluster import Clustering
            
            clustering = Clustering(data)

            labels = clustering.kMeans(param)

            out = {
                "id": id_list,
                "labels": labels
            }
            
            return Response(out)
        
        except Exception as detail:
            logger.exception('Exception in clustering: ' + str(detail))
            return Response('')


class GetCluster(APIView):

    def __init__(self):
        pass

    def post(self, request, format=None):
        try:

            dir_path = os.path.dirname(os.path.realpath(__file__))
            labels = []
            id_list = []

            with open(os.path.join(dir_path,"labels.csv"), "r") as file:

                content = file.read().split("\n")

                for row in content:
                    if row == "":
                        continue
                    elif "," in row:
                        id_list.append(row.split(",")[0])
                        labels.append(row.split(",")[1])
                    else:
                        labels.append(row)

            out = {
                "id": id_list,
                "labels": labels
            }
            return Response(out)
        
        except Exception as detail:
            logger.exception('Exception in getting cluster labels: ' + str(detail))
            return Response('')        


class ConvertToDNF(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.POST['expression']
            dnf_expression = self.DataMiningClient.convertToDNF(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(dnf_expression)
        
        except Exception as detail:
            logger.exception('Exception in convertingToDNF: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ConvertToCNF(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.POST['expression']
            cnf_expression = self.DataMiningClient.convertToCNF(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(cnf_expression)
        
        except Exception as detail:
            logger.exception('Exception in convertingToCNF: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeTypicality(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            # Get selected arch id's
            inputString = request.POST['input']
            inputString = inputString[1:-1]
            inputSplit = inputString.split(',')

            # Convert strings to ints
            inputs = []
            for i in inputSplit:
                inputs.append(int(i))

            # Get the expression
            expression = request.POST['expression']
            typicality = self.DataMiningClient.computeTypicality(inputs, expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(typicality)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexity: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeComplexity(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.POST['expression']
            complexity = self.DataMiningClient.computeComplexity(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(complexity)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexity: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeComplexityOfFeatures(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expressions = request.POST['expressions']
            expressions = json.loads(expressions)

            complexity = self.DataMiningClient.computeComplexityOfFeatures(expressions)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(complexity)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexityOfFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetProblemParameters(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.POST['problem']
            params = self.DataMiningClient.getProblemParameters(problem)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(params)
        
        except Exception as detail:
            logger.exception('Exception in GetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class SetProblemParameters(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.POST['problem']
            params = json.loads(request.POST['params'])

            self.DataMiningClient.setProblemParameters(problem, params)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response()
        
        except Exception as detail:
            logger.exception('Exception in SetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')

class SetProblemGeneralizedConcepts(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.POST['problem']
            params = json.loads(request.POST['params'])

            self.DataMiningClient.setProblemGeneralizedConcepts(problem, params)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response()
        
        except Exception as detail:
            logger.exception('Exception in SetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')

class getProblemConceptHierarchy(APIView):

    def __init__(self):
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.POST['problem']
            params = json.loads(request.POST['params'])

            conceptHierarchy = self.DataMiningClient.getProblemConceptHierarchy(problem, params)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(conceptHierarchy)
        
        except Exception as detail:
            logger.exception('Exception in calling getProblemConceptHierarchy: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


def booleanArray2booleanString(booleanArray):
    leng = len(booleanArray)
    boolString = ''
    for i in range(leng):
        if booleanArray[i] == True:
            boolString += '1'
        else:
            boolString += '0'
    return boolString


class ImportTargetSelection(APIView):

    def post(self, request, format=None):
        try:
            filename = request.POST['filename']
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

            selected_arch_ids = []

            with open(file_path, "r") as file:

                content = file.read().split("\n")

                for row in content:
                    if row == "":
                        continue

                    elif "," in row:
                        id = row.split(",")[0]
                        label = row.split(",")[1]

                        if label == "1":
                            selected_arch_ids.append(int(id))

            return Response(selected_arch_ids)
        
        except Exception as detail:
            logger.exception('Exception in getting cluster labels: ' + str(detail))
            return Response('') 


class ExportTargetSelection(APIView):

    def post(self, request, format=None):
        try:
            problem = request.POST['problem']
            inputType = request.POST['input_type']
            filename = request.POST['name']

            import datetime
            timestamp = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")

            if filename is None:
                filename = ""
            else:
                pass
            filename = filename + "_" + timestamp + ".selection"

            # Set the path of the file containing data
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

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

            # Load architecture data from the session info
            architectures = request.session['data']

            #########################################
            #########################################
            ### Write data file with labels

            with open(file_path, "w") as file:

                content = []
                for i, arch in enumerate(architectures):
                    line = []

                    archID = arch['id']
                    label = None
                    if archID in behavioral:
                        label = "1"
                    else:
                        label = "0"

                    inputs = arch['inputs']
                    inputString = ""
                    for val in inputs:
                        if val:
                            inputString += "1"
                        else:
                            inputString += "0"

                    line.append(str(archID))
                    line.append(str(label))
                    line.append(inputString)
                    content.append(",".join(line))    

                file.write("\n".join(content))

            #########################################
            #########################################

            return Response('')
        
        except Exception:
            logger.exception('Exception in importing feature data')
            return Response('')


class ImportFeatureData(APIView):

    def post(self, request, format=None):
        try:
            # Set the path of the file containing data
            filename_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', request.POST['filename_data'])
            filename_params = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', request.POST['filename_params'])

            out = {}
            out['params'] = []
            out['data'] = []
            features = []

            # Open the data file
            with open(filename_data) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=' ')

                # For each row, store the information
                for i, row in enumerate(read):
                    if i == 0: # Check if the first line is a header
                        if row[0].startswith("#"):
                            continue

                    index = int(row[0])
                    feature_expression = row[1]

                    if len(row) > 5: # All metrics are included
                        support = float(row[2])
                        lift = float(row[3])
                        coverage = float(row[4])
                        specificity = float(row[5])
                        complexity = float(row[6])
                        metrics = [support, lift, coverage, specificity]
                        
                    else: # Only coverage and specificity are included in the data
                        coverage = float(row[2])
                        specificity = float(row[3])
                        complexity = float(row[4])
                        metrics = [-1, -1, coverage, specificity]

                    features.append({'id':index, 'name':feature_expression, 'expression':feature_expression, 'metrics':metrics, 'complexity': complexity})

            # Import parameters
            params = None
            if os.path.isfile(filename_params):
                # Open the file
                with open(filename_params) as csvfile:

                    # Read the file as a csv file
                    read = csv.reader(csvfile, delimiter=',')

                    paramNames = []
                    params = {}

                    # For each row, store the information
                    for i, row in enumerate(read):
                        if i == 0: # Check if the first line is a header
                            if row[0].startswith("#"):
                                for cell in row:
                                    if cell.startswith("#"):
                                        paramNames.append(cell[1:].strip())
                                    else:
                                        paramNames.append(cell.strip())
                                continue

                        # Get param name
                        paramName = None
                        if len(paramNames) != 0:
                            paramName = paramNames[i - 1]
                        else:
                            paramName = "param" + str(i)

                        params[paramName] = []
                        for cell in row:    
                            params[paramName].append(cell)

            out['data'] = features
            out['params'] = params
            return Response(out)
        
        except Exception:
            logger.exception('Exception in importing feature data')
            return Response('')
