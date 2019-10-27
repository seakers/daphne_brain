# --> Sample Functions
from SALib.sample import saltelli
from SALib.sample import sobol_sequence


# --> VASSAR for the latin hypercube sampling
from EOSS.vassar.api import VASSARClient

# --> Evaluates sample functions
from SALib.test_functions import Ishigami

# --> Analyze functions with results
from SALib.analyze import sobol

from pyDOE import lhs


import numpy as np


# -------------------------------------------
# arch_dict_list
# --> id: int_value
# --> inputs: [x1, x2, ..., xN]
# --> outputs: [science, cost]
# -------------------------------------------

class AssignationAnalysis:

    def __init__(self, arch_dict_list, vassar_port, problem):
        self.arch_dict_list = arch_dict_list
        self.num_archs = len(arch_dict_list)
        self.vassar_port = vassar_port
        self.problem = problem


    def get_num_inputs(self):
        first_arch = self.arch_dict_list[0]
        return len(first_arch['inputs'])


    # --> Currently sets bounds as [0, 1] --> Can we make this binary instead?
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


    # --> Returns numpy array for science output, cost output
    # --> Must have results such that:  num_arches % (2 * num_inputs + 2) = 0
    def get_science_cost_lists(self):
        num_inputs = self.get_num_inputs()
        d_value = (2 * num_inputs + 2)

        # --> Reduce the number of architectures such that the equation above is met
        arch_dict_list_modified = self.arch_dict_list
        while(len(arch_dict_list_modified) % d_value != 0):
            del arch_dict_list_modified[-1]

        # --> Get the science and cost scores
        science_list = []
        cost_list = []
        for arch in arch_dict_list_modified:
            science_list.append(arch['outputs'][0])
            cost_list.append(arch['outputs'][1])
        return np.array(science_list), np.array(cost_list)






    def latin_hypercube_sampling(self):
        print("------------------------------------")



        num_inputs = self.get_num_inputs()
        d_value = (2 * num_inputs + 2)
        lhd = lhs(num_inputs, samples=d_value)


        lhd = list(lhd)
        arch_input_list = []
        for x in range(len(lhd)):
            arch_input_list.append(list(lhd[x]))

        architectures = []
        for x in range(len(arch_input_list)):
            arch_row = []
            for y in range(len(arch_input_list[x])):
                if arch_input_list[x][y] < 0.5:
                    arch_row.append(False)
                else:
                    arch_row.append(True)
            architectures.append(arch_row)


        # Start connection with VASSAR to evaluate architectures
        # client = VASSARClient(self.vassar_port)
        # client.start_connection()

        # test = client.evaluate_architecture(self.problem, architectures[0])
        # print(test)

        # for arch in architectures:
        #     client.evaluate_architecture(self.problem, arch)


        #print(architectures)
        print("------------------------------------")



    def sobol_analysis(self):
        print("Conducting Sobol Analysis for", len(self.arch_dict_list), "assignation architectures")
        problem = self.get_problem_form()

        # --> Get the respective science and cost outputs for the architectures
        science_list, cost_list = self.get_science_cost_lists()

        # --> Calculate science and cost sensitivities
        science_sensitivities = sobol.analyze(problem, science_list)
        cost_sensitivities = sobol.analyze(problem, cost_list)


        test = self.latin_hypercube_sampling()


        # --> Return the science and cost sensitivities
        return science_sensitivities, cost_sensitivities







