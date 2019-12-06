import os
import json
import csv
import pika
import logging
import threading

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.data import problem_specific
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture, \
    ContinuousInputArchitecture, AssigningProblemEntities
from EOSS.models import Design
from auth_API.helpers import get_or_create_user_information
from EOSS.data_mining.api import DataMiningClient

# Get an instance of a logger
logger = logging.getLogger('EOSS.analyst')


# Create your views here.
class GetDrivingFeatures(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

            # Get threshold values for the metrics
            supp = float(request.data['supp'])
            conf = float(request.data['conf'])
            lift = float(request.data['lift'])
            
            # Get selected arch id's
            selected = request.data['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.data['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.data['problem']
            input_type = request.data['input_type']

            logger.debug('getDrivingFeatures() called ... ')
            logger.debug('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral), len(non_behavioral), len(dataset)))
        
            _archs = []
            if input_type == "binary":
                for arch in dataset:
                    _archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getDrivingFeaturesBinary(problem, behavioral, non_behavioral, _archs, supp, conf, lift)

            elif input_type == "discrete":
                for arch in dataset:
                    _archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getDrivingFeaturesDiscrete(problem, behavioral, non_behavioral, _archs, supp, conf, lift)

            else:
                raise NotImplementedError("Unsupported input type: {0}".format(input_type))

            features = []
            for df in _features:
                features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics, 'complexity': df.complexity})

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(features)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetDrivingFeaturesEpsilonMOEA(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            session_key = request.session.session_key
            
            # Get selected arch id's
            selected = request.data['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.data['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.data['problem']
            input_type = request.data['input_type']

            logger.debug('getDrivingFeaturesEpsilonMOEA() called ... ')
            logger.debug('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral), len(non_behavioral), len(dataset)))
        
            _archs = []
            if input_type == "binary":
                for arch in dataset:
                    _archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getDrivingFeaturesEpsilonMOEABinary(session_key, problem, behavioral, non_behavioral, _archs)

            elif input_type == "discrete":
                for arch in dataset:
                    _archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getDrivingFeaturesEpsilonMOEADiscrete(session_key, problem, behavioral, non_behavioral, _archs)

            elif input_type == "continuous":
                for arch in dataset:
                    inputs = []
                    for i in arch['inputs']:
                        if i is None:
                            pass
                        else:
                            inputs.append(float(i))
                            
                    _archs.append(ContinuousInputArchitecture(arch['id'], inputs, arch['outputs']))
                _features = self.DataMiningClient.client.getDrivingFeaturesEpsilonMOEAContinuous(problem, behavioral, non_behavioral, _archs)

            features = []
            for df in _features:
                features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(features)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetDrivingFeaturesWithGeneralization(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            session_key = request.session.session_key

            # Get selected arch id's
            selected = request.data['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.data['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.data['problem']
            input_type = request.data['input_type']

            logger.debug('getDrivingFeaturesWithGeneralization() called ...')
            logger.debug('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(dataset)))
            
            _all_archs = []
            if input_type == "binary":
                for arch in dataset:
                    _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getDrivingFeaturesWithGeneralizationBinary(session_key, problem, behavioral, non_behavioral, _all_archs)

            elif input_type == "discrete":
                raise NotImplementedError("Data mining with generalization not implemented for discrete input problem.")

            features = []
            for df in _features:
                features.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(features)
        
        except Exception as detail:
            logger.exception('Exception in getDrivingFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetMarginalDrivingFeatures(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            session_key = request.session.session_key
                        
            # Get selected arch id's
            behavioral = json.loads(request.data['selected'])
            non_behavioral = json.loads(request.data['non_selected'])
                
            feature_expression = request.data['featureExpression']
            logical_connective = request.data['logical_connective']

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.data['problem']
            input_type = request.data['input_type']

            logger.debug('getMarginalDrivingFeatures() called ... ')
            logger.debug('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(dataset)))
                
            _all_archs = []
            if input_type == "binary":

                # Start listening for redis inputs to share through websockets
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                channel = connection.channel()
                channel.queue_declare(queue=session_key + '_localSearch')
                channel.queue_purge(queue=session_key + '_localSearch')

                def callback(ch, method, properties, body):
                    thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
                    message = json.loads(body)

                    if message['type'] == 'search_started':
                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                        {
                            'type': 'data.mining.search.started',
                        })

                    if message['type'] == 'search_finished':
                        message['type'] = 'data.mining.search.finished'
                        message['searchMethod'] = 'localSearch'

                        logger.debug('Ending the thread!')
                        channel.stop_consuming()
                        channel.close()

                        if 'features' in message:
                            if message['features'] != None and len(message['features']) != 0: 
                                logger.debug('Features from local search returned')

                        # Look for channel to send back to user
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(thread_user_info.channel_name, message)

                channel.basic_consume(queue=session_key + '_localSearch',
                                      on_message_callback=callback)
                thread = threading.Thread(target=channel.start_consuming)
                thread.start()

                for arch in dataset:
                    _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                self.DataMiningClient.client.getMarginalDrivingFeaturesBinary(session_key, problem, behavioral, non_behavioral, _all_archs,
                                                                           feature_expression, logical_connective)
                _features = []

            elif input_type == "discrete":
                for arch in dataset:
                    _all_archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.DataMiningClient.client.getMarginalDrivingFeaturesDiscrete(session_key, problem, behavioral, non_behavioral, _all_archs,
                                                                           feature_expression, logical_connective)
                        
            features = []
            for df in _features:
                features.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics, 'complexity':df.complexity})
                    
            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(features)
        
        except Exception as detail:
            logger.exception('Exception in calling GetMarginalDrivingFeatures(): ' + detail)
            self.DataMiningClient.endConnection()
            return Response('')


class GeneralizeFeature(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        # Start listening for redis inputs to share through websockets
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        session_key = request.session.session_key
        logger.debug("GeneralizeFeature (session key: {0})".format(session_key))

        channel.queue_declare(queue=session_key + '_generalization')
        channel.queue_purge(queue=session_key + '_generalization')

        try:
            user_initiated = request.data['userInitiated']
        except KeyError:
            user_initiated = None

        def callback(ch, method, properties, body):
            thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            message = json.loads(body)

            if message['type'] == 'search_started':
                # Look for channel to send back to user
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(thread_user_info.channel_name,
                {
                    'type': 'data.mining.search.started',
                })

            if message['type'] == 'search_finished':
                logger.debug('Ending the thread!')
                channel.stop_consuming()
                channel.close()

                message['type'] = 'data.mining.search.finished'
                message['searchMethod'] = 'generalization'
                message['userInitiated'] = user_initiated

                if 'features' in message:
                    if message['features'] != None and len(message['features']) != 0: 
                        logger.debug('Generalized features returned')

                # Look for channel to send back to user
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(thread_user_info.channel_name, message)

        channel.basic_consume(queue=session_key + '_generalization',
                              on_message_callback=callback)
        thread = threading.Thread(target=channel.start_consuming)
        thread.start()

        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            # Get user information
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            
            # Get selected arch id's
            behavioral = json.loads(request.data['selected'])
            non_behavioral = json.loads(request.data['non_selected'])
                
            root_feature_expression = request.data['rootFeatureExpression']
            node_feature_expression = request.data['nodeFeatureExpression']

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            problem = request.data['problem']
            input_type = request.data['input_type']

            logger.debug('generalizeFeature() called ... ')
            logger.debug('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(dataset)))

            _all_archs = []
            if input_type == "binary":
                for arch in dataset:
                    _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))

                self.DataMiningClient.client.generalizeFeatureBinary(session_key, problem, behavioral, non_behavioral, _all_archs,
                                                                           root_feature_expression, node_feature_expression)

            elif input_type == "discrete":
                raise NotImplementedError()

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(None)
        
        except Exception as detail:
            logger.exception('Exception in calling GeneralizeFeature()')
            self.DataMiningClient.endConnection()
            return Response('')


class SimplifyFeatureExpression(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            session_key = request.session.session_key

            # Start data mining client
            self.DataMiningClient.startConnection()

            # Get problem name
            problem = request.data['problem']

            # Get the expression
            expression = request.data['expression']
            simplified_feature = self.DataMiningClient.client.simplifyFeatureExpression(session_key, problem, expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(simplified_feature)
        
        except Exception as detail:
            logger.exception('Exception in simplifying feature: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ClusterData(APIView):

    def post(self, request, format=None):
        
        try:
            param = int(request.data['param'])

            problem = request.data['problem']
            input_type = request.data['input_type']

            # Get selected arch id's
            selected = request.data['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.data['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            architectures = request.session['data']

            data = []
            for arch in architectures:
                if arch['id'] in behavioral:
                    data.append(arch['outputs'])
                else:
                    pass

            id_list = behavioral

            # dir_path = os.path.dirname(os.path.realpath(__file__))
            # with open(os.path.join(dir_path,"data.csv"), "w") as file:

            #     for i, row in enumerate(data):
            #         out = []
            #         out.append(str(id_list[i]))

            #         for val in row:
            #             out.append(str(val))
            #         out = ",".join(out)
            #         file.write(out + "\n")

            from cluster import Clustering
            
            clustering = Clustering(data)

            labels = clustering.kMeans(param)

            out = {
                "id": id_list,
                "labels": labels
            }
            
            return Response(out)
        
        except Exception as detail:
            logger.exception('Exception in clustering: ' + str(detail))
            return Response('')


class GetCluster(APIView):

    def post(self, request, format=None):
        try:

            dir_path = os.path.dirname(os.path.realpath(__file__))
            labels = []
            id_list = []

            with open(os.path.join(dir_path, "labels.csv"), "r") as file:

                content = file.read().split("\n")

                for row in content:
                    if row == "":
                        continue
                    elif "," in row:
                        id_list.append(row.split(",")[0])
                        labels.append(row.split(",")[1])
                    else:
                        labels.append(row)

            out = {
                "id": id_list,
                "labels": labels
            }
            return Response(out)
        
        except Exception as detail:
            logger.exception('Exception in getting cluster labels: ' + str(detail))
            return Response('')        


class ConvertToDNF(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.data['expression']
            dnf_expression = self.DataMiningClient.client.convertToDNF(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(dnf_expression)
        
        except Exception as detail:
            logger.exception('Exception in convertingToDNF: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ConvertToCNF(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.data['expression']
            cnf_expression = self.DataMiningClient.client.convertToCNF(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(cnf_expression)
        
        except Exception as detail:
            logger.exception('Exception in convertingToCNF: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeTypicality(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            # Get selected arch id's
            input_string = request.data['input']
            input_string = input_string[1:-1]
            input_split = input_string.split(',')

            # Convert strings to ints
            inputs = []
            for i in input_split:
                inputs.append(int(i))

            # Get the expression
            expression = request.data['expression']

            _arch = BinaryInputArchitecture(0, inputs, [])
            typicality = self.DataMiningClient.client.computeAlgebraicTypicality(_arch, expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(typicality)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexity: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeComplexity(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expression = request.data['expression']
            complexity = self.DataMiningClient.client.computeComplexity(expression)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(complexity)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexity: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class ComputeComplexityOfFeatures(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()
        pass

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()
            
            # Get the expression
            expressions = request.data['expressions']
            expressions = json.loads(expressions)

            complexity = self.DataMiningClient.client.computeComplexityOfFeatures(expressions)

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(complexity)
        
        except Exception as detail:
            logger.exception('Exception in ComputeComplexityOfFeatures: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetProblemParameters(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        try:
            session_key = request.session.session_key

            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.data['problem']

            params = None
            if problem == "ClimateCentric":
                params_ = self.DataMiningClient.client.getAssigningProblemEntities(session_key, problem)
                params = {}
                params['leftSet'] = params_.leftSet
                params['rightSet'] = params_.rightSet

                concept_hierarchy_ = self.DataMiningClient.client.getAssigningProblemConceptHierarchy(session_key, problem, AssigningProblemEntities(params['leftSet'], params['rightSet']))
                params['instanceMap'] = concept_hierarchy_.instanceMap
                params['superclassMap'] = concept_hierarchy_.superclassMap
                
            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(params)
        
        except Exception as detail:
            logger.exception('Exception in GetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class SetProblemParameters(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        # Start listening for redis inputs to share through websockets
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        session_key = request.session.session_key
        logger.debug("SetProblemParameters (session key: {0})".format(session_key))

        channel.queue_declare(queue=session_key + '_problemSetting')
        channel.queue_purge(queue=session_key + '_problemSetting')

        def callback(ch, method, properties, body):
            thread_user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            message = json.loads(body)

            logger.debug("Problem parameters received: (session key: {0})".format(session_key))

            if message['type'] == 'entities':
                message['type'] = 'data.mining.problem.entities'

                # Look for channel to send back to user
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(thread_user_info.channel_name, message)

        channel.basic_consume(queue=session_key + '_problemSetting',
                              on_message_callback=callback)
        thread = threading.Thread(target=channel.start_consuming)
        thread.start()

        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            problem = request.data['problem']
            params = json.loads(request.data['params'])

            if problem in problem_specific.assignation_problems:
                entities = AssigningProblemEntities(params['instrument_list'], params['orbit_list'])
                self.DataMiningClient.client.setAssigningProblemEntities(session_key, problem, entities)

            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response()
        
        except Exception as detail:
            logger.exception('Exception in SetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class SetProblemGeneralizedConcepts(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            # Start data mining client
            self.DataMiningClient.startConnection()

            session_key = request.session.session_key
            logger.debug("SetProblemGeneralizedConcepts (session key: {0})".format(session_key))
            
            problem = request.data['problem']
            params = json.loads(request.data['params'])

            if problem == "ClimateCentric":
                orbit_generalized_concepts = []
                instrument_generalized_concepts = []

                for concept in params['orbit_extended_list']:
                    if concept in params['orbit_list']:
                        pass
                    else:
                        orbit_generalized_concepts.append(concept)

                for concept in params['instrument_extended_list']:
                    if concept in params['instrument_list']:
                        pass
                    else:
                        instrument_generalized_concepts.append(concept)

                entities = AssigningProblemEntities(instrument_generalized_concepts, orbit_generalized_concepts)
                self.DataMiningClient.client.setAssigningProblemGeneralizedConcepts(session_key, problem, entities)
            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response()
        
        except Exception as detail:
            logger.exception('Exception in SetProblemParameters: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


class GetProblemConceptHierarchy(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            session_key = request.session.session_key

            # Start data mining client
            self.DataMiningClient.startConnection()
            
            problem = request.data['problem']
            params = json.loads(request.data['params'])

            concept_hierarchy = None
            if problem == "ClimateCentric":
                params = AssigningProblemEntities(params["instrument_list"],params["orbit_list"])
                concept_hierarhcy_ = self.DataMiningClient.client.getAssigningProblemConceptHierarchy(session_key, problem, params)
                concept_hierarchy = {}
                concept_hierarchy['instanceMap'] = concept_hierarhcy_.instanceMap
                concept_hierarchy['superclassMap'] = concept_hierarhcy_.superclassMap
            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

            # End the connection before return statement
            self.DataMiningClient.endConnection() 
            return Response(concept_hierarchy)
        
        except Exception as detail:
            logger.exception('Exception in calling getProblemConceptHierarchy: ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')


def boolean_array_2_boolean_string(boolean_array):
    leng = len(boolean_array)
    bool_string = ''
    for i in range(leng):
        if boolean_array[i]:
            bool_string += '1'
        else:
            bool_string += '0'
    return bool_string


class ImportTargetSelection(APIView):
    def post(self, request, format=None):
        try:
            filename = request.data['filename']
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

            selected_arch_ids = []

            with open(file_path, "r") as file:

                content = file.read().split("\n")

                for row in content:
                    if row == "":
                        continue

                    elif "," in row:
                        id = row.split(",")[0]
                        label = row.split(",")[1]

                        if label == "1":
                            selected_arch_ids.append(int(id))

            return Response(selected_arch_ids)
        
        except Exception as detail:
            logger.exception('Exception in getting cluster labels: ' + str(detail))
            return Response('') 


class ExportTargetSelection(APIView):
    def post(self, request, format=None):
        try:
            problem = request.data['problem']
            input_type = request.data['input_type']
            filename = request.data['name']

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

            # Get selected arch id's
            selected = request.data['selected']
            selected = selected[1:-1]
            selected_arch_ids = selected.split(',')
            # Convert strings to ints
            behavioral = []
            for s in selected_arch_ids:
                behavioral.append(int(s))

            # Get non-selected arch id's
            non_selected = request.data['non_selected']
            non_selected = non_selected[1:-1]
            non_selected_arch_ids = non_selected.split(',')
            # Convert strings to ints
            non_behavioral = []
            for s in non_selected_arch_ids:
                non_behavioral.append(int(s))

            # Load architecture data from the session info
            dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

            import datetime
            timestamp = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")

            if filename is None:
                filename = ""
            else:
                pass
            filename = filename + "_" + timestamp + ".selection"

            # Set the path of the file containing data
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

            #########################################
            #########################################
            ### Write data file with labels

            with open(file_path, "w") as file:

                content = []
                for i, arch in enumerate(dataset):
                    line = []

                    label = None
                    if arch.id in behavioral:
                        label = "1"
                    else:
                        label = "0"

                    inputs = json.loads(arch.inputs)

                    input_string = ""
                    for val in inputs:
                        print(val)
                        if val:
                            input_string += "1"
                        else:
                            input_string += "0"

                    line.append(str(arch.id))
                    line.append(str(label))

                    line.append(input_string)

                    outputs = json.loads(arch.outputs)
                    line.append(str(outputs[0]))
                    line.append(str(outputs[1]))
                    content.append(",".join(line))    

                file.write("\n".join(content))

            #########################################
            #########################################

            return Response('')
        
        except Exception:
            logger.exception('Exception in exporting target selection')
            return Response('')


class ImportFeatureData(APIView):
    def post(self, request, format=None):
        try:
            # Set the path of the file containing data
            filename_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', request.data['filename_data'])
            filename_params = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', request.data['filename_params'])

            out = {}
            out['params'] = []
            out['data'] = []
            features = []

            # Open the data file
            with open(filename_data) as csvfile:
                # Read the file as a csv file
                read = csv.reader(csvfile, delimiter=' ')

                # For each row, store the information
                for i, row in enumerate(read):
                    if i == 0: # Check if the first line is a header
                        if row[0].startswith("#"):
                            continue

                    index = int(row[0])
                    feature_expression = row[1]

                    if len(row) > 5:  # All metrics are included
                        support = float(row[2])
                        lift = float(row[3])
                        coverage = float(row[4])
                        specificity = float(row[5])
                        complexity = float(row[6])
                        metrics = [support, lift, coverage, specificity]
                        
                    else:  # Only coverage and specificity are included in the data
                        coverage = float(row[2])
                        specificity = float(row[3])
                        complexity = float(row[4])
                        metrics = [-1, -1, coverage, specificity]

                    features.append({'id': index, 'name': feature_expression, 'expression': feature_expression, 'metrics': metrics, 'complexity': complexity})

            # Import parameters
            params = None
            if os.path.isfile(filename_params):
                # Open the file
                with open(filename_params) as f:
                    params = json.loads(f.read())

            out['data'] = features
            out['params'] = params
            return Response(out)
        
        except Exception:
            logger.exception('Exception in importing feature data')
            return Response('')


class StopSearch(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DataMiningClient = DataMiningClient()

    def post(self, request, format=None):
        try:
            session_key = request.session.session_key

            # Start connection with DataMiningClient
            self.DataMiningClient.startConnection()

            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
            logger.debug("StopSearch (session key: {0})".format(request.session.session_key))

            # Stop the generalization search
            self.DataMiningClient.client.stopSearch(session_key)

            # End the connection before return statement
            self.DataMiningClient.endConnection()
            return Response('Generalization stopped correctly!')

        except Exception as detail:
            logger.exception('Exception in StopSearch(): ' + str(detail))
            self.DataMiningClient.endConnection()
            return Response('')
