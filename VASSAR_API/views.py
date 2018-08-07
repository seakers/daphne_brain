import logging
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import redis

from VASSAR_API.VASSARInterface.ttypes import BinaryInputArchitecture
from VASSAR_API.VASSARInterface.ttypes import DiscreteInputArchitecture
from VASSAR_API.api import VASSARClient
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Get an instance of a logger
logger = logging.getLogger('VASSAR')

class GetOrbitList(APIView):
    
    def post(self, request, format=None):
        try:
            # Start connection with VASSAR
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
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
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
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
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
            # Start connection with VASSAR
            self.VASSARClient.startConnection()
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architecture = self.VASSARClient.evaluateArchitecture(request.session['problem'], inputs)

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []
            if 'context' not in request.session:
                request.session['context'] = {}
            if 'current_design_id' not in request.session['context']:
                request.session['context']['current_design_id'] = None

            is_same = True
            for old_arch in request.session['data']:
                is_same = True
                for i in range(len(old_arch['outputs'])):
                    if old_arch['outputs'][i] != architecture['outputs'][i]:
                        is_same = False
                if is_same:
                    break

            if not is_same:
                architecture['id'] = request.session['archID']
                request.session['context']['current_design_id'] = architecture['id']
                print(request.session['context']['current_design_id'])
                request.session['data'].append(architecture)
                request.session['archID'] += 1

            request.session.modified = True

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
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            self.VASSARClient = VASSARClient(port)
            self.VASSARClient.startConnection()
                        
            inputs = request.data['inputs']
            inputs = json.loads(inputs)

            architectures = self.VASSARClient.runLocalSearch(inputs)

            # If there is no session data, initialize and create a new dataset
            if 'data' not in request.session:
                request.session['data'] = []
                
            if 'archID' not in request.session:
                request.session['archID'] = None

            self.architectures = request.session['data']
            self.archID = request.session['archID'] 
            
            if self.archID is None:
                self.archID = 0
                
            for arch in architectures:                
                arch['id'] = self.archID
                self.archID += 1
                self.architectures.append(arch)
            
            request.session['archID'] = self.archID            
            request.session['data'] = self.architectures
            
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
        request.session['vassar_port'] = new_port
        request.session.modified = True
        return Response('')


class StartGA(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # Start connection with VASSAR
                port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
                client = VASSARClient(port)
                client.startConnection()

                problem = request.data['problem']
                inputType = request.data['inputType']

                # Convert the architecture list
                thrift_list = []
                inputs_unique_set = set()

                if inputType == 'binary':
                    for arch in request.session['data']:
                        thrift_list.append(BinaryInputArchitecture(arch['id'], arch['inputs'], arch['outputs']))
                        hashed_input = hash(tuple(arch['inputs']))
                        inputs_unique_set.add(hashed_input)
                        client.client.startGABinaryInput(problem, thrift_list, request.user.username)

                elif inputType == 'discrete':
                    for arch in request.session['data']:
                        thrift_list.append(DiscreteInputArchitecture(arch['id'], arch['inputs'], arch['outputs']))
                        hashed_input = hash(tuple(arch['inputs']))
                        inputs_unique_set.add(hashed_input)
                        client.client.startGADiscreteInput(problem, thrift_list, request.user.username)
                else:
                    raise ValueError('Unrecognized input type: {0}'.format(inputType))

                # End the connection before return statement
                client.endConnection()

                # Start listening for redis inputs to share through websockets
                r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
                p = r.pubsub()

                def my_handler(message):
                    if message['data'] == 'new_arch':
                        print('Processing some new archs!')
                        nonlocal inputs_unique_set
                        nonlocal request
                        # Archs are added in pairs
                        new_archs = r.lrange(request.user.username, -2, -1)
                        send_back = []
                        # Add archs to the context data before sending back to user
                        for arch in new_archs:
                            arch = json.loads(arch)
                            hashed_input = hash(tuple(arch['inputs']))
                            if hashed_input not in inputs_unique_set:
                                full_arch = {'id': request.session['archID'], 'inputs': arch['inputs'], 'outputs': arch['outputs']}
                                request.session['data'].append(full_arch)
                                request.session['archID'] += 1
                                send_back.append(full_arch)
                                inputs_unique_set.add(hashed_input)
                                request.session.save()

                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(request.session['channel_name'],
                                                          {
                                                              'type': 'ga.new_archs',
                                                              'archs': send_back
                                                          })
                    if message['data'] == 'ga_done':
                        print('Ending the thread!')
                        thread.stop()


                p.subscribe(**{request.user.username: my_handler})
                thread = p.run_in_thread(sleep_time=0.001)
                return Response('GA started correctly!')

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
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            client = VASSARClient(port)
            client.startConnection()

            assignation_problems = ['SMAP', 'ClimateCentric']
            partition_problems = ['Decadal2017Aerosols']

            # Get the correct architecture
            this_arch = None
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            for arch in request.session['data']:
                if arch['id'] == arch_id:
                    if problem in assignation_problems:
                        this_arch = BinaryInputArchitecture(arch['id'], arch['inputs'], arch['outputs'])
                    elif problem in partition_problems:
                        this_arch = DiscreteInputArchitecture(arch['id'], arch['inputs'], arch['outputs'])
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
            port = request.session['vassar_port'] if 'vassar_port' in request.session else 9090
            client = VASSARClient(port)
            client.startConnection()

            assignation_problems = ['SMAP', 'ClimateCentric']
            partition_problems = ['Decadal2017Aerosols']

            # Get the correct architecture
            this_arch = None
            arch_id = int(request.data['arch_id'])
            problem = request.data['problem']
            for arch in request.session['data']:
                if arch['id'] == arch_id:
                    if problem in assignation_problems:
                        this_arch = BinaryInputArchitecture(arch['id'], arch['inputs'], arch['outputs'])
                    elif problem in partition_problems:
                        this_arch = DiscreteInputArchitecture(arch['id'], arch['inputs'], arch['outputs'])
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
