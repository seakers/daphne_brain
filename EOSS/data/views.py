import json
import os
import csv
import timeit
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.data.problem_helpers import assignation_problems, partition_problems
from EOSS.graphql.api import GraphqlClient
from auth_API.helpers import get_or_create_user_information
from EOSS.vassar.evaluation import Evaluation

from EOSS.graphql.clients.Dataset import Dataset
from asgiref.sync import async_to_sync


class ImportData(APIView):
    """ Returns architectures from the requested dataset

        Request Args:
            group_id: Group id
            problem_id: Problem id
            dataset_id: Dataset id

        Returns:
            formatted_architectures: Correctly formatted architectures

    """
    def post(self, request, format=None):
        print('--> LOADING ARCHITECTURES...')
        try:

            # --> 1. Get user_info and save
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            user_info.eosscontext.problem_id = int(request.data['problem_id'])
            user_info.eosscontext.group_id = int(request.data['group_id'])
            user_info.eosscontext.dataset_id = int(request.data['dataset_id'])
            user_info.eosscontext.save()
            user_info.save()

            # --> 2. Purge evaluation queues
            e_client = Evaluation(user_info)
            async_to_sync(e_client.purge_all)()

            # --> 3. Create dataset client
            d_client = Dataset(user_info)

            # --> 4. Get all architectures
            all_architectures = []
            user_architectures = async_to_sync(d_client.get_architectures_user_all)(None, False, True)
            ga_architectures = async_to_sync(d_client.get_architectures_ga)(None, False, True)
            if user_architectures is not None:
                all_architectures.extend(user_architectures)
            if ga_architectures is not None:
                all_architectures.extend(ga_architectures)
            print('--> LOADED ARCHITECTURES:', all_architectures)

            # --> 4. Format architectures
            formatted_architectures = async_to_sync(self.format_architectures_ai4se)(all_architectures)
            return Response(formatted_architectures)

        except Exception:
            raise ValueError("There has been an error when parsing the architectures")

    async def format_inputs(self, inputs):
        return [b == "1" for b in inputs]

    async def format_architectures(self, architectures):
        formatted = []
        for idx, architecture in enumerate(architectures):
            # --> 1. Create inputs
            inputs = await self.format_inputs(architecture['input'])

            # --> 2. Create outputs
            outputs = [float(architecture['cost']), float(architecture['science'])]

            # --> 3. Create formatted architecture
            formatted.append({'id': idx, 'db_id': architecture['id'], 'inputs': inputs, 'outputs': outputs})

        return formatted

    async def format_architectures_ai4se(self, architectures):
        formatted = []
        for idx, architecture in enumerate(architectures):

            # --> 1. Create inputs
            inputs = await self.format_inputs(architecture['input'])

            # --> 2. Create outputs
            outputs = []
            if 'cost' in architecture:
                if architecture['cost'] is not None:
                    outputs.append(float(architecture['cost']))
            if 'science' in architecture:
                if architecture['science'] is not None:
                    print('--> SCIENCE SKIPPED')
                    # outputs.append(float(architecture['science']))
            if 'programmatic_risk' in architecture:
                if architecture['programmatic_risk'] is not None:
                    outputs.append(float(architecture['programmatic_risk']))
            for x in architecture['ArchitectureScoreExplanations']:
                outputs.append(float(x['satisfaction']))
            while len(outputs) < 5:
                outputs.append(0)

            # --> 3. Create formatted architecture
            formatted.append({'id': idx, 'db_id': architecture['id'], 'inputs': inputs, 'outputs': outputs})

        return formatted

class CopyData(APIView):
    """ Copies a dataset into another dataset

    Request Args:
        source_id: Id of source dataset
        target_name: Name of new dataset

    Returns:
        target_id: Id of the new dataset.

    """
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # --> 1. Get request data
                source_id = int(request.data['src_dataset_id'])
                target_name = request.data['dst_dataset_name']
                save = True
                costs = True
                scores = True

                # --> 2. Create dataset client
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                d_client = Dataset(user_info)

                # --> 3. Clone dataset
                target_id = async_to_sync(d_client.clone_dataset)(source_id, target_name, save, costs, scores)

                # --> 4. Return results
                return Response({
                    "problem_id": user_info.eosscontext.problem_id,
                    "dst_dataset_id": target_id
                })
            except Exception:
                raise ValueError("There has been an error when cloning the dataset!")
        else:
            return Response({
                "error": "This is only available to registered users!"
            })




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

        # --> 1. Get user_info and save
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_info.eosscontext.problem_id = int(request.data['problem_id'])
        user_info.eosscontext.group_id = int(request.data['group_id'])
        user_info.eosscontext.dataset_id = int(request.data['dataset_id'])
        user_info.eosscontext.save()
        user_info.save()

        # --> 2. Purge evaluation queues
        e_client = Evaluation(user_info)
        async_to_sync(e_client.purge_all)()

        return Response({
            "status": "Problem has been set successfully."
        })
