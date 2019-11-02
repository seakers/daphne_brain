import threading
import json
from queue import Queue
from time import sleep

from asgiref.sync import async_to_sync

from EOSS.models import ArchitecturesEvaluated, ArchitecturesUpdated, ArchitecturesClicked

# --> Import the problem types
from EOSS.data.problem_specific import assignation_problems, partition_problems

from EOSS.sensitivities.api import SensitivitiesClient


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

    sensitivity_info = get_sensitivity_information(user_info, request)
    orbits = get_orbits(request)
    instruments = get_instruments(request)
    # print(sensitivity_info)



    thought_iteration = 0
    while thread_queue.empty():

        # --> 5 seconds after previous thought iteration
        thought_iteration = thought_iteration + 1
        print("\nTeacher thought iteration", thought_iteration)

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
        print("Architectures Clicked ---", len(archs_clicked))
        print("Architecture Updates ----", len(arch_updates))
        print("Architectures Evaluated -", len(archs_evaluated))



        # ----> Design Space Functionality
        # async_to_sync(channel_layer.send)(channel_name, {'type': 'teacher.design_space'})




        # ----> Objective Space Functionality
        # async_to_sync(channel_layer.send)(channel_name, {'type': 'teacher.objective_space'})






        # ----> Sensitivity Functionality
        if thought_iteration is 1:
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
                                          # --> I have information about sensitive design decisions, would you like to learn more?
        # --> Yes: display chart with short explanation
        # --> No: Ok, more information can be found in the teacher window under sensitivities
        # --> Ask after the thread has been running for at least three ticks and if the user has updated at least one architecture


        # ----> Feature Functionality
        # async_to_sync(channel_layer.send)(channel_name, {'type': 'teacher.features'})
        # --> I have information about driving design features, would you like to learn more?
        # --> Yes: display chart with short explanation
        # --> No: Ok, more information can be found in the teacher window under features

        # --> COMBINE: I have informaiton about sensitive design elements and driving features, would you like to learn more?



        sleep(15)

    print('--> Teacher thread has finished')



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
