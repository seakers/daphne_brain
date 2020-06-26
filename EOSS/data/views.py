import json
import os
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.models import Design
from auth_API.helpers import get_or_create_user_information


class ImportData(APIView):
    """ Imports data from a csv file.

    Request Args:
        path: Relative path to a csv file residing inside Daphne project folder

    Returns:
        architectures: a list of python dict containing the basic architecture information.

    """

    def boolean_string_to_boolean_array(self, boolean_string):
        return [b == "1" for b in boolean_string]

    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

            # Set the path of the file containing data
            user_path = request.user.username if request.data['load_user_files'] == 'true' != '' else 'default'
            problem = request.data['problem']
            filename = request.data['filename']
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", user_path,
                                     problem, filename)

            input_num = int(request.data['input_num'])
            input_type = request.data['input_type']
            output_num = int(request.data['output_num'])

            user_info.eosscontext.last_arch_id = 0

            # Open the file
            with open(file_path) as csvfile:
                Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).delete()
                architectures = []
                architectures_json = []

                inputs_unique_set = set()
                # For each row, store the information
                has_header = csv.Sniffer().has_header(csvfile.read(1024))
                csvfile.seek(0)

                # Read the file as a csv file
                reader = csv.reader(csvfile, delimiter=',')

                for row in reader:
                    if has_header:
                        has_header = False
                        continue

                    inputs = []
                    outputs = []

                    # Import inputs
                    for i in range(input_num):
                        if input_type == 'binary':
                            # Assumes that there is only one column for the inputs
                            inputs = self.boolean_string_to_boolean_array(row[i])

                        elif input_type == 'discrete':
                            inputs.append(int(row[i]))

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
            user_info.eosscontext.dataset_user = request.data['load_user_files'] == 'true'
            user_info.eosscontext.save()
            user_info.save()

            return Response(architectures_json)
        except Exception:
            raise ValueError("There has been an error when parsing the architectures")


class SaveData(APIView):
    """ Save current dataset to a new csv file in the user folder
    """
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
        problem = request.data['problem']
        user_info.eosscontext.problem = problem
        user_info.eosscontext.save()
        user_info.save()
        return Response({
            "status": "Problem has been set successfully."
        })
