import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from VASSAR_API.api import VASSARClient

# Get an instance of a logger
logger = logging.getLogger('VASSAR')


class GetOrbitList(APIView):
    
    def get(self, request, format=None):
        try:
            # Start connection with VASSAR
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
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

    def get(self, request, format=None):
        try:
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
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
    
    def post(self, request, format=None):
        try:
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architecture = self.VASSARClient.evaluateArchitecture(inputs)

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []
            if 'context' not in request.session:
                request.session['context'] = {}
            if 'current_design_id' not in request.session['context']:
                request.session['context']['current_design_id'] = None

            is_same = True
            for old_arch in request.session['data']:
                is_same = True
                for i in range(len(old_arch['outputs'])):
                    if old_arch['outputs'][i] != architecture['outputs'][i]:
                        is_same = False
                if is_same:
                    break

            if not is_same:
                architecture['id'] = len(request.session['data'])
                request.session['context']['current_design_id'] = architecture['id']
                print(request.session['context']['current_design_id'])
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

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
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


class ChangePort(APIView):

    def post(self, request, format=None):
        new_port = request.data['port']
        request.session['vassar_port'] = new_port
        request.session.modified = True
        return Response('')