from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import numpy as np
import sys,os
import json
import csv

from config.loader import ConfigurationLoader


# Print all paths included in sys.path
# from pprint import pprint as p
# p(sys.path)



config = ConfigurationLoader().load()


class updateUtterance(APIView):
    def __init__(self):
        pass
    def post(self, request, format=None):
        
        print(request.POST['content'])
        return Response('') 




