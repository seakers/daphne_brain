import logging

# Get an instance of a logger
logger = logging.getLogger('data-mining')


from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import datetime
import csv


# Create your views here.
class StartExperiment(APIView):

    def get(self, request, format=None):
        # Obtain ID number
        new_id = len(os.listdir('./experiment_API/results'))

        # Create File so ID does not get repeated
        open('./experiment_API/results/' + str(new_id) + '.json', 'w')

        # Save experiment start info
        request.session['experiment'] = {}
        request.session['experiment']['id'] = new_id
        request.session['experiment']['start_date1'] = datetime.datetime.now().isoformat()
        request.session['experiment']['stage1'] = 'with_ca' if new_id % 2 == 0 else 'without_ca'
        request.session['experiment']['stage2'] = 'without_ca' if new_id % 2 == 0 else 'with_ca'
        request.session['experiment']['dialog'] = []
        request.session['experiment']['architectures'] = []
        request.session['experiment']['architectures'].append({
            'arch': request.session['data'][0],
            'time': datetime.datetime.now().isoformat()
        })
        request.session.modified = True

        return Response(request.session['experiment'])


class FinishStage(APIView):

    def get(self, request, format=None):
        request.session['experiment']['end_date1'] = datetime.datetime.now().isoformat()
        request.session.modified = True
        return Response(request.session['experiment'])


class StartStage(APIView):

    def get(self, request, format=None):
        request.session['experiment']['start_date2'] = datetime.datetime.now().isoformat()
        request.session.modified = True
        return Response(request.session['experiment'])


class ReloadExperiment(APIView):

    def get(self, request, format=None):
        if 'experiment' in request.session:
            return Response(request.session['experiment'])
        else:
            return Response({"error": "Experiment not started!"})
        
        
class EndExperiment(APIView):

    def get(self, request, format=None):
        request.session['experiment']['end_date2'] = datetime.datetime.now().isoformat()
        request.session.modified = True
        # Save experiment results to file
        with open('./experiment_API/results/' + str(request.session['experiment']['id']) + '.json', 'w') as f:
            json.dump(request.session['experiment'], f)

        del request.session['experiment']

        return Response("Correct!")
