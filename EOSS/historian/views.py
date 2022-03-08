import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json

from thrift.Thrift import TApplicationException

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design
from EOSS.historian.historian import Historian

# Get an instance of a logger
logger = logging.getLogger('EOSS.historian')


class GetMissions(APIView):
    
    def post(self, request, format=None):
        try:
            historian = Historian()
            missions = historian.get_all_missions()
            logger.exception("hey got to GetMissions in historian views")
            return Response(missions)
        except Exception:
            logger.exception("fuck")
            return Response("")
