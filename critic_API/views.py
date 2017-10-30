from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
import json

from VASSAR_API.api import VASSARClient

from critic_API.historian_critic import Critic


# Get an instance of a logger
logger = logging.getLogger('critic')


        
class CriticizeArchitecture(APIView):
    
    
    def post(self, request, format=None):
        try:
            
            inputs = request.POST['inputs']   
                        
            inputs = json.loads(inputs)            
            
            critique = self.get_history_critique(inputs)
            
            critique = self.get_expert_critique(inputs)
                                
            return Response(critique)
        
        except Exception:
            
            logger.exception('Exception in generating a critique of an architecture')
            return Response('')
                

    def get_history_critique(self,inputs):

        try:

            historian_critic = Critic()

            historian_critic.criticizeArchitecture(inputs)

        except Exception:
            logger.exception('Exc in generating a critique using historical database')
            raise


    def get_expert_critique(self,inputs):

        try:
            self.VASSARClient = VASSARClient()

            # Start connection with VASSAR
            self.VASSARClient.startConnection()

            critique = self.VASSARClient.critiqueArchitecture(inputs)            

            # End the connection before return statement
            self.VASSARClient.endConnection()

        except Exception:
            logger.exception('Exc in generating a critique using expert knowledge base')
            self.VASSARClient.endConnection()
            
            raise
        