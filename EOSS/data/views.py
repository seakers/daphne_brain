import json
import os
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.graphql.api import GraphqlClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design



class ImportData(APIView):
    """ Imports data from a csv file.

    Request Args:
        path: Relative path to a csv file residing inside Daphne project folder

    Returns:
        architectures: a list of python dict containing the basic architecture information.

    """

    def boolean_string_to_boolean_array(self, boolean_string):
        return [b == "1" for b in boolean_string]

    
    """
        Rquest Fields
        - problem_id
        - group_id
        - load_user_files

    """
    def post(self, request, format=None):
        try:

            # Get user_info and problem_id
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            problem_id = int(request.data['problem_id'])
            group_id = int(request.data['group_id'])
            dataset_id = int(request.data['dataset_id'])

            # Get problem architectures
            dbClient = GraphqlClient(problem_id=problem_id)

            print("--> PROBLEM IDER: ", problem_id)

            # If dataset_id is -1, copy all architectures in the default set for this problem into a user-specific dataset called 'default' and set that as the main dataset,
            # Else, use the request dataset_id to get architectures
            if dataset_id == -1:
                default_dataset_id = dbClient.get_default_dataset_id("default", problem_id)
                dataset_id = dbClient.clone_default_dataset(default_dataset_id, user_info.user.id)
            query = dbClient.get_architectures(problem_id, dataset_id)

            # Iterate over architectures
            # Create: user context Designs
            # Create: object to send designs to front-end
            architectures_json = []
            counter = 0
            for arch in query['data']['Architecture']:

                # If the arch needs to be re-evaluated due to a problem definition change, do not add
                if not arch['eval_status']:
                    continue

                # Arch: inputs / outputs
                inputs = self.boolean_string_to_boolean_array(arch['input'])
                outputs = [float(arch['science']), float(arch['cost'])]

                # Append design object and front-end design object
                architectures_json.append({'id': counter, 'db_id': arch['id'], 'inputs': inputs, 'outputs': outputs})

                # Increment counters
                user_info.eosscontext.last_arch_id = counter
                counter = counter + 1


            # Set user context
            user_info.eosscontext.problem_id = problem_id
            user_info.eosscontext.group_id = group_id
            user_info.eosscontext.dataset_id = dataset_id
            user_info.eosscontext.save()
            user_info.save()

            # Return architectures
            return Response(architectures_json)
        except Exception:
            raise ValueError("There has been an error when parsing the architectures")

""" Save current dataset to a new csv file in the user folder
"""
class SaveData(APIView):
    
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

                # Get the problem type
                problem = user_info.eosscontext.problem
                if problem in assignation_problems:
                    problem_type = 'binary'
                elif problem in partition_problems:
                    problem_type = 'discrete'
                else:
                    problem_type = 'unknown'

                # Set the path of the file where the data will be saved
                user_path = request.user.username
                filename = request.data['filename']
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", user_path, problem,
                                         filename)

                # input_num = int(request.data['input_num'])
                # input_type = request.data['input_type']
                # output_num = int(request.data['output_num'])

                # Open the file
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write header
                    if problem_type == 'binary':
                        design = user_info.eosscontext.design_set.first()
                        num_outputs = len(json.loads(design.outputs))
                        writer.writerow(['Inputs'] + ['Output' + str(i) for i in range(num_outputs)])
                    elif problem_type == 'discrete':
                        design = user_info.eosscontext.design_set.first()
                        num_inputs = len(json.loads(design.inputs))
                        num_outputs = len(json.loads(design.outputs))
                        writer.writerow(['Input' + str(i) for i in range(num_inputs)] + ['Output' + str(i) for i in range(num_outputs)])
                    else:
                        raise ValueError("Not implemented!")
                    # Write designs
                    for design in user_info.eosscontext.design_set.all():
                        inputs = json.loads(design.inputs)
                        if problem_type == 'binary':
                            input_list = [''.join(['1' if x else '0' for x in inputs])]
                        elif problem_type == 'discrete':
                            input_list = inputs
                        else:
                            raise ValueError("Not implemented!")
                        output_list = json.loads(design.outputs)
                        writer.writerow(input_list + output_list)

                return Response(filename + " has been saved correctly!")
            except Exception:
                raise ValueError("There has been an error when writing the file")
        else:
            return Response({
                "error": "This is only available to registered users!"
            })

### DEPRECATED (temporarily)
class DownloadData(APIView):
    """ Download the csv file to the user computer
    """
    def get(self, request, format=None):
        if request.user.is_authenticated:
            try:
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                problem = user_info.eosscontext.problem

                # Set the path of the file where the data will be saved
                user_path = request.user.username
                filename = request.query_params['filename']
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", user_path, problem,
                                         filename)

                # Create the HttpResponse object with the appropriate CSV header.
                csv_data = open(file_path, "r").read()
                response = HttpResponse(csv_data, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

                return response

            except Exception:
                raise ValueError("There has been an error when downloading the file")
        else:
            return Response({
                "error": "This is only available to registered users!"
            })

### DEPRECATED (temporarily)
class DatasetList(APIView):
    """ Returns a list of problem files.

    Request Args:
        problem: Name of the problem for the list

    Returns:
        dataset_list: a python dict with two lists: one for default datasets and another for user datasets

    """
    def post(self, request, format=None):

        default_datasets = []
        user_datasets = []

        # Set the path of the file containing data
        problem = request.data['problem']
        default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", 'default', problem)
        default_datasets.extend(os.listdir(default_path))

        if request.user.is_authenticated:
            username = request.user.username
            user_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", username, problem)
            user_datasets.extend(os.listdir(user_path))

        response_data = {
            'default': default_datasets,
            'user': user_datasets
        }

        return Response(response_data)


class SetProblem(APIView):
    """ Sets the name of the problem
    """
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        # problem = request.data['problem']
        problem = 'SMAP'  # HARDCODE
        user_info.eosscontext.problem = problem
        user_info.eosscontext.save()
        user_info.save()
        print("---> SetProblem", problem)
        return Response({
            "status": "Problem has been set successfully."
        })
