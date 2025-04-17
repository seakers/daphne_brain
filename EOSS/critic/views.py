import logging
import json

from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information


# Get an instance of a logger
logger = logging.getLogger('EOSS.critic')

        
class CriticizeArchitecture(APIView):
    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            
            inputs = request.data['inputs']
                        
            inputs = json.loads(inputs)            
            
            critique = self.get_history_critique(inputs)
            
            critique += self.get_expert_critique(user_info.eosscontext.problem, inputs, port)
            
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

    def get_expert_critique(self, problem, inputs, port):

        try:
            self.VASSARClient = VASSARClient(port)

            # Start connection with VASSAR
            self.VASSARClient.start_connection()

            critique = self.VASSARClient.critique_architecture(problem, inputs)

            # End the connection before return statement
            self.VASSARClient.end_connection()

        except Exception:
            logger.exception('Exc in generating a critique using expert knowledge base')
            self.VASSARClient.end_connection()
            raise
