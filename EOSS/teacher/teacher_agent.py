import threading
import json
from queue import Queue
import random
from time import sleep
import math
from asgiref.sync import async_to_sync
from EOSS.models import ArchitecturesEvaluated, ArchitecturesUpdated, ArchitecturesClicked
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture, ContinuousInputArchitecture, AssigningProblemEntities
from EOSS.explorer.objective_space_evaluator import evaluate_objective_space
from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.sensitivities.api import SensitivitiesClient
from EOSS.explorer.design_space_evaluator import evaluate_design_space_level_one
from EOSS.explorer.design_space_evaluator import evaluate_design_space_level_two
from EOSS.data_mining.api import DataMiningClient
from EOSS.models import Design


# --> This function will be the proactive teacher agent
def teacher_thread(request, thread_queue, user_info, channel_layer):
    session = user_info.session
    user = user_info.user
    channel_name = user_info.channel_name
    print('\n----- Teacher thread -----')
    print('----> session:', session)
    print('----> user:', user)
    print('----> channel name:', channel_name)
    print('--------------------------', '\n')

    # --> Architectures
    arch_dict_list = []
    for arch in user_info.eosscontext.design_set.all():
        temp_dict = {'id': arch.id, 'inputs': json.loads(arch.inputs), 'outputs': json.loads(arch.outputs)}
        arch_dict_list.append(temp_dict)

    # --> Orbits : Instruments
    orbits = get_orbits(request)
    instruments = get_instruments(request)

    # --> Sensitivities
    sensitivity_info = get_sensitivity_information(user_info, request)

    # --> Design Space
    level_one_analysis = evaluate_design_space_level_one(arch_dict_list, orbits, instruments)
    level_two_analysis = evaluate_design_space_level_two(arch_dict_list, orbits, instruments)
    design_space_info = {'level_one_analysis': level_one_analysis, 'level_two_analysis': level_two_analysis}

    # --> Objective Space
    plotData = request.data['plotData']
    plotDataJson = json.loads(plotData)
    objectiveSpaceInformation = evaluate_objective_space(plotDataJson)
    objective_space_science = objectiveSpaceInformation['0']
    objective_space_cost = objectiveSpaceInformation['1']
    objective_space_science_1 = objective_space_science['1']
    objective_space_science_5 = objective_space_science['5']

    # --> Features
    features = get_driving_features_epsilon_moea(request, user_info)
    features.sort(key=lambda feature: feature['score'])
    top_features = features[:5]
    features.sort(key=lambda feature: feature['overall'])


    # --> Set initial user information
    archs_clicked_data = ArchitecturesClicked.objects.all().filter(user_information=user_info)
    arch_updates_data = ArchitecturesUpdated.objects.all().filter(user_information=user_info)
    archs_evaluated_data = ArchitecturesEvaluated.objects.all().filter(user_information=user_info)
    archs_clicked = []
    arch_updates = []
    archs_evaluated = []
    for arch in archs_clicked_data:
        archs_clicked.append(json.loads(arch.arch_clicked))
    for arch in arch_updates_data:
        arch_updates.append(json.loads(arch.arch_updated))
    for arch in archs_evaluated_data:
        archs_evaluated.append(json.loads(arch.arch_evaluated))
    num_evaluated = len(archs_evaluated)
    num_updates = len(arch_updates)
    num_clicked = len(archs_clicked)

    num_clicked_previous = num_clicked
    num_evaluated_previous = num_evaluated
    num_updates_previous = num_updates

    one_evals_counter = num_evaluated
    one_evals = False

    two_evals_counter = num_evaluated
    two_evals = False

    three_evals_counter = num_evaluated
    three_evals = False

    four_evals_counter = num_evaluated
    four_evals = False

    five_evals_counter = num_evaluated
    five_evals = False

    sensitivity_info_given = False
    feature_info_given = False
    design_space_info_given = False
    objective_space_info_given = False

    send_message = False

    question_given = False



    # generate_design_prediction_question(arch_dict_list, orbits, instruments)





    thought_iteration = 0
    seconds = 0
    while thread_queue.empty():

        # --> 5 seconds after previous thought iteration
        thought_iteration = thought_iteration + 1
        if thought_iteration % 100 == 0:
            seconds = seconds + 1
            print("Second:", seconds)

        # --> Get all relevant information from the database
        archs_clicked_data = ArchitecturesClicked.objects.all().filter(user_information=user_info)
        arch_updates_data = ArchitecturesUpdated.objects.all().filter(user_information=user_info)
        archs_evaluated_data = ArchitecturesEvaluated.objects.all().filter(user_information=user_info)
        archs_clicked = []
        arch_updates = []
        archs_evaluated = []
        for arch in archs_clicked_data:
            archs_clicked.append(json.loads(arch.arch_clicked))
        for arch in arch_updates_data:
            arch_updates.append(json.loads(arch.arch_updated))
        for arch in archs_evaluated_data:
            archs_evaluated.append(json.loads(arch.arch_evaluated))
        num_evaluated = len(archs_evaluated)
        num_updates = len(arch_updates)
        num_clicked = len(archs_clicked)

        # --> Determine if the user has evaluted 2 or 3 designs since the last 2 or 3
        if num_evaluated - one_evals_counter >= 1:
            one_evals = True
            one_evals_counter = num_evaluated
        if num_evaluated - two_evals_counter >= 2:
            two_evals = True
            two_evals_counter = num_evaluated
        if num_evaluated - three_evals_counter >= 3:
            three_evals = True
            three_evals_counter = num_evaluated
        if num_evaluated - four_evals_counter >= 4:
            four_evals = True
            four_evals_counter = num_evaluated
        if num_evaluated - five_evals_counter >= 5:
            five_evals = True
            five_evals_counter = num_evaluated

        # ---------------------------------------------------------------------------------Objective Space Functionality
        if thought_iteration == 2000:
            async_to_sync(channel_layer.send)(channel_name, {
                'type': 'teacher.objective_space',
                'name': 'displayObjectiveSpaceInformation',
                'data': objective_space_science_1,
                'speak': 'ping',
                "voice_message": "",
                "visual_message_type": ["objective_space_plot"],
                "visual_message": [""],
                "writer": "daphne"
            })
            objective_space_info_given = True

        # ------------------------------------------------------------------------------------------------- Design Space
        if thought_iteration == 4000:
            async_to_sync(channel_layer.send)(channel_name, {
                'type': 'teacher.design_space',
                'name': 'displayDesignSpaceInformation',
                'data': design_space_info,
                'speak': 'ping',
                "voice_message": 'testing',
                "visual_message_type": ["design_space_plot"],
                "visual_message": ["ping"],
                "writer": "daphne"
            })
            design_space_info_given = True

        # ----------------------------------------------------------------------------------------------------- Question
        if thought_iteration % 6000 == 0:
            rand = random.random()
            if rand < 0.33:
                first_choice_info, second_choice_info, correct_answer, question = generate_design_prediction_question(
                    arch_dict_list, orbits, instruments)
                async_to_sync(channel_layer.send)(channel_name, {
                    'type': 'teacher.design_space',
                    'name': 'designQuestion',
                    'data': None,
                    'speak': 'ping',
                    "voice_message": 'testing',
                    "visual_message_type": ["question_template"],
                    "visual_message": ["ping"],
                    "first_choice": first_choice_info,
                    "second_choice": second_choice_info,
                    "correct_answer": correct_answer,
                    "question": question,
                    "writer": "daphne"
                })
            elif rand < .66:
                first_choice_info, second_choice_info, correct_answer, question = generate_sensitivity_question(
                    sensitivity_info)
                first_choice = first_choice_info[0] + ' - ' + first_choice_info[1]
                second_choice = second_choice_info[0] + ' - ' + second_choice_info[1]
                second_choice_revealed = second_choice_info[0] + ' - ' + second_choice_info[
                    1] + '  Sensitivity: ' + str(second_choice_info[2])
                first_choice_revealed = first_choice_info[0] + ' - ' + first_choice_info[
                    1] + '  Sensitivity: ' + str(first_choice_info[2])
                async_to_sync(channel_layer.send)(channel_name, {
                    'type': 'teacher.sensitivities',
                    'name': 'sensitivityQuestion',
                    'data': None,
                    'speak': 'ping',
                    "voice_message": 'testing',
                    "visual_message_type": ["question_template"],
                    "visual_message": ["ping"],
                    "first_choice": first_choice,
                    "second_choice": second_choice,
                    "first_choice_revealed": first_choice_revealed,
                    "second_choice_revealed": second_choice_revealed,
                    "correct_answer": correct_answer,
                    "question": question,
                    "writer": "daphne"
                })
            else:
                feature_choices, answer = generate_feature_question(features)
                async_to_sync(channel_layer.send)(channel_name, {
                    'type': 'teacher.features',
                    'name': 'featureQuestion',
                    'first_choice': feature_choices[0],
                    'second_choice': feature_choices[1],
                    'correct_answer': answer,
                    'question': 'Which of the two features better describes the Pareto Front?',
                })

        # -------------------------------------------------------------------------------------Sensitivity Functionality
        if thought_iteration == 9000:
            async_to_sync(channel_layer.send)(channel_name, {
                        'type': 'teacher.sensitivities',
                        'name': 'displaySensitivityInformation',
                        'data': sensitivity_info,
                        'speak': 'ping',
                        "voice_message": 'testing',
                        "visual_message_type": ["sensitivity_plot"],
                        "visual_message": ["ping"],
                        "writer": "daphne"
                    })
            sensitivity_info_given = True

        # -----------------------------------------------------------------------------------------Feature Functionality
        if thought_iteration == 15000:
            async_to_sync(channel_layer.send)(channel_name, {
                        'type': 'teacher.features',
                        'name': 'displayFeatureInformation',
                        'data': top_features,
                    })
            feature_info_given = True





        one_evals = False
        two_evals = False
        three_evals = False
        four_evals = False
        sleep(0.01)

    print('--> Teacher thread has finished')





# --> Questions

def generate_design_prediction_question(designs, orbits, instruments):
    objectives = ['lower cost', 'higher science']
    objective = random.choice(objectives)

    # --> Default to science questions for now
    objective = 'higher science'

    question = 'Which design will produce a ' + objective + ' value?'

    # --> Sort designs by cost
    designs.sort(key=lambda design: design['outputs'][1])
    first_design = random.choice(designs)
    first_design_index = designs.index(first_design)
    second_design_index = 0
    if (first_design_index+1) < len(designs):
        second_design_index = first_design_index + 1
    else:
        second_design_index = first_design_index - 1
    second_design = designs[second_design_index]


    correct_answer = 0
    if objective == 'lower cost':
        if first_design['outputs'][1] > second_design['outputs'][1]:
            correct_answer = 1

    elif objective == 'higher science':
        if first_design['outputs'][0] < second_design['outputs'][0]:
            correct_answer = 1

    first_design_elements = get_design_orbit_instrument_combinations(orbits, instruments, first_design)
    second_design_elements = get_design_orbit_instrument_combinations(orbits, instruments, second_design)


    first_design_dict = dict()
    for element in first_design_elements:
        key = element[0]
        inst = element[1]
        if key not in first_design_dict.keys():
            first_design_dict[key] = []
        first_design_dict[key].append(inst)

    second_design_dict = dict()
    for element in second_design_elements:
        key = element[0]
        inst = element[1]
        if key not in second_design_dict.keys():
            second_design_dict[key] = []
        second_design_dict[key].append(inst)

    return first_design_dict, second_design_dict, correct_answer, question

def generate_sensitivity_question(sensitivities):
    rand = random.random()
    objective = ''
    data = 0

    if rand > 0.7:
        print('Cost Question', rand)
        objective = 'Cost'
        data = sensitivities['science']['S1']
    else:
        print('Science Question', rand)
        objective = 'Science'
        data = sensitivities['cost']['S1']

    orbit_key_list = [*data]
    orbit = random.choice(orbit_key_list)

    instrument_data = data[orbit]
    instrument_key_list = [*instrument_data]
    first_inst = random.choice(instrument_key_list)
    instrument_key_list.remove(first_inst)
    second_inst = random.choice(instrument_key_list)

    first_choice_info = [orbit, first_inst, data[orbit][first_inst]]
    second_choice_info = [orbit, second_inst, data[orbit][second_inst]]
    correct_answer = 0
    if abs(float(first_choice_info[2])) < abs(float(second_choice_info[2])):
        correct_answer = 1

    question = 'Which design decision has a higher sensitivity for ' + str(objective) + '?'
    first_choice = first_choice_info[0] + ' - ' + first_choice_info[1]
    second_choice = second_choice_info[0] + ' - ' + second_choice_info[1]


    return first_choice_info, second_choice_info, correct_answer, question

def generate_feature_question(features):
    num_features = len(features)
    first_feature = random.choice(features)
    first_feature_index = features.index(first_feature)
    features.remove(first_feature)
    second_feature = random.choice(features)
    second_feature_index = features.index(second_feature)
    correct_choice = 0
    if first_feature['overall'] < second_feature['overall']:
        correct_choice = 1
    else:
        correct_choice = 0
    print("Feature Question")
    print("First", first_feature)
    print("Second", second_feature)
    print(correct_choice)
    return [first_feature, second_feature], correct_choice






def get_driving_features_epsilon_moea(request, user_info, pareto=0):
    client = DataMiningClient()
    client.startConnection()

    session_key = request.session.session_key
    problem = request.data['problem']
    input_type = request.data['input_type']

    # --> All architectures
    dataset = Design.objects.filter(eosscontext_id__exact=user_info.eosscontext.id).all()

    # --> Get architectures in the pareto front with ranking 5: list of dictionaries
    plotData = request.data['plotData']
    plotDataJson = json.loads(plotData)

    designs_low_ranking = []
    designs_low_ranking_id = []
    designs_high_ranking = []
    designs_high_ranking_id = []
    for design in plotDataJson:
        try:
            if design['paretoRanking'] <= pareto:
                designs_low_ranking.append(design)
                designs_low_ranking_id.append(int(design['id']))
            else:
                designs_high_ranking.append(design)
                designs_high_ranking_id.append(int(design['id']))
        except:
            continue



    _archs = []
    if input_type == 'binary':
        for arch in dataset:
            _archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
        _features = client.client.getDrivingFeaturesEpsilonMOEABinary(session_key, problem, designs_low_ranking_id, designs_high_ranking_id, _archs)
    elif input_type == 'discrete':
        for arch in dataset:
            _archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
        _features = client.client.getDrivingFeaturesEpsilonMOEADiscrete(session_key, problem, designs_low_ranking_id, designs_high_ranking_id, _archs)


    features = []
    for df in _features:
        fm = df.metrics
        cov = fm[2] * 100
        sen = fm[3] * 100
        distance_value = abs(fm[2] - fm[3])
        overall = cov * cov + sen * sen
        features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics, 'score': distance_value, 'overall': overall})

    client.endConnection()
    features.sort(key=lambda feature: feature['score'])

    return features





def get_design_orbit_instrument_combinations(orbits, instruments, design):
    inputs = design['inputs']
    combinations = []

    for index in range(len(inputs)):
        if inputs[index] is True:
            combinations.append(get_orbit_instrument_from_index(orbits, instruments, index))

    return combinations

def get_orbit_instrument_from_index(orbits, instruments, index):
    total_combinations = len(orbits) * len(instruments)
    orbit_index = math.floor(index / len(instruments))
    instrument_index = index - (orbit_index * len(instruments))
    return [orbits[orbit_index], instruments[instrument_index]]



def get_orbits(request):
    # --> Get the Problem Orbits
    orbits = request.data['orbits']
    orbits = orbits[1:-1]
    orbits = orbits.split(',')
    for x in range(0, len(orbits)):
        orbits[x] = (orbits[x])[1:-1]
    return orbits

def get_instruments(request):
    # --> Get the Problem Instruments
    instruments = request.data['instruments']
    instruments = instruments[1:-1]
    instruments = instruments.split(',')
    for x in range(0, len(instruments)):
        instruments[x] = (instruments[x])[1:-1]
    return instruments

def get_sensitivity_information(user_info, request):
    # --> Sensitivity Information ----------------------------------------------------------------------
    sensitivities_client = SensitivitiesClient()
    problem = user_info.eosscontext.problem
    port = user_info.eosscontext.vassar_port

    orbits = request.data['orbits']
    orbits = orbits[1:-1]
    orbits = orbits.split(',')
    for x in range(0, len(orbits)):
        orbits[x] = (orbits[x])[1:-1]

    instruments = request.data['instruments']
    instruments = instruments[1:-1]
    instruments = instruments.split(',')
    for x in range(0, len(instruments)):
        instruments[x] = (instruments[x])[1:-1]

    arch_dict_list = []
    for arch in user_info.eosscontext.design_set.all():
        temp_dict = {'id': arch.id, 'inputs': json.loads(arch.inputs), 'outputs': json.loads(arch.outputs)}
        arch_dict_list.append(temp_dict)

    # --> Call the Sensitivity Service API
    sensitivity_results = False
    if problem in assignation_problems:
        print("Assignation Problem")
        sensitivity_results = sensitivities_client.assignation_sensitivities(arch_dict_list, orbits, instruments, port, problem)
    elif problem in partition_problems:
        print("Partition Problem")
        sensitivity_results = sensitivities_client.partition_sensitivities(arch_dict_list, orbits, instruments)
    else:
        raise ValueError('Unrecognized problem type: {0}'.format(problem))
    return sensitivity_results