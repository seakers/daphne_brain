from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class GetDrivingFeatures(APIView):
    def post(self, request, format=None):
        # TODO: Call the datamining module for your specific problem
        return Response("TODO")
