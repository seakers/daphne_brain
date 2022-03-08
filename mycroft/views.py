import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json

from thrift.Thrift import TApplicationException

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design


class CheckConnection(APIView):

    def post(self, request, format=None):
        # user_info = get_or_create_user_information(request.session, request.user, request.data['problem'])
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if user_info.mycroft_connection is False:
            return Response({"connection": "false", "access_token": user_info.mycroft_session})
        else:
            return Response({"connection": "true"})



