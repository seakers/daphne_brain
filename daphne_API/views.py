import json
import os
import csv
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from daphne_brain.nlp_object import nlp
import daphne_API.command_processing as command_processing
from auth_API.helpers import get_or_create_user_information
from daphne_API.models import Design
import daphne_API.command_lists as command_lists
from VASSAR_API.api import VASSARClient

# from daphne_API.MatEngine_object import eng1
# print(eng1)
# eng1.desktop(nargout=0)  # open engine





class Command(APIView):
    """
    Process a command
    """

    def post(self, request, format=None):
        # Preprocess the command
        processed_command = nlp(request.data['command'].strip().lower())

        # Classify the command, obtaining a command type
        command_options = ['iFEED', 'VASSAR', 'Critic', 'Historian', 'EDL']
        condition_names = ['ifeed', 'analyst', 'critic', 'historian', 'edl']
        command_types = command_processing.classify_command(processed_command)

        # Define context and see if it was already defined for this session
        if 'context' not in request.session:
            request.session['context'] = {}

        if 'data' in request.session:
            request.session['context']['data'] = request.session['data']

        if 'vassar_port' in request.session:
            request.session['context']['vassar_port'] = request.session['vassar_port']

        if 'problem' in request.session:
            request.session['context']['problem'] = request.session['problem']

        request.session['context']['answers'] = []

        if 'allowed_commands' in request.data:
            request.session['context']['allowed_commands'] = json.loads(request.data['allowed_commands'])

        # Act based on the types
        for command_type in command_types:
            command_class = command_options[command_type]
            condition_name = condition_names[command_type]
            request.session['context']['answers'].append(
                command_processing.command(processed_command, command_class, condition_name, request.session['context']))

        response = command_processing.think_response(request.session['context'])

        request.session.modified = True
        print('The command type is:')
        print(command_type)
        print('the type is:')
        print(type(command_type))

        if command_type == int(4):
            print(eng1.eval('2+2'))


        # If command is to switch modes, send new mode back, if not
        return Response({'response': response})

class CommandList(APIView):
    """
    Get a list of commands, either for all the system or for a single subsystem
    """
    def post(self, request, format=None):
        port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
        vassar_client = VASSARClient(port)
        problem = request.session["problem"]
        # List of commands for a single subsystem
        command_list = []
        command_list_request = request.data['command_list']
        restricted_list = None
        if 'restricted_list' in request.data:
            restricted_list = request.data['restricted_list']
        if command_list_request == 'general':
            command_list = command_lists.general_commands_list(restricted_list)
        elif command_list_request == 'datamining':
            command_list = command_lists.datamining_commands_list(restricted_list)
        elif command_list_request == 'analyst':
            command_list = command_lists.analyst_commands_list(restricted_list)
        elif command_list_request == 'critic':
            command_list = command_lists.critic_commands_list(restricted_list)
        elif command_list_request == 'historian':
            command_list = command_lists.historian_commands_list(restricted_list)
        elif command_list_request == 'measurements':
            command_list = command_lists.measurements_list()
        elif command_list_request == 'missions':
            command_list = command_lists.missions_list()
        elif command_list_request == 'technologies':
            command_list = command_lists.technologies_list()
        elif command_list_request == 'space_agencies':
            command_list = command_lists.agencies_list()
        elif command_list_request == 'objectives':
            command_list = command_lists.objectives_list(vassar_client)
        elif command_list_request == 'orb_info':
            command_list = command_lists.orbits_info(problem)
        elif command_list_request == 'instr_info':
            command_list = command_lists.instruments_info(problem)
        elif command_list_request == 'analyst_instrument_parameters':
            command_list = command_lists.analyst_instrument_parameter_list(problem)
        elif command_list_request == 'analyst_instruments':
            command_list = command_lists.analyst_instrument_list(problem)
        elif command_list_request == 'analyst_measurements':
            command_list = command_lists.analyst_measurement_list(problem)
        elif command_list_request == 'analyst_stakeholders':
            command_list = command_lists.analyst_stakeholder_list(problem)
        return Response({'list': command_list})


class ImportData(APIView):
    """ Imports data from a csv file.

    Request Args:
        path: Relative path to a csv file residing inside Daphne project folder

    Returns:
        architectures: a list of python dict containing the basic architecture information.

    """

    def booleanString2booleanArray(self, booleanString):
        return [b == "1" for b in booleanString]

    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request, 'EOSS')

            # Set the path of the file containing data
            user_path = request.user.username if request.data['load_user_files'] == 'true' != '' else 'default'
            problem = request.data['problem']
            filename = request.data['filename']
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', user_path, problem, filename)

            input_num = int(request.data['input_num'])
            input_type = request.data['input_type']
            output_num = int(request.data['output_num'])

            user_info.eosscontext.last_arch_id = 0

            # Open the file
            with open(file_path) as csvfile:
                Design.objects.filter(eosscontext__exact=user_info.eosscontext).delete()
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
                            inputs = self.booleanString2booleanArray(row[i])

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
            user_info.save()

            return Response(architectures_json)
        except Exception:
            raise ValueError("There has been an error when parsing the architectures")


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
        default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'default', problem)
        default_datasets.extend(os.listdir(default_path))

        if request.user.is_authenticated:
            username = request.user.username
            user_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', username, problem)
            user_datasets.extend(os.listdir(user_path))

        response_data = {
            'default': default_datasets,
            'user': user_datasets
        }

        return Response(response_data)


class ClearSession(APIView):
    """ Clears the Daphne Session.
    """

    def post(self, request, format=None):
        from . daphne_fields import daphne_fields

        # Remove all fields from session if they exist
        for field in daphne_fields:
            if field in request.session:
                del request.session[field]

        return Response({})

class ImportDataEDLSTATS(APIView):
    """ Imports data from a csv file. To be deprecated in the future.

    Request Args:
        filename: Name of the sample data file

    Returns:
        data: Json string with the read data
        columns: array with the columns of the data

    """


    def post(self, request, format=None):

        # Set the path of the file containing data
        file_path = '/Users/ssantini/Desktop/Code Daphne/daphne_brain/daphne_API/' + request.data['filename']

        data = pd.read_csv(file_path, parse_dates=True, index_col='timestamp')

        return Response(data)

class SetProblem(APIView):
    """ Sets the name of the problem
    """

    def post(self, request, format=None):
        problem = request.data['problem']
        request.session['problem'] = problem
        return Response({})


class ActiveFeedbackSettings(APIView):
    """ Returns the values for the different active daphne settings
    """
    def get(self, request, format=None):
        if request.user.is_authenticated:
            if 'show_background_search_feedback' not in request.session \
                    or 'check_for_diversity' not in request.session \
                    or 'show_arch_suggestions' not in request.session:
                request.session['show_background_search_feedback'] = False
                request.session['check_for_diversity'] = True
                request.session['show_arch_suggestions'] = True

            return Response({
                'show_background_search_feedback': request.session['show_background_search_feedback'],
                'check_for_diversity': request.session['check_for_diversity'] ,
                'show_arch_suggestions': request.session['show_arch_suggestions'] ,
            })
        else:
            return Response({
                'error': 'User not logged in!'
            })


    def post(self, request, format=None):
        if 'show_background_search_feedback' in request.data:
            request.session['show_background_search_feedback'] = request.data['show_background_search_feedback']
        if 'check_for_diversity' in request.data:
            request.session['check_for_diversity'] = request.data['check_for_diversity']
        if 'show_arch_suggestions' in request.data:
            request.session['show_arch_suggestions'] = request.data['show_arch_suggestions']
        return Response({})
