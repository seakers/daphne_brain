from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.docker.api import DockerClient

from SALib.sample import saltelli
from SALib.analyze import sobol

import numpy as np





class SensitivityAnalysis:
    def __init__(self, user_info):
        self.db_client = GraphqlClient(user_info=user_info)
        self.vassar_client = VASSARClient(user_information=user_info)
        self.orbits = None
        self.instruments = None
        self.architectures = None
        self.set_problem_parameters()

    def set_problem_parameters(self):
        self.orbits = self.vassar_client.get_orbit_list()
        self.instruments = self.vassar_client.get_instrument_list()
        self.architectures = self.db_client.get_architectures_ai4se_form()

    def get_num_inputs(self):
        return len(self.orbits) * len(self.instruments)

    def get_samples(self, num_samples=None):
        d_value = (2 * self.get_num_inputs() + 2)

        # Must have n samples such that: n % d_value = 0
        if not num_samples:
            num_samples = 10
            while (num_samples % d_value) != 0:
                num_samples = num_samples + 1

        samples = saltelli.sample(self.get_problem(), num_samples)
        np.round(samples, 0)
        return samples

    def get_problem(self):
        num_inputs = self.get_num_inputs()
        counter = 1
        var_names = []
        var_bounds = []
        for x in range(0, num_inputs):
            var_names.append('x' + str(counter))
            var_bounds.append([0, 1])
            counter = counter + 1
        return {
            'num_vars': num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }






