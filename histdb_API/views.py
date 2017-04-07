from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import regex_engine

class Question(APIView):
    """
    Ask a question.
    """

    def post(self, request, format=None):

        answer = regex_engine.ask_question(request.data['question'])
        # TODO: Answer from DB list to human language -> This will be needed for ML algorithm as well
        return Response({'answer': answer[0]})
