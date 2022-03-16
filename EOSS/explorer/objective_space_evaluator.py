import numpy as np
from EOSS.explorer.diversifier import calculate_crowding

# --> Objective: (0 --> Science), (1 --> Cost)
# --> This function will compute a maximum of 10 crowding distance groups for pareto rankings 0 - 10
# --> This will be done for science and cost! So a total of 22 datasets
def evaluate_objective_space(plotDataJson, pareto_rank_range=11):
    print("Evaluating Objective Space")

    considered_architectures = {}
    for pareto_rank in range(pareto_rank_range):
        temp_list = []
        for arch in plotDataJson:
            try:
                if arch['paretoRanking'] <= pareto_rank:
                    temp_list.append(arch)
            except:
                print("This design doesn't have a pareto ranking")
        considered_architectures[pareto_rank] = temp_list


    return_groups = {}
    for objective in range(2):          # --> One iteration per objective
        return_groups[str(objective)] = {}
        for pareto_rank in range(pareto_rank_range):   # --> One iteration per pareto ranking - paretoRanking
            return_groups[str(objective)][str(pareto_rank)] = group_architectures(considered_architectures[pareto_rank], pareto_rank, objective)

    return return_groups


# --> Takes: all the architectures that meet a pareto ranking (list of dictionaries), a pareto ranking, an objective(0 or 1)
# --> Returns: list of grouped architectures based on crowding distance (max of 10 groups)
def group_architectures(architectures, pareto_rank, objective):
    # 1. Sort the pareto front by objective
    sorted_pareto_front = sorted(architectures, key=lambda design: design["outputs"][objective])

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
        while design_idx < len(sorted_pareto_front) - 1 and sorted_pareto_front[design_idx]["outputs"][0] <= subgroup_max:
            subgroup.append(sorted_pareto_front[design_idx])
            design_idx += 1
        objective_groups.append(subgroup)


    return objective_groups
