import logging
import os
import json
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response

# Get an instance of a logger
logger = logging.getLogger('experiment')

def stage_type(id, stage_num):
    if id % 2 == 0:
        if stage_num == 0:
            return 'daphne_assistant'
        else:
            return 'daphne_peer'
    else:
        if stage_num == 0:
            return 'daphne_peer'
        else:
            return 'daphne_assistant'


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

        if 'context' not in request.session:
            request.session['context'] = {}
        request.session['context']['in_experiment'] = True

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
        request.session['experiment']['stages'][stage]['end_state'] = request.session['experiment']['state']
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
        request.session['context']['in_experiment'] = False
        request.session['vassar_port'] = 9090

        request.session.modified = True

        return Response('Correct!')
