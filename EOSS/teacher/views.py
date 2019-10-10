import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json


from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design






# --> Will return information on the Features subject
class GetSubjectFeatures(APIView):
    def post(self, request, format=None):
        return 0








# --> Will return information on the Sensitivities subject --> Ask Samalis
class GetSubjectSensitivities(APIView):
    def post(self, request, format=None):
        return 0






# --> Will return information on the Objective Space subject
class GetSubjectObjectiveSpace(APIView):
    def post(self, request, format=None):
        return 0





# --> Will return information on the Design Space subject
class GetSubjectDesignSpace(APIView):
    def post(self, request, format=None):
        return 0




