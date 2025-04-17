import json
from collections import OrderedDict

from django.core import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from EOSS.tse.helpers import get_instrument_names, get_orbit_names, get_neo4j_functions, transform_frontend_config, save_backend_config, get_orbit_types, transform_frontend_config_combining

from EOSS.models import EOSSContext, EOSSContextSerializer, ActiveContextSerializer, EOSSDialogueContextSerializer, \
    EngineerContextSerializer, EOSSDialogueContext, EngineerContext
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
import EOSS.dialogue.command_lists as command_lists
from EOSS.models import Design
import os
import csv 

class TseAssigningData(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        # problem = request.data['problem']
        problem = user_info.eosscontext.problem
        instrument_dataset = get_instrument_names(problem)
        orbit_dataset = get_orbit_names(problem)
        metrics, functions_tools = get_neo4j_functions()
        orbit_types = get_orbit_types()

        return Response({
            'instrument_names': instrument_dataset,
            'orbit_names': orbit_dataset,
            'metrics': metrics,
            'functions_tools': functions_tools,
            'orbit_types': orbit_types,
            })

class StartAssigningTSE(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        problem = user_info.eosscontext.problem
        configurationstr = (request.data['configuration'])
        # print("configurationstr", configurationstr)
        configuration = json.loads(configurationstr)
        print("configuration", configuration)

        backend_config = transform_frontend_config(problem,configuration)
        config_file_path = save_backend_config(backend_config, "backend")
        return Response({
            'message': "Assigning TSE data",
            })

class StartCombiningTSE(APIView):

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        problem = user_info.eosscontext.problem
        configurationstr = (request.data['configuration'])
        configuration = json.loads(configurationstr)
        backend_config = transform_frontend_config_combining(problem,configuration)
        config_file_path = save_backend_config(backend_config, "backend")

        return Response({
            'message': "Combining TSE data",
        })
    

# Add this new class
class AddGADesign(APIView):
    """ Receives a new GA-generated design and adds it to the database
    """
    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
            # Extract design data
            design_data = json.loads(request.data.get('design', '{}'))
            problem_id = request.data.get('problem_id', user_info.eosscontext.problem)
            
            # Extract inputs and outputs
            inputs = design_data.get('inputs', [])
            outputs = design_data.get('outputs', [])
            
            # Create a new design
            new_design = Design(
                id=user_info.eosscontext.last_arch_id,
                eosscontext=user_info.eosscontext,
                inputs=json.dumps(inputs),
                outputs=json.dumps(outputs),
            )
            
            # Save the design
            new_design.save()
            
            # Increment the arch_id
            user_info.eosscontext.last_arch_id += 1
            user_info.eosscontext.save()
            
            # Add design to the CSV file
            dataset_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       "datasets", 
                                       request.user.username if request.user.is_authenticated else 'default',
                                       problem_id,
                                       user_info.eosscontext.dataset_name)
            
            with open(dataset_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Determine problem type
                if isinstance(inputs[0], bool) or (isinstance(inputs[0], int) and all(x in [0, 1] for x in inputs)):
                    # Binary input
                    input_row = [''.join(['1' if x else '0' for x in inputs])]
                else:
                    # Discrete input
                    input_row = inputs
                
                writer.writerow(input_row + outputs)
            
            return Response({
                "success": True,
                "design_id": new_design.id,
                "design": {
                    "id": new_design.id,
                    "inputs": inputs,
                    "outputs": outputs,
                    "is_ga": True
                }
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
        

# Add this new class
class PollGADesigns(APIView):
    """ Polls for new GA designs
    """
    def get(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
            # Get problem ID (current problem by default)
            problem_id = request.query_params.get('problem_id', user_info.eosscontext.problem)
            
            # Get last design ID seen by client
            last_id = int(request.query_params.get('last_id', -1))
            
            # Get all designs newer than last_id
            new_designs = []
            for design in user_info.eosscontext.design_set.filter(id__gt=last_id).order_by('id'):
                new_designs.append({
                    'id': design.id,
                    'inputs': json.loads(design.inputs),
                    'outputs': json.loads(design.outputs),
                    'is_ga': True  # All designs from polling are GA designs
                })
            
            return Response({
                "success": True,
                "designs": new_designs,
                "generation_complete": False  # Set to true when GA completes
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)