import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json


from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design






# --> Will return information on the Features subject
# --> We will need a DataMiningClient, used in analyst/views.py
class GetSubjectFeatures(APIView):
    def post(self, request, format=None):
        test_data = request.data['fricken_key']
        print(test_data)
        return Response({'list': 'test'})








# --> Will return information on the Sensitivities subject --> Ask Samalis
# --> We will need a DataMiningClient, used in analyst/views.py
class GetSubjectSensitivities(APIView):
    def post(self, request, format=None):
        return Response({'list': 'test'})






# --> Will return information on the Objective Space subject
# --> Call VASSAR
class GetSubjectObjectiveSpace(APIView):
    def post(self, request, format=None):
        return Response({'list': 'test'})





# --> Will return information on the Design Space subject
# --> Call VASSAR
class GetSubjectDesignSpace(APIView):
    def post(self, request, format=None):
        return Response({'list': 'test'})




