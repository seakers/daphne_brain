from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class OrbitList(APIView):
    """
    List all orbits.
    """
    def get(self, request, format=None):
        # Call Java library to get the list of orbits
        # ArrayList<String> orbitList = new ArrayList<>();
        # String[] orbits = Params.orbit_list;
        # for (String orb: orbits){
        #     orbitList.add(orb);
        # }
        return Response({'test':'test'})

class InstrumentList(APIView):
    """
    List all instruments.
    """
    def get(self, request, format=None):
        # Call Java library to get the list of instruments
        # ArrayList<String> instrumentList = new ArrayList<>();
        # String[] instruments = Params.instrument_list;
        # for (String inst:instruments){
        #     instrumentList.add(inst);
        # }
        return Response({'test2':'test2'})
