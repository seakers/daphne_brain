import json
import threading
from queue import Queue
from rest_framework.views import APIView
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from EOSS.graphql.client.Dataset import DatasetGraphqlClient
from EOSS.sensitivities.api import SensitivitiesClient
from EOSS.vassar.api import VASSARClient
from auth_API.helpers import get_or_create_user_information
from EOSS.explorer.design_space_evaluator import evaluate_design_space_level_one
from EOSS.explorer.design_space_evaluator import evaluate_design_space_level_two
from EOSS.explorer.objective_space_evaluator import evaluate_objective_space
from .teacher_agent import teacher_thread, get_driving_features_epsilon_moea
from EOSS.teacher.models import ArchitecturesEvaluated, ArchitecturesUpdated, ArchitecturesClicked


class ClearTeacherUserData(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        ArchitecturesClicked.objects.all().filter(user_information=user_info).delete()
        ArchitecturesUpdated.objects.all().filter(user_information=user_info).delete()
        ArchitecturesEvaluated.objects.all().filter(user_information=user_info).delete()
        return Response({'list': 'test'})


class SetProactiveMode(APIView):
    # --> For each current session, we will have a teacher object as long as that session
    # has a teacher agent window open with "Proactive" set to true...
    # --> This teacher object will be a thread running a proactive teacher
    # --> Later, if the user is registered, the teacher agent will pull that user's ability parameter from a database
    teachersDict = {}

    def post(self, request, format=None):

        # --> Get Daphne user information
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_session = user_info.session
        print("\n--> USER INFO", user_session, user_info.user)

        # --> Get the channel layer
        channel_layer = get_channel_layer()

        # --> Determine the setting for Proactive Mode
        mode = request.data['proactiveMode']

        # --> Proactive Mode: enabled - create a teacher for this session
        if mode == 'enabled':
            print('--> Teacher request')
            if user_session not in self.teachersDict:
                print("--> Request approved for", user_session)
                communication_queue = Queue()
                user_thread = threading.Thread(target=teacher_thread,
                                               args=(request, communication_queue,
                                                     user_info,
                                                     channel_layer))
                user_thread.start()
                self.teachersDict[user_session] = (user_thread, communication_queue)
            else:
                print('--> Request denied, Teacher already assigned')

        # --> Proactive Mode: disabled - remove a teacher for this session
        elif mode == 'disabled':
            print('--> Teacher request')
            if user_session in self.teachersDict:
                print("--> Request approved")
                thread_to_join = (self.teachersDict[user_session])[0]
                communication_queue = (self.teachersDict[user_session])[1]
                communication_queue.put('stop fam')
                thread_to_join.join()
                print("Thread Killed")
                if user_session in self.teachersDict:
                    del self.teachersDict[user_session]
                    print("")

            else:
                print('--> Request denied, no teacher to return')


        print('\n')
        print("Teachers Online", self.teachersDict, "\n")
        return Response({'list': 'test'})


class GetSubjectFeatures(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        features = get_driving_features_epsilon_moea(request, user_info)
        features.sort(key=lambda feature: feature['complexity'])
        question_features = features[:5]
        return_data = json.dumps(question_features)
        return Response(return_data)


class GetSubjectDesignSpace(APIView):
    def post(self, request, format=None):
        print("Getting Subject DesignSpace!!!")

        # --> Get Daphne user information
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        # --> Get the Problem Name
        problem_id = user_info.eosscontext.problem_id
        dataset_id = user_info.eosscontext.dataset_id

        # --> Get the Problem Orbits
        orbits = request.data['orbits']
        orbits = orbits[1:-1]
        orbits = orbits.split(',')
        for x in range(0, len(orbits)):
            orbits[x] = (orbits[x])[1:-1]

        # --> Get the Problem Instruments
        instruments = request.data['instruments']
        instruments = instruments[1:-1]
        instruments = instruments.split(',')
        for x in range(0, len(instruments)):
            instruments[x] = (instruments[x])[1:-1]

        # --> Get all the architectures that daphne is considering right now
        
        # Get problem architectures
        dbClient = DatasetGraphqlClient(user_info)
        dataset = async_to_sync(dbClient.get_architectures)(dataset_id, problem_id)

        def boolean_string_2_boolean_array(boolean_string):
            return [b == "1" for b in boolean_string]
        
        arch_dict_list = []
        for arch in dataset:
            arch_id = arch['id']
            arch_inputs = boolean_string_2_boolean_array(arch['input'])
            arch_outputs = [float(arch['science']), float(arch['cost'])]
            temp_dict = {'id': arch_id, 'inputs': arch_inputs, 'outputs': arch_outputs}
            arch_dict_list.append(temp_dict)

        # --> Call the Design Space Evaluator Service API
        level_one_analysis = evaluate_design_space_level_one(arch_dict_list, orbits, instruments)
        level_two_analysis = evaluate_design_space_level_two(arch_dict_list, orbits, instruments)

        # print("Level 1", level_one_analysis)
        # for key in level_two_analysis:
        #     print("Level 2", level_two_analysis[key])

        return Response({'level_one_analysis': level_one_analysis, 'level_two_analysis': level_two_analysis})


class GetSubjectSensitivities(APIView):
    def post(self, request, format=None):
        print("Getting Subject Sensitivities!!!")
        sensitivities_client = SensitivitiesClient()

        # --> Get Daphne user information
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        problem_id = user_info.eosscontext.problem_id
        dataset_id = user_info.eosscontext.dataset_id

        # --> Get the Problem Name
        # problem = request.data['problem']
        problem = user_info.eosscontext.problem
        print("-------------PROBLEM")
        print(problem)

        # --> Get the Problem Orbits
        orbits = request.data['orbits']
        orbits = orbits[1:-1]
        orbits = orbits.split(',')
        for x in range(0, len(orbits)):
            orbits[x] = (orbits[x])[1:-1]

        # --> Get the Problem Instruments
        instruments = request.data['instruments']
        instruments = instruments[1:-1]
        instruments = instruments.split(',')
        for x in range(0, len(instruments)):
            instruments[x] = (instruments[x])[1:-1]

        # --> Get all the architectures that daphne is considering right now
        # Get problem architectures
        dbClient = DatasetGraphqlClient(user_info)
        dataset = async_to_sync(dbClient.get_architectures)(dataset_id, problem_id)

        def boolean_string_2_boolean_array(boolean_string):
            return [b == "1" for b in boolean_string]
        
        arch_dict_list = []
        for arch in dataset:
            arch_id = arch['id']
            arch_inputs = boolean_string_2_boolean_array(arch['input'])
            arch_outputs = [float(arch['science']), float(arch['cost'])]
            temp_dict = {'id': arch_id, 'inputs': arch_inputs, 'outputs': arch_outputs}
            arch_dict_list.append(temp_dict)

        # --> Call the Sensitivity Service API
        vassar_client = VASSARClient(user_information=user_info)
        problem_type = vassar_client.get_problem_type(problem_id)
        results = False
        if problem_type == "assignation":
            print("Assignation Problem")
            results = sensitivities_client.assignation_sensitivities(arch_dict_list, orbits, instruments, problem)
        elif problem_type == "partition":
            print("Partition Problem")
            results = sensitivities_client.partition_sensitivities(arch_dict_list, orbits, instruments)
        else:
            raise ValueError('Unrecognized problem type: {0}'.format(problem))

        return Response(results)


class GetSubjectObjectiveSpace(APIView):
    def post(self, request, format=None):
        print("Getting Objective Space Information!!!")

        # --> Get Daphne user information
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        # --> Get the Problem Orbits
        orbits = request.data['orbits']
        orbits = orbits[1:-1]
        orbits = orbits.split(',')
        for x in range(0, len(orbits)):
            orbits[x] = (orbits[x])[1:-1]

        # --> Get the Problem Instruments
        instruments = request.data['instruments']
        instruments = instruments[1:-1]
        instruments = instruments.split(',')
        for x in range(0, len(instruments)):
            instruments[x] = (instruments[x])[1:-1]

        # dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

        # --> Get all the architectures that daphne is considering right now
        # arch_dict_list = []
        # for arch in user_info.eosscontext.design_set.all():
        #     temp_dict = {'id': arch.id, 'inputs': json.loads(arch.inputs), 'outputs': json.loads(arch.outputs), 'paretoRanking': arch.paretoRanking}
        #     arch_dict_list.append(temp_dict)


        plotData = request.data['plotData']
        plotDataJson = json.loads(plotData)
        objectiveSpaceInformation = evaluate_objective_space(plotDataJson)

        return_data = json.dumps(objectiveSpaceInformation)

        return Response(return_data)


class GetObjectiveGroupInformation(APIView):
    def post(self, request, format=None):
        print("Getting Objective Group Information!!!")

        # --> Get Daphne user information
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        # # --> Connect to VASSAR
        # port = user_info.eosscontext.vassar_port
        # client = VASSARClient(port)
        # client.start_connection()

        # --> Get the Problem Name
        problem = request.data['problem']

        groupData = request.data['groupData']
        groupData = json.loads(groupData)
        print(groupData)

        # --> VASSAR local search will take a list of bools

        return Response({})
