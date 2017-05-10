from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import spacy
from . import qa_pipeline

nlp = spacy.load('en')

class Question(APIView):
    """
    Ask a question.
    """

    def post(self, request, format=None):
        # Preprocess the question
        processed_question = nlp(request.data['question'])
        # Classify the question, obtaining a question type
        question_type = qa_pipeline.classify(processed_question)
        # Load list of required and optional parameters from question, query and response format for question type
        [params, query, response_template] = qa_pipeline.load_type_info(question_type)
        # TODO: Extract required and optional parameters
        data = qa_pipeline.extract_data(processed_question, params)
        # TODO: Query the database
        response = qa_pipeline.query(query, data)
        # TODO: Construct the response from the database query and the response format
        answer = qa_pipeline.build_answer(response_template, response)
        answer = question_type
        # Return the answer to the client
        return Response({'answer': answer})
