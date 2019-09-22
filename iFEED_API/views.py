import logging

from rest_framework.views import APIView
from rest_framework.response import Response

import os
import json
import csv
from random import *

from EOSS.models import Design
from iFEED_API.venn_diagram.intersection import optimize_distance
from config.loader import ConfigurationLoader

from auth_API.helpers import get_or_create_user_information

# Get an instance of a logger
logger = logging.getLogger('iFEED')

config = ConfigurationLoader().load()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class ImportData(APIView):
    
    """ Imports data from a csv file. To be deprecated in the future.

    Request Args:
        path: Relative path to a csv file residing inside iFEED project folder
        
    Returns:
        architectures: a list of python dict containing the basic architecture information.
        
    """

    def post(self, request, format=None):
        try:    
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            user_info.eosscontext.last_arch_id = 0

            # Set the path of the file containing data
            filename = request.POST['file_path']
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

            problem = request.POST['problem']
            
            input_type = request.POST['input_type']
            input_num = int(request.POST['input_num'])
            output_num = int(request.POST['output_num'])
            
            # Open the file
            with open(file_path) as csvfile:
                Design.objects.filter(eosscontext__exact=user_info.eosscontext).delete()

                architectures = []
                architectures_json = []

                inputs_unique_set = set()

                # Check if there exists a header
                has_header = csv.Sniffer().has_header(csvfile.read(1024))
                csvfile.seek(0)

                # Read the file as a csv file
                reader = csv.reader(csvfile, delimiter=',')

                # For each row, store the information
                for row in reader:
                    if has_header:
                        has_header = False
                        continue

                    inputs = []
                    outputs = []

                    if problem == "Constellation_10":
                        # Filter out outliers

                        if float(row[40]) > 22000: # mean_resp
                            continue
                        elif float(row[41]) > 93000: # latency
                            continue
                        else:
                            if random() > 0.1:
                                continue

                    # Import inputs
                    for i in range(input_num):
                        if input_type == 'binary':
                            # Assumes that there is only one column for the inputs
                            inputs = self.booleanString2booleanArray(row[i])

                        elif input_type == 'discrete':
                            inputs.append(int(row[i]))

                        elif input_type == 'continuous': # continuous variable input

                            inp = row[i]
                            if inp == "":
                                inp = None
                            elif inp == "null":
                                inp = None
                            else:
                                inp = float(inp)
                            inputs.append(inp)
                        else:
                            raise ValueError('Unknown input type: {0}'.format(input_type))


                    for i in range(output_num):
                        out = row[i + input_num]
                        if out == "":
                            out = 0
                        else:
                            out = float(out)
                        outputs.append(out)

                    hashed_input = hash(tuple(inputs))
                    if hashed_input not in inputs_unique_set:
                        architectures.append(Design(id=user_info.eosscontext.last_arch_id,
                                                    eosscontext=user_info.eosscontext,
                                                    inputs=json.dumps(inputs),
                                                    outputs=json.dumps(outputs)))
                        architectures_json.append({'id': user_info.eosscontext.last_arch_id, 'inputs': inputs, 'outputs': outputs})
                        user_info.eosscontext.last_arch_id += 1
                        inputs_unique_set.add(hashed_input)

            # Define context and see if it was already defined for this session
            Design.objects.bulk_create(architectures)
            user_info.eosscontext.problem = problem
            user_info.eosscontext.dataset_name = filename
            user_info.eosscontext.save()
            user_info.save()
            return Response(architectures_json)
        
        except Exception:
            raise ValueError("There has been an error when parsing the architectures")

    def booleanString2booleanArray(self, booleanString):
        return [b == "1" for b in booleanString]
    

    
class SetTargetRegion(APIView):

    def post(self, request, format=None):
        try:
            logger.debug('iFEED set target region')
            
            # Get selected arch id's
            selected = request.POST['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            
            # Convert strings to ints
            behavioral = []
            if selected_arch_ids:
                for s in selected_arch_ids:
                    if not len(s)==0:
                        behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.POST['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')

            # Convert strings to ints
            non_behavioral = []
            if non_selected_arch_ids:
                for s in non_selected_arch_ids:
                    if not len(s)==0:
                        non_behavioral.append(int(s))

            # Define context and see if it was already defined for this session
            if 'context' not in request.session:
                request.session['context'] = {}
            
            # Update context information
            request.session['context']['behavioral'] = behavioral
            request.session['context']['non_behavioral'] = non_behavioral
                        
            return Response('')
        
        except Exception:
            logger.exception('Exception in setting the target region for iFEED')
            return Response('')

class VennDiagramDistance(APIView):

    """ Optimizes the distance between two circles in a Venn diagram

    Request Args:
        a1: the area of the first circle
        a2: the area of the second circle
        intersection: the intersecting area of two circles

    Returns:
        The distance between two circles

    """
    def __init__(self):
        pass
    def post(self, request, format=None):
        a1 = float(request.POST['a1'])
        a2 = float(request.POST['a2'])
        intersection = float(request.POST['intersection'])
        res = optimize_distance(a1,a2,intersection)

        distance = res.x[0]
        return Response(distance)
