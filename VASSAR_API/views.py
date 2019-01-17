import logging
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import redis
import time

from VASSAR_API.thriftinterface.ttypes import BinaryInputArchitecture
from VASSAR_API.thriftinterface.ttypes import DiscreteInputArchitecture
from VASSAR_API.api import VASSARClient
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from importlib import import_module
from django.conf import settings

from auth_API.helpers import get_or_create_user_information
from daphne_API.background_search import send_archs_from_queue_to_main_dataset, send_archs_back
from daphne_API.design_helpers import add_design
from daphne_API.models import Design

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

# Get an instance of a logger
logger = logging.getLogger('VASSAR')


class GetOrbitList(APIView):
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            self.VASSARClient = VASSARClient(port)
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getOrbitList(request.data['problem_name'])
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            logger.exception('Exception in getting the orbit list')
            self.VASSARClient.endConnection()
            return Response('')


class GetInstrumentList(APIView):

    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            self.VASSARClient = VASSARClient(port)
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
            list = self.VASSARClient.getInstrumentList(request.data['problem_name'])
            
            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(list)
        
        except Exception:
            logger.exception('Exception in getting the instrument list')
            self.VASSARClient.endConnection()
            return Response('')


class EvaluateArchitecture(APIView):
    
    def post(self, request, format=None):
        try:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            self.VASSARClient = VASSARClient(port)
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architecture = self.VASSARClient.evaluateArchitecture(user_info.eosscontext.problem, inputs)

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
                architecture['id'] = user_info.eosscontext.last_arch_id
                print(user_info.eosscontext.last_arch_id)
                add_design(architecture, user_info.eosscontext, False)

            user_info.save()

            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architecture)
        
        except Exception:
            logger.exception('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')


class RunLocalSearch(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            self.VASSARClient = VASSARClient(port)
            self.VASSARClient.startConnection()

            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architectures = self.VASSARClient.runLocalSearch(inputs)

            for arch in architectures:
                arch['id'] = user_info.eosscontext.last_arch_id
                add_design(arch, user_info.eosscontext, False)

            user_info.save()

            # End the connection before return statement
            self.VASSARClient.endConnection()
            return Response(architectures)

        except Exception:
            logger.exception('Exception in evaluating an architecture')
            self.VASSARClient.endConnection()
            return Response('')


class ChangePort(APIView):

    def post(self, request, format=None):
        new_port = request.data['port']
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_info.eosscontext.vassar_port = new_port
        user_info.eosscontext.save()
        user_info.save()
        return Response('')


class StartGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # Start listening for redis inputs to share through websockets
                r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
                p = r.pubsub()

                def my_handler(message):
                    thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                    if message['data'] == 'new_arch':
                        print('Processing some new archs!')
                        nonlocal inputs_unique_set
                        # Archs are added one by one
                        new_archs = r.lrange(request.user.username, -1, -1)
                        send_back = []
                        # Add archs to the context data before sending back to user
                        for arch in new_archs:
                            arch = json.loads(arch)
                            hashed_input = hash(tuple(arch['inputs']))
                            if hashed_input not in inputs_unique_set:
                                full_arch = {
                                    'id': thread_user_info.eosscontext.last_arch_id,
                                    'inputs': arch['inputs'],
                                    'outputs': arch['outputs']
                                }
                                if thread_user_info.eosscontext.activecontext.show_background_search_feedback:
                                    add_design(full_arch, thread_user_info.eosscontext, False)
                                else:
                                    add_design(full_arch, thread_user_info.eosscontext, True)
                                send_back.append(full_arch)
                                inputs_unique_set.add(hashed_input)
                                thread_user_info.save()

                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()

                        background_queue_qs = Design.objects.filter(activecontext_id__exact=thread_user_info.eosscontext.activecontext.id)
                        if background_queue_qs.count() >= 10:
                            async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                              {
                                                                  'type': 'active.notification',
                                                                  'notification': {
                                                                      'title': 'Background search results',
                                                                      'message': 'The background search has found more than 10 architectures, but you have chosen to not show them. Do you want to see them now?',
                                                                      'setting': 'show_background_search_feedback'
                                                                  }
                                                              })
                        if thread_user_info.eosscontext.activecontext.show_background_search_feedback:
                            back_list = send_archs_from_queue_to_main_dataset(thread_user_info)
                            send_back.extend(back_list)
                            send_archs_back(channel_layer, thread_user_info.channel_name, send_back)
                    if message['data'] == 'ga_started':
                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                          {
                                                              'type': 'ga.started'
                                                          })
                    if message['data'] == 'ga_done':
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                                                          {
                                                              'type': 'ga.finished'
                                                          })
                        print('Ending the thread!')
                        thread.stop()

                p.subscribe(**{request.user.username: my_handler})
                thread = p.run_in_thread(sleep_time=0.001)

                # Start connection with VASSAR
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port)
                client.startConnection()

                problem = request.data['problem']
                inputType = request.data['inputType']

                # Restart archs queue before starting the GA again
                Design.objects.filter(activecontext__exact=user_info.eosscontext.activecontext).delete()
                user_info.eosscontext.last_arch_id = user_info.eosscontext.design_set.count()
                user_info.eosscontext.save()

                # Convert the architecture list and wait for threads to be available (ask for stop again just in case)
                thrift_list = []
                inputs_unique_set = set()

                if inputType == 'binary':
                    for arch in user_info.eosscontext.design_set.all():
                        thrift_list.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                        hashed_input = hash(tuple(json.loads(arch.inputs)))
                        inputs_unique_set.add(hashed_input)
                    client.client.stopGABinaryInput(request.user.username)
                    while client.client.isGABinaryInputRunning():
                        time.sleep(0.1)
                    client.client.startGABinaryInput(problem, thrift_list, request.user.username)

                elif inputType == 'discrete':
                    for arch in user_info.eosscontext.design_set.all():
                        thrift_list.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                        hashed_input = hash(tuple(json.loads(arch.inputs)))
                        inputs_unique_set.add(hashed_input)
                    client.client.stopGADiscreteInput(request.user.username)
                    while client.client.isGADiscreteInputRunning():
                        time.sleep(0.1)
                    client.client.startGADiscreteInput(problem, thrift_list, request.user.username)
                else:
                    raise ValueError('Unrecognized input type: {0}'.format(inputType))

                # End the connection before return statement
                client.endConnection()

                return Response('GA started correctly!')

            except Exception:
                logger.exception('Exception in starting the GA!')
                client.endConnection()
                return Response('')

        else:
            return Response('This is only available to registered users!')


class StopGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

                # Start connection with VASSAR
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port)
                client.startConnection()

                problem = request.data['problem']
                inputType = request.data['inputType']

                # Call the GA stop function on Engineer
                if inputType == 'binary':
                    client.client.stopGABinaryInput(request.user.username)
                    while client.client.isGABinaryInputRunning():
                        time.sleep(0.1)
                elif inputType == 'discrete':
                    client.client.stopGADiscreteInput(request.user.username)
                    while client.client.isGADiscreteInputRunning():
                        time.sleep(0.1)
                else:
                    raise ValueError('Unrecognized input type: {0}'.format(inputType))

                # End the connection before return statement
                client.endConnection()

                return Response('GA stopped correctly!')

            except Exception:
                logger.exception('Exception in stopping the GA!')
                client.endConnection()
                return Response('')

        else:
            return Response('This is only available to registered users!')


class CheckGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # Start connection with VASSAR
                user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                port = user_info.eosscontext.vassar_port
                client = VASSARClient(port)
                client.startConnection()

                inputType = request.data['inputType']

                status = None
                if inputType == 'binary':
                    status = client.client.isGABinaryInputRunning()

                elif inputType == 'discrete':
                    status = client.client.isGADiscreteInputRunning()
                else:
                    raise ValueError('Unrecognized input type: {0}'.format(inputType))

                # End the connection before return statement
                client.endConnection()

                return Response({
                    'ga_status': status
                })

            except Exception:
                logger.exception('Exception in starting the GA!')
                client.endConnection()
                return Response('')

        else:
            return Response('This is only available to registered users!')


class GetArchDetails(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.startConnection()

            assignation_problems = ['SMAP', 'ClimateCentric']
            partition_problems = ['Decadal2017Aerosols']

            # Get the correct architecture
            this_arch = None
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            for arch in user_info.eosscontext.design_set.all():
                if arch.id == arch_id:
                    if problem in assignation_problems:
                        this_arch = BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
                    elif problem in partition_problems:
                        this_arch = DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
                    break

            score_explanation = None
            cost_explanation = None
            if problem in assignation_problems:
                score_explanation = client.client.getArchScienceInformationBinaryInput(problem, this_arch)
                cost_explanation = client.client.getArchCostInformationBinaryInput(problem, this_arch)
            elif problem in partition_problems:
                score_explanation = client.client.getArchScienceInformationDiscreteInput(problem, this_arch)
                cost_explanation = client.client.getArchCostInformationDiscreteInput(problem, this_arch)

            # End the connection before return statement
            client.endConnection()

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

        except Exception:
            logger.exception('Exception when retrieving information from the current architecture!')
            client.endConnection()
            return Response('')


class GetSubobjectiveDetails(APIView):

    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            port = user_info.eosscontext.vassar_port
            client = VASSARClient(port)
            client.startConnection()

            assignation_problems = ['SMAP', 'ClimateCentric']
            partition_problems = ['Decadal2017Aerosols']

            # Get the correct architecture
            this_arch = None
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            for arch in user_info.eosscontext.design_set.all():
                if arch.id == arch_id:
                    if problem in assignation_problems:
                        this_arch = BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
                    elif problem in partition_problems:
                        this_arch = DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
                    break

            subobjective_explanation = None
            if problem in assignation_problems:
                subobjective_explanation = client.client.getSubscoreDetailsBinaryInput(problem, this_arch, request.data['subobjective'])
            elif problem in partition_problems:
                subobjective_explanation = client.client.getSubscoreDetailsDiscreteInput(problem, this_arch, request.data['subobjective'])

            # End the connection before return statement
            client.endConnection()

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

        except Exception:
            logger.exception('Exception when retrieving information from the current architecture!')
            client.endConnection()
            return Response('')
