import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json

from thrift.Thrift import TApplicationException

from EOSS.data.problem_specific import assignation_problems, partition_problems
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
            client = VASSARClient(port)
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
            client = VASSARClient(port)
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
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            # Start connection with VASSAR
            client.start_connection()

            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architecture = client.evaluate_architecture(user_info.eosscontext.problem, inputs)

            # Check if the architecture already exists in DB before adding it again
            is_same = True
            for old_arch in user_info.eosscontext.design_set.all():
                is_same = True
                old_arch_outputs = json.loads(old_arch.outputs)
                for i in range(len(old_arch_outputs)):
                    if old_arch_outputs[i] != architecture['outputs'][i]:
                        is_same = False
                if is_same:
                    break

            if not is_same:
                architecture = add_design(architecture, request.session, request.user, False)

            user_info.save()

            # End the connection before return statement
            client.end_connection()
            return Response(architecture)
        
        except TApplicationException as exc:
            logger.exception('Evaluating an architecture failed')
            client.end_connection()
            return Response({
                "error": "Evaluating an architecture failed",
                "explanation": str(exc)
            })


class RunLocalSearch(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
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
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()

            # Get the correct architecture
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            arch = user_info.eosscontext.design_set.get(id__exact=arch_id)

            score_explanation = client.get_arch_science_information(problem, arch)
            cost_explanation = client.get_arch_cost_information(problem, arch)

            # End the connection before return statement
            client.end_connection()

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

        except TApplicationException as exc:
            logger.exception('Exception when retrieving information from the current architecture!')
            client.end_connection()
            return Response({
                "error": "Retrieving information from the current architecture failed",
                "explanation": str(exc)
            })


class GetSubobjectiveDetails(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()

            # Get the correct architecture
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            arch = user_info.eosscontext.design_set.get(id__exact=arch_id)

            subobjective_explanation = client.get_subscore_details(problem, arch, request.data['subobjective'])

            # End the connection before return statement
            client.end_connection()

            def explanation_to_json(explanation):
                json_exp = {
                    'subobjective': request.data['subobjective'],
                    'param': explanation.param,
                    'attr_names': explanation.attr_names,
                    'attr_values': explanation.attr_values,
                    'scores': explanation.scores,
                    'taken_by': explanation.taken_by,
                    'justifications': explanation.justifications
                }
                return json_exp

            return Response({
                'subobjective': explanation_to_json(subobjective_explanation)
            })

        except TApplicationException as exc:
            logger.exception('Exception when retrieving information from the current subobjective!')
            client.end_connection()
            return Response({
                "error": "Retrieving information from the current subobjective failed",
                "explanation": str(exc)
            })
