from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

from channels import Group

from config.loader import ConfigurationLoader


# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)


config = ConfigurationLoader().load()


class updateUtterance(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        chat_message = request.POST['content']
        print('Message received from chat module: {0}'.format(chat_message))
        Group("mycroft").send({
                "text": chat_message
        })        
        return Response('') 

class updateSystemResponse(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        message = request.POST['content']
        print('Message received from mycroft: {0}'.format(message))
        Group("chat").send({
            "text": message
        })
        return Response('')