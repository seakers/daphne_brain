# --> Sample Functions
from SALib.sample import saltelli
from SALib.sample import sobol_sequence


# --> Evaluates sample functions
from SALib.test_functions import Ishigami


# --> Analyze functions with results
from SALib.analyze import sobol


import numpy as np


class PartitionAnalysis:

    def __init__(self, arch_dict_list):
        self.arch_dict_list = arch_dict_list
        self.num_archs = len(arch_dict_list)
        for arch in arch_dict_list:
            print(arch)

    def get_num_inputs(self):
        first_arch = self.arch_dict_list[0]
        return len(first_arch['inputs'])


    def get_problem_form(self):
        # --> Find the number of variables
        num_inputs = self.get_num_inputs()

        # --> Create the variable names
        counter = 1
        var_names = []
        for x in range(0, num_inputs):
            var_names.append('x' + str(counter))
            counter = counter + 1

        # --> Create the bounds for the variables
        var_bounds = []
        for x in range(0, num_inputs):
            var_bounds.append([0, 1])

        problem = {
            'num_vars': num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }
        return problem


    def sobol_analysis(self):
        print("Conducting Sobol Analysis for", len(self.arch_dict_list), "partition architectures")
        problem = self.get_problem_form()
        print(problem)
        return 0