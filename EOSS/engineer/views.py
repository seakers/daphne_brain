import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json

from thrift.Thrift import TApplicationException

from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design

# Get an instance of a logger
logger = logging.getLogger('EOSS.engineer')


class GetOrbitList(APIView):
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
            client.start_connection()
            orbit_list = client.get_orbit_list(request.data['problem_name'])
            
            # End the connection before return statement
            client.end_connection()
            return Response(orbit_list)
        
        except TApplicationException as exc:
            logger.exception('Getting the orbit list failed')
            client.end_connection()
            return Response({
                "error": "Orbit list retrieval failed",
                "explanation": str(exc)
            })


class GetInstrumentList(APIView):

    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
            # Start connection with VASSAR
            client.start_connection()
            instrument_list = client.get_instrument_list(request.data['problem_name'])
            
            # End the connection before return statement
            client.end_connection()
            return Response(instrument_list)
        
        except TApplicationException as exc:
            logger.exception('Getting the instrument list failed')
            client.end_connection()
            return Response({
                "error": "Instrument list retrieval failed",
                "explanation": str(exc)
            })


class EvaluateArchitecture(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        client = VASSARClient(user_information=user_info)

        inputs = request.data['inputs']
        inputs = json.loads(inputs)

        # Make sure the dataset is not read-only
        is_read_only = client.check_dataset_read_only()

        if is_read_only:
            return Response({
                "status": "Dataset is read only",
                "code": "read_only_dataset"
            })

        # Check if the architecture already exists in DB before adding it again
        is_same, arch_id = client.check_for_existing_arch(inputs)

        if not is_same:
            architecture = client.evaluate_architecture(inputs, eval_queue_url=user_info.eosscontext.vassar_request_queue_url, block=False, user=request.user, session=request.session)
            return Response({
                "status": "Architecture evaluated!",
                "code": "arch_evaluated"
            })
        else:
            return Response({
                "status": "Architecture already exists",
                "code": "arch_repeated",
                "arch_id": arch_id
            })



def trim_architectures(archs):
    new_archs = []
    for arch in archs:
        input = arch['input']
        if '1' in input:
            new_archs.append(arch)

    seen_inputs = set()
    final_archs = []
    for arch in new_archs:
        input = arch['input']
        if input not in seen_inputs:
            final_archs.append(arch)
            seen_inputs.add(input)
    return final_archs



class EvaluateFalseArchitecture(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        archs = request.data['archs']
        archs = json.loads(archs)
        archs = trim_architectures(archs)
        print('--> EVALUATING FALSE ARCHITECTURES:', archs)
        vassar_client = VASSARClient(user_information=user_info)

        if user_info.eosscontext.vassar_request_queue_url:
            print("--> evaluating false architectures")
            vassar_client.purge_queue(user_info.eosscontext.vassar_request_queue_url)
            vassar_client.purge_queue(user_info.eosscontext.vassar_response_queue_url)
            vassar_client.evaluate_false_architectures(user_info.eosscontext.vassar_request_queue_url, archs)
        return Response({'status': 'ok'})





class RunLocalSearch(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
            client.start_connection()

            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architectures = client.run_local_search(user_info.eosscontext.problem, inputs)

            for arch in architectures:
                arch = add_design(arch, request.session, request.user, False)

            user_info.save()

            # End the connection before return statement
            client.end_connection()
            return Response(architectures)

        except TApplicationException as exc:
            logger.exception('Running a local search failed')
            client.end_connection()
            return Response({
                "error": "Running a local search failed",
                "explanation": str(exc)
            })


class GetArchDetails(APIView):

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        eosscontext = user_info.eosscontext
        client = VASSARClient(user_information=user_info)

        # Get the correct architecture
        arch_id = int(request.data['arch_id'])
        problem_id = int(request.data['problem_id'])
        dataset_id = int(request.data['dataset_id'])

        designs = client.get_dataset_architectures(problem_id=problem_id, dataset_id=dataset_id)
        arch = None
        for design in designs:
            if design["id"] == arch_id:
                arch = design

        score_explanation = client.get_arch_science_information(problem_id, arch)
        cost_explanation = client.get_arch_cost_information(problem_id, arch)

         # If score explanations have not been precomputed
        if score_explanation == [] or cost_explanation == []:
            client.reevaluate_architecture(arch, eosscontext.vassar_request_queue_url)
            score_explanation = client.get_arch_science_information(problem_id, arch)
            cost_explanation = client.get_arch_cost_information(problem_id, arch)

        def score_to_json(explanation):
            json_list = []
            for exp in explanation:
                json_exp = {
                    'name': exp.name,
                    'description': exp.description,
                    'value': exp.value,
                    'weight': exp.weight
                }
                if exp.subscores is not None:
                    json_exp['subscores'] = score_to_json(exp.subscores)
                json_list.append(json_exp)
            return json_list

        def budgets_to_json(explanation):
            json_list = []
            for exp in explanation:
                json_exp = {
                    'orbit_name': exp.orbit_name,
                    'payload': exp.payload,
                    'launch_vehicle': exp.launch_vehicle,
                    'total_mass': exp.total_mass,
                    'total_power': exp.total_power,
                    'total_cost': exp.total_cost,
                    'mass_budget': exp.mass_budget,
                    'power_budget': exp.power_budget,
                    'cost_budget': exp.cost_budget
                }
                json_list.append(json_exp)
            return json_list

        return Response({
            'score': score_to_json(score_explanation),
            'budgets': budgets_to_json(cost_explanation)
        })


class GetSubobjectiveDetails(APIView):

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        eosscontext = user_info.eosscontext
        client = VASSARClient(user_information=user_info)

        # Get the correct architecture
        arch_id = int(request.data['arch_id'])
        problem_id = int(request.data['problem_id'])
        dataset_id = int(request.data['dataset_id'])
        subobjective = request.data['subobjective']
        designs = client.get_dataset_architectures(problem_id=problem_id, dataset_id=dataset_id)
        arch = None
        for design in designs:
            if design["id"] == arch_id:
                arch = design

        subobjective_explanation = client.get_subobjective_score_explanation(arch, subobjective)

        print(subobjective_explanation)
        subobjective_details = {
            "subobjective": subobjective,
            "measurement": client.get_measurement_for_subobjective(problem_id, subobjective),
            "rows": subobjective_explanation,
        }

        return Response({
            'subobjective': subobjective_details,
        })

