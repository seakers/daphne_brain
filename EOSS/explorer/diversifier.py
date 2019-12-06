import datetime
import json
import random

import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from EOSS.models import EOSSContext, Design
from daphne_context.models import DialogueHistory


def activate_diversifier(eosscontext: EOSSContext):
    if not eosscontext.activecontext.check_for_diversity:
        return

    # 1. Compute the pareto front
    dataset = Design.objects.filter(eosscontext_id__exact=eosscontext.id).all()
    json_dataset = []
    for design in dataset:
        json_dataset.append({
            "id": design.id,
            "inputs": json.loads(design.inputs),
            "outputs": json.loads(design.outputs)
        })
    pareto_front = compute_pareto_front(json_dataset, [1, -1])
    sorted_pareto_front = sorted(pareto_front, key=lambda design: design["outputs"][0])

    # 2. Compute the crowding distances of the pareto front
    scores = np.zeros(shape=(len(sorted_pareto_front), 2))
    for idx, design in enumerate(sorted_pareto_front):
        scores[idx] = design["outputs"]
    crowding_distances = calculate_crowding(scores)

    for idx, design in enumerate(sorted_pareto_front):
        design["crowding"] = crowding_distances[idx]

    # 3. Separate the designs in 10 uniform sets by one objective
    objective_span = sorted_pareto_front[-1]["outputs"][0] - sorted_pareto_front[0]["outputs"][0]
    objective_min = sorted_pareto_front[0]["outputs"][0]
    objective_groups = []
    design_idx = 1
    for i in range(10):
        subgroup_span = objective_span / 10
        subgroup_min = objective_min + subgroup_span * i
        subgroup_max = subgroup_min + subgroup_span
        subgroup = []
        while design_idx < len(sorted_pareto_front)-1 and sorted_pareto_front[design_idx]["outputs"][0] <= subgroup_max:
            subgroup.append(sorted_pareto_front[design_idx])
            design_idx += 1
        objective_groups.append(subgroup)

    # 4. Choose the group with the maximum crowding distance.
    max_crowding = 0
    max_idx = []
    group_max_crowding = []
    for idx, group in enumerate(objective_groups):
        max_group_crowding = max(group, key=lambda design: design["crowding"], default={"crowding": 2})["crowding"]
        group_max_crowding.append(max_group_crowding)
        if max_group_crowding > max_crowding:
            max_crowding = max_group_crowding
            max_idx = [idx]
        elif max_group_crowding == max_crowding:
            max_idx.append(idx)
    # TODO: Change metric so that empty areas get priority over non-empty ones and the arch that is sent is the closest to that area

    # 5. If it's more than 1.x that of other groups, choose an architecture of that group
    # 6. Notify the user to try investigating around that architecture
    is_considerably_larger = True
    for idx, group_crowding in enumerate(group_max_crowding):
        if idx not in max_idx:
            if max_crowding/group_crowding < 1.3:
                is_considerably_larger = False

    if is_considerably_larger:
        group_idx = random.choice(max_idx)
        group = objective_groups[group_idx]
        group_size = len(group)
        # look for the closest non-empty group
        if group_size == 0:
            do_incr = True
            idx_incr = 0
            while group_size == 0:
                idx_incr = -idx_incr
                if do_incr:
                    idx_incr += 1
                    do_incr = False
                else:
                    do_incr = True
                new_group_idx = group_idx + idx_incr
                if new_group_idx >= 0 and new_group_idx < len(objective_groups):
                    group = objective_groups[new_group_idx]
                    group_size = len(group)
            if idx_incr > 0:
                chosen_arch = group[0]
            else:
                chosen_arch = group[-1]
        else:
            chosen_arch = group[int(group_size/2)]

        message = {
            'voice_message': 'I have detected an area in the Pareto front which is relatively unexplored. Do you want '
                             'me to select an architecture close to it so you can start exploring it?',
            'visual_message_type': ['active_message'],
            'visual_message': [
                {
                    'message': 'I have detected an area in the Pareto front which is relatively unexplored. Do you want'
                               ' me to select an architecture close to it so you can start exploring it?',
                    'setting': 'modification',
                    'modification': {
                        'type': 'set_diversifier_id',
                        'arch_id': chosen_arch["id"]
                    }
                }
            ],
            "writer": "daphne",
        }
        DialogueHistory.objects.create(user_information=eosscontext.user_information,
                                       voice_message=message["voice_message"],
                                       visual_message_type=json.dumps(message["visual_message_type"]),
                                       visual_message=json.dumps(message["visual_message"]),
                                       writer="daphne",
                                       date=datetime.datetime.utcnow())
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(eosscontext.user_information.channel_name,
                                          {
                                              'type': 'active.message',
                                              'message': message
                                          })


def compute_pareto_front(population, objective_sign):
    pop_size = len(population)
    obj_num = 2

    domination_counter = [0] * pop_size

    for i in range(pop_size):
        for j in range(i+1, pop_size):
            # check each objective for dominance
            dominate = [0] * obj_num
            for k in range(obj_num):
                if population[i]['outputs'][k] > population[j]['outputs'][k]:
                    dominate[k] = objective_sign[k]*1
                elif population[i]['outputs'][k] < population[j]['outputs'][k]:
                    dominate[k] = objective_sign[k]*-1
            if -1 not in dominate and 1 in dominate:
                domination_counter[j] += 1
            elif -1 in dominate and 1 not in dominate:
                domination_counter[i] += 1

    pareto_solutions = []
    for i in range(len(domination_counter)):
        if domination_counter[i] == 0:
            pareto_solutions.append(population[i])
    return pareto_solutions


def calculate_crowding(scores):
    # Crowding is based on a vector for each individual
    # All dimension is normalised between low and high. For any one dimension, all
    # solutions are sorted in order low to high. Crowding for chromsome x
    # for that score is the difference between the next highest and next
    # lowest score. Total crowding value sums all crowding for all scores

    # From https://pythonhealthcare.org/2018/10/06/95-when-too-many-multi-objective-solutions-exist-selecting-solutions-based-on-crowding-distances

    population_size = len(scores[:, 0])
    number_of_scores = len(scores[0, :])

    # create crowding matrix of population (row) and score (column)
    crowding_matrix = np.zeros((population_size, number_of_scores))

    # normalise scores (ptp is max-min)
    normed_scores = (scores - scores.min(0)) / scores.ptp(0)

    # calculate crowding distance for each score in turn
    for col in range(number_of_scores):
        crowding = np.zeros(population_size)

        # end points have maximum crowding
        crowding[0] = 1
        crowding[population_size - 1] = 1

        # Sort each score (to calculate crowding between adjacent scores)
        sorted_scores = np.sort(normed_scores[:, col])

        sorted_scores_index = np.argsort(normed_scores[:, col])

        # Calculate crowding distance for each individual
        crowding[1:population_size - 1] = (sorted_scores[2:population_size] - sorted_scores[0:population_size - 2])

        # resort to orginal order (two steps)
        re_sort_order = np.argsort(sorted_scores_index)
        sorted_crowding = crowding[re_sort_order]

        # Record crowding distances
        crowding_matrix[:, col] = sorted_crowding

    # Sum crowding distances of each score
    crowding_distances = np.sum(crowding_matrix, axis=1)

    return crowding_distances
