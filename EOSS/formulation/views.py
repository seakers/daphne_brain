from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from auth_API.helpers import get_or_create_user_information
import distutils
import json
from asgiref.sync import async_to_sync, sync_to_async
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.evaluation import Evaluation


from .agent import FormulationAgent

agent_dict = {}


class ClearEvalRequests(APIView):
    def post(self, request, format=None):

        # --> 1. Get evaluation client
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        client = Evaluation(user_info)

        # --> 2. Purge requests
        async_to_sync(client.purge_requests)()
        return Response({'status': 'ok'})







class ToggleAgent(APIView):
    def post(self, request, format=None):
        global agent_dict

        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_session = user_info.session
        channel_layer = get_channel_layer()

        if request.data['mode'] == 'start':
            objective_list = json.loads(request.data['objective_list'])
            print('--> OBJECTIVE LIST:', objective_list)
            if user_session not in agent_dict:
                agent_dict[user_session] = FormulationAgent(user_info, channel_layer, request.session, objective_list).start()
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
        objList = json.loads(request.data['objective_list'])

        agent.formulation_change(instChange, orbChange, stakeChange, objChange, objList)
        return Response({'status': 'success', 'message': 'formulation change recorded'})

