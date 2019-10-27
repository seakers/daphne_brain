




# --> Evaluates the least used orbit - instrument combination
# --> Calculates the percent each combination is seen (num times seen / total architectures)
def evaluate_design_space_level_one(arch_dict_list, orbits, instruments):
    # --> Create a matrix of --> row: architecture - col: orbit instrument pair
    bool_matrix = []
    for arch_dict in arch_dict_list:
        bool_matrix.append(arch_dict['inputs'])

    num_architectures = len(bool_matrix)

    # --> Create the list of summated column values
    summation_list = [0] * len(bool_matrix[0])
    for row in bool_matrix:
        for row_index in range(len(row)):
            if(row[row_index] is True):
                summation_list[row_index] = summation_list[row_index] + 1

    # --> Create the list of pairs(summated column values, index)
    summation_index_list = []
    for x in range(len(summation_list)):
        summation_index_list.append({'value': summation_list[x], 'index': x})

    summation_index_list = sorted(summation_index_list, key=lambda k: k['value'])

    print("Current Results")
    for x in summation_index_list:
        print(x)


    # --> Enumerate Combinations
    combination_key_list = []
    index = 0
    for orb in orbits:
        for inst in instruments:
            combination_key_list.append({'orbit': orb, 'instrument': inst, 'index': index})
            index = index + 1

    # --> Set the ground work for the final dict
    final_dict = {}
    for orb in orbits:
        final_dict[orb] = {}
        for inst in instruments:
            final_dict[orb][inst] = {}


    # --> Fill in the final dictionary
    combo_under_eval_index = 0
    for orb in orbits:
        for inst in instruments:
            value_dict = index_to_value(combo_under_eval_index, summation_index_list)
            value = value_dict['value']
            percent = round((value / num_architectures) * 100, 2)
            final_dict[orb][inst] = {'value': str(value), 'percent': str(percent)}
            combo_under_eval_index = combo_under_eval_index + 1

    #print(final_dict)


    final_list = []
    for entry in summation_index_list:
        index = entry['index']
        value = entry['value']
        obj = index_to_combination(index, combination_key_list)
        percent = round((value / num_architectures) * 100, 2)
        final_list.append({'orbit': obj['orbit'], 'instrument': obj['instrument'], 'value': str(value), 'percent': str(percent)})


    return final_list




def index_to_value(index, values):
    for val in values:
        if val['index'] is index:
            return val
    return False




def index_to_combination(index, combinations):
    for combo in combinations:
        if combo['index'] is index:
            return combo
    return False



def summate_matrix_columns(bool_matrix, combination_index, combinations):
    num_architectures = len(bool_matrix)

    output = index_to_combination(combination_index, combinations)
    print("Evaluating: ", output['orbit'], output['instrument'])


    summation_list = {}
    for x in range(len(bool_matrix)):         # --> Iterate over each architecture
        if bool_matrix[x][combination_index] is True:
            index = 0
            for y in range(len(bool_matrix[0])):  # --> Iterate over each element in an architecture
                if y is combination_index:
                    index = index + 1
                    continue
                if bool_matrix[x][y] is True:
                    if str(index) not in summation_list:
                        summation_list[str(index)] = 1
                    else:
                        summation_list[str(index)] = summation_list[str(index)] + 1
                index = index + 1

    # --> Turn summation_list into a sorted list of dictoinaries with all of our information
    dictionary_list = []
    for key in summation_list:
        key_info = index_to_combination(int(key), combinations)
        percent_seen = round((summation_list[key] / num_architectures) * 100, 2)
        key_num = int(key)

        # --> {'index': index, 'orbit': orbit, 'inst': inst, 'value': value, 'percent': percent}
        temp_dictionary = {'index': str(key_num), 'orbit': key_info['orbit'], 'instrument': key_info['instrument'],
                           'value': str(summation_list[key]), 'percent': str(percent_seen)}
        dictionary_list.append(temp_dictionary)



    dictionary_list = sorted(dictionary_list, key=lambda k: k['percent'])
    return dictionary_list



# --> Evaluates the least used orbit - instrument combination for a given orbit - instrument combination
# --> Calculates the percent each combination is seen for a given combination (num times seen / total architectures)
def evaluate_design_space_level_two(arch_dict_list, orbits, instruments):
    # --> Create a matrix of --> row: architecture - col: orbit instrument pair
    bool_matrix = []
    for arch_dict in arch_dict_list:
        bool_matrix.append(arch_dict['inputs'])

    # --> Enumerate Combinations
    combination_key_list = []
    index = 0
    for orb in orbits:
        for inst in instruments:
            combination_key_list.append({'orbit': orb, 'instrument': inst, 'index': index})
            index = index + 1


    # --> Set the ground work for the final dict
    final_dict = {}
    for orb in orbits:
        final_dict[orb] = {}
        for inst in instruments:
            final_dict[orb][inst] = []


    combo_under_eval_index = 0
    for orb in orbits:
        for inst in instruments:
            # --> now we create create the summation_list
            final_dict[orb][inst] = summate_matrix_columns(bool_matrix, combo_under_eval_index, combination_key_list)
            combo_under_eval_index = combo_under_eval_index + 1


    return final_dict
