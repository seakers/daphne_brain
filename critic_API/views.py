from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
import json

from importlib import import_module
from django.conf import settings
from daphne_brain.session_lock import session_lock
from VASSAR_API.api import VASSARClient

#from critic_API.historian_critic import Critic


# Get an instance of a logger
logger = logging.getLogger('critic')
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

        
class CriticizeArchitecture(APIView):
    
    
    def post(self, request, format=None):
        try:
            store = SessionStore(request.session.session_key)
            port = store['vassar_port'] if 'vassar_port' in store else 9090
            
            inputs = request.POST['inputs']   
                        
            inputs = json.loads(inputs)            
            
            critique = self.get_history_critique(inputs)
            
            critique += self.get_expert_critique(inputs, port)
            
            critiques = json.dumps(critique)
                                
            return Response(critiques)
        
        except Exception:
            
            logger.exception('Exception in generating a critique of an architecture')
            return Response('')
                

    def get_history_critique(self, inputs):

        try:
            pass
#            historian_critic = Critic()
#
#            critique = historian_critic.criticizeArchitecture(inputs)
#            
#            return critique

        except Exception:
            logger.exception('Exc in generating a critique using historical database')
            
            raise


    def get_expert_critique(self, inputs, port):

        try:
            self.VASSARClient = VASSARClient(port)

            # Start connection with VASSAR
            self.VASSARClient.startConnection()

            critique = self.VASSARClient.critiqueArchitecture(inputs, False)

            # End the connection before return statement
            self.VASSARClient.endConnection()

        except Exception:
            logger.exception('Exc in generating a critique using expert knowledge base')
            self.VASSARClient.endConnection()
            
            raise
        