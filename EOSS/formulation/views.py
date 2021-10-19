from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information
import distutils


from EOSS.vassar.api import VASSARClient


from .agent import FormulationAgent

agent_dict = {}


class ClearEvalRequests(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        vassar_client = VASSARClient(user_information=user_info)

        if user_info.eosscontext.vassar_request_queue_url:
            vassar_client.purge_queue(user_info.eosscontext.vassar_request_queue_url)
        if user_info.eosscontext.vassar_response_queue_url:
            vassar_client.purge_queue(user_info.eosscontext.vassar_response_queue_url)

        return Response({'status': 'ok'})

class ToggleAgent(APIView):
    def post(self, request, format=None):
        global agent_dict

        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_session = user_info.session
        channel_layer = get_channel_layer()

        if request.data['mode'] == 'start':
            if user_session not in agent_dict:
                agent_dict[user_session] = FormulationAgent(user_info, channel_layer).start()
            return Response({'status': 'on'})
        elif request.data['mode'] == 'stop':
            if user_session in agent_dict:
                agent_dict.pop(user_session).stop()
            return Response({'status': 'off'})

        return Response({'status': 'ok'})



class FormulationChange(APIView):

    def parse_req_bool(self, item):
        if item in ['true', 'True', 'TRUE']:
            return True
        return False


    def post(self, request, format=None):
        global agent_dict

        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_session = user_info.session

        if user_session not in agent_dict:
            print('--> NO FORMULATION AGENT EXISTS')
            return Response({'status': 'error', 'message': 'no formulation agent exists'})
        agent = agent_dict[user_session]

        instChange = self.parse_req_bool(request.data['instrument'])
        orbChange = self.parse_req_bool(request.data['orbit'])
        stakeChange = self.parse_req_bool(request.data['stakeholder'])
        objChange = self.parse_req_bool(request.data['objective'])

        agent.formulation_change(instChange, orbChange, stakeChange, objChange)
        return Response({'status': 'success', 'message': 'formulation change recorded'})

