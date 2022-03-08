import logging

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from EOSS.models import Design



from thrift.Thrift import TApplicationException

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.data.design_helpers import add_design
from EOSS.historian.historian import Historian
from EOSS.vassar.interface.ttypes import MissionMeasurements

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
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
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

            # if not is_same:
            #     architecture = add_design(architecture, request.session, request.user, False)

            user_info.save()

            # End the connection before return statement
            # client.end_connection()
            return Response({})
        
        except TApplicationException as exc:
            logger.exception('Evaluating an architecture failed')
            client.end_connection()
            return Response({
                "error": "Evaluating an architecture failed",
                "explanation": str(exc)
            })



class EvaluateFalseArchitecture(APIView):
    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)

            problem_id = request.data['problem_id']

            # Delete all design objects
            Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).delete()
        
            architecture = client.evaluate_false_architectures(problem_id)



            # # Check if the architecture already exists in DB before adding it again
            # is_same = True
            # for old_arch in user_info.eosscontext.design_set.all():
            #     is_same = True
            #     old_arch_outputs = json.loads(old_arch.outputs)
            #     for i in range(len(old_arch_outputs)):
            #         if old_arch_outputs[i] != architecture['outputs'][i]:
            #             is_same = False
            #     if is_same:
            #         break

            # if not is_same:
            #     architecture = add_design(architecture, request.session, request.user, False)

            # user_info.save()

            # # End the connection before return statement
            # client.end_connection()
            return Response({})
        
        except TApplicationException as exc:
            logger.exception('Evaluating false architectures failed')
            client.end_connection()
            return Response({
                "error": "Evaluating false architectures failed",
                "explanation": str(exc)
            })





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
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
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


class GetMultArchMeas(APIView):

    def post(self, request, format=None):
        try:
            # Start VASSAR connection
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()

            # Get architectures
            arch_string = request.data['arch_ids']
            arch_list = arch_string.split(",")
            problem = request.data['problem']
            measurements = []
            for arch_id in arch_list:
                measurement = client.get_measurement_list(problem, user_info.eosscontext.design_set.get(id__exact=arch_id))
                measurements.append(measurement)
            client.end_connection()

            return Response(measurements)
        except TApplicationException as exc:
            logger.exception('Exception when retrieving measurements from architectures.')
            return Response({
                "error": "Retrieving measurements from selected architectures failed.",
                "explanation": str(exc)
            })


class GetMissions(APIView):

    def post(self, request, format=None):
        try:
            historian = Historian()
            missions = historian.get_all_missions()
            return Response(missions)
        except Exception:
            logger.exception("Error getting missions.")
            return Response("")


class GetMissionMeasurements(APIView):

    def post(self, request, format=None):
        try:
            historian = Historian()
            mission_measurements = historian.get_all_mission_measurements()
            return Response(mission_measurements)
        except Exception:
            logger.exception("Error getting mission measurements.")
            return Response("")


class GetSchedulingEval(APIView):
    def post(self, request, format=None):
        try:
            # Start VASSAR connection
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()
            historian = Historian()
            historical_mission_data = historian.get_all_mission_measurements()
            arch_string = request.data['arch_ids']
            arch_list = arch_string.split(",")
            problem = request.data['problem']
            mission_data = []
            date_string = request.data['dates']
            date_list = date_string.split(",")
            count = 0
            for arch_id in arch_list:
                arch = user_info.eosscontext.design_set.get(id__exact=arch_id)
                measurements = client.get_measurement_list(problem, arch)
                start_date = int(date_list[count])
                end_date = int(date_list[count + 1])
                count = count + 2
                mission_data.append(MissionMeasurements(measurements, start_date, end_date))
            score = client.get_scheduling_eval(mission_data, historical_mission_data)
            client.end_connection()
            return Response(score)
        except Exception:
            logger.exception("Error evaluating scheduling architecture.")
            return Response("")

class StartSchedulingGA(APIView):
    def post(self, request, format=None):
        try:
            # Start VASSAR connection
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()
            historian = Historian()
            historical_mission_data = historian.get_all_mission_measurements()
            arch_string = request.data['arch_ids']
            arch_list = arch_string.split(",")
            problem = request.data['problem']
            arches = []
            thrift_list = []
            for arch_id in arch_list:
                arch = user_info.eosscontext.design_set.get(id__exact=arch_id)
                arches.append(arch)
            score = client.start_scheduling_ga(problem, request.user.username, thrift_list, arches, historical_mission_data)
            client.end_connection()
            return Response(score)
        except Exception:
            logger.exception("Error evaluating scheduling architecture.")
            return Response("")

class StartEnumeration(APIView):
    def post(self, request, format=None):
        try:
            # Start VASSAR connection
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.start_connection()
            historian = Historian()
            historical_mission_data = historian.get_all_mission_measurements()
            arch_string = request.data['arch_ids']
            arch_list = arch_string.split(",")
            problem = request.data['problem']
            arches = []
            for arch_id in arch_list:
                arch = user_info.eosscontext.design_set.get(id__exact=arch_id)
                arches.append(arch)
            score = client.start_enumeration(problem, arches, historical_mission_data)
            client.end_connection()
            return Response(score)
        except Exception:
            logger.exception("Error evaluating scheduling architecture.")
            return Response("")

class DataContinuityTable(APIView):
    def post(self, request, format=None):
        try:
            # Start VASSAR connection
            historian = Historian()
            measurement_list, array = historian.data_continuity_table();
            return Response(measurement_list, array)
        except Exception:
            logger.exception("Error evaluating scheduling architecture.")
            return Response("")

class GetSubobjectiveDetails(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port, user_info=user_info)
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
