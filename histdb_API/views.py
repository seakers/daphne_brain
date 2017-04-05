from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class Question(APIView):
    """
    Ask a question.
    """

    def post(self, request, format=None):
        # TODO: Here I would call the HistDB backend
        return Response(request.data)
