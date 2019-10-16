

from EOSS.sensitivities.service.AssignationAnalysis import AssignationAnalysis
from EOSS.sensitivities.service.PartitionAnalysis import PartitionAnalysis



# ----------------------------------------
# sensitivities
# --> 'S1': level one sensitivities
# --> 'S2': level two sensitivities
# --> 'ST': total sensitivities
# --> 'S1_conf': confidence interval for level one sensitivities
# --> 'S2_conf': confidence interval for level one sensitivities
# --> 'ST_conf': confidence interval for total sensitivities
# ----------------------------------------
def format_sensitivities(sensitivities, orbits, instruments):

    # --> Get the total data
    s1_dict = {}
    st_dict = {}
    s1_data = sensitivities['S1']
    s2_data = format_s2_data(sensitivities['S2'], orbits, instruments)
    st_data = sensitivities['ST']
    counter = 0
    for orb in orbits:
        s1_dict[orb] = {}
        st_dict[orb] = {}
        for inst in instruments:
            s1_dict[orb][inst] = str(round(s1_data[counter], 3))
            st_dict[orb][inst] = str(st_data[counter])
            counter = counter + 1


    # --> Top sensitivities for S1
    min_s1_list = max_sensitivities_s1(sensitivities['S1'], orbits, instruments, 10)


    total_data = {'S1': s1_dict, 'S2': s2_data, 'ST': st_dict, 'S1_mins': min_s1_list}
    return total_data


# --> This will return an N by N matrix where N = numOrbits * numInstruments
def format_s2_data(s2_data, orbits, instruments):
    # --> turn everything into a list
    s2_list = []
    for row in range(len(s2_data)):
        temp_list = list(s2_data[row])
        s2_list.append(temp_list)

    # iterate over every row in the data
    # --> row: index of row being edited
    for row in range(len(s2_list)):
        if(row is 0):
            continue
        for left_data_index in range(row):
            s2_list[row][left_data_index] = s2_list[left_data_index][row]

    for row in range(len(s2_list)):
        for idx in range(len(s2_list[row])):
            s2_list[row][idx] = str(round( (s2_list[row][idx]) , 3))
    return s2_list





# --> sensitivities: list of n sensitivities where n = number of parameters
# --> condition: num_return < len(sensitivities)
# --> returns list of [orbit, sensor, sensitivity] with strongest first order sensitivities
def max_sensitivities_s1(sensitivities, orbits, instruments, num_return=3):
    list_values = []
    min_indicies = []
    sensitivities = list(sensitivities)
    temp_sensitivities = sensitivities[:]
    for x in range(num_return):
        min_val = min(temp_sensitivities)
        min_indicies.append(sensitivities.index(min_val))
        temp_sensitivities.remove(min_val)

    for x in range(num_return):
        counter = 0
        for orb in orbits:
            for inst in instruments:
                if counter == min_indicies[x]:
                    list_values.append([orb, inst, str(round(sensitivities[min_indicies[x]], 3))])
                counter = counter + 1
    return list_values


# --> sensitivities: list of n sensitivities where n = number of parameters
# --> condition: num_return < len(sensitivities)
# --> returns list of [orbit, sensor, orbit, sensor sensitivity] with strongest second order sensitivities
def max_sensitivities_s2(sensitivities, orbits, instruments, num_return=3):
    # --> Turn everything into a list
    sensitivities = list(sensitivities)
    for x in range(sensitivities):
        sensitivities[x] = list(sensitivities[x])
    return 0


# This class is the API for the Sensitivities Service
class SensitivitiesClient:

    def __init__(self):
        self.counter = 0


    def assignation_sensitivities(self, arch_dict_list, orbits, instruments):
        # --> Create the Sensitivity Service
        analyzer = AssignationAnalysis(arch_dict_list)

        # --> Get Sensitivity Results
        science_sensitivities, cost_sensitivities = analyzer.sobol_analysis()

        print("Science S1", science_sensitivities['S1'])
        print("Science S2", science_sensitivities['S2'])

        # --> Format Sensitivity Results
        science_data = format_sensitivities(science_sensitivities, orbits, instruments)
        cost_data = format_sensitivities(cost_sensitivities, orbits, instruments)

        final_data = {'science': science_data, 'cost': cost_data}
        return final_data



    def partition_sensitivities(self, arch_dict_list, orbits, instruments):
        analyzer = PartitionAnalysis(arch_dict_list)
        results = analyzer.sobol_analysis()



        return 0