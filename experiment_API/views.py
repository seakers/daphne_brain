import logging

# Get an instance of a logger
logger = logging.getLogger('data-mining')

from rest_framework.views import APIView
from rest_framework.response import Response

import os
import json
import datetime

def stage_type(id, stage_num):
    if id % 4 <= 1:
        if stage_num % 2 == 0:
            return 'no_daphne'
        else:
            if id % 2 == 0:
                return 'daphne_assistant'
            else:
                return 'daphne_peer'
    else:
        if stage_num % 2 == 0:
            if id % 2 == 0:
                return 'daphne_assistant'
            else:
                return 'daphne_peer'
        else:
            return 'no_daphne'

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
        request.session['experiment']['stages'] = []
        request.session['experiment']['state'] = {}

        # Specific to current experiment
        request.session['experiment']['stages'].append({
            'type': stage_type(request.session['experiment']['id'], 0),
            'actions': []
        })
        request.session['experiment']['stages'].append({
            'type': stage_type(request.session['experiment']['id'], 1),
            'actions': []
        })
        request.session.modified = True

        return Response(request.session['experiment'])


class StartStage(APIView):

    def get(self, request, stage, format=None):
        request.session['experiment']['stages'][stage]['start_date'] = datetime.datetime.utcnow().isoformat()
        request.session.modified = True

        return Response(request.session['experiment'])


class FinishStage(APIView):

    def get(self, request, stage, format=None):
        request.session['experiment']['stages'][stage]['end_date'] = datetime.datetime.utcnow().isoformat()
        request.session.modified = True
        return Response(request.session['experiment'])


class AddAction(APIView):

    def post(self, request, stage, format=None):
        action = request.data['action']
        action['date'] = datetime.datetime.utcnow().isoformat()
        request.session['experiment']['stages'][stage]['actions'].append(action)
        request.session.modified = True
        return Response(request.session['experiment'])


class UpdateState(APIView):

    def post(self, request, format=None):
        request.session['experiment']['state'] = request.data['state']
        request.session.modified = True
        return Response(request.session['experiment'])


class ReloadExperiment(APIView):

    def get(self, request, format=None):
        if 'experiment' in request.session:
            return Response({ 'is_running': True, 'experiment_data': request.session['experiment'] })
        else:
            return Response({ 'is_running': False })
        
        
class FinishExperiment(APIView):

    def get(self, request, format=None):
        # Save experiment results to file
        with open('./experiment_API/results/' + str(request.session['experiment']['id']) + '.json', 'w') as f:
            json.dump(request.session['experiment'], f)

        del request.session['experiment']

        return Response('Correct!')
