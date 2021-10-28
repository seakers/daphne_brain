from SALib.sample import saltelli
import numpy as np


# This is for problems assigning instruments to orbits
class AssigningSampling:
    def __init__(self, instruments, orbits, group=True):
        self.instruments = instruments
        self.orbits = orbits
        self.num_inputs = len(self.instruments) * len(self.orbits)
        self.d_value = (2 * self.num_inputs + 2)

        # --> Problems
        self.orbit_problem = self.build_orbit_problem()
        self.instrument_problem = self.build_instrument_problem()


    def build_orbit_problem(self):
        var_names = []
        var_bounds = []
        var_group = []
        counter = 1
        for x in range(0, len(self.orbits)):
            group_name = self.orbits[x]
            for y in range(0, len(self.instruments)):
                var_group.append(group_name)
                var_names.append('x' + str(counter))
                var_bounds.append([0, 1])
                counter += 1
        return {
            'groups': var_group,
            'num_vars': self.num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }

    def build_instrument_problem(self):
        var_names = []
        var_bounds = []
        var_group = []
        counter = 1
        for x in range(0, len(self.orbits)):
            for y in range(0, len(self.instruments)):
                group_name = self.instruments[y]
                var_group.append(group_name)
                var_names.append('x' + str(counter))
                var_bounds.append([0, 1])
                counter += 1
        return {
            'groups': var_group,
            'num_vars': self.num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }

    def get_orbit_samples(self):
        samples = saltelli.sample(self.orbit_problem, self.d_value, calc_second_order=False)
        print('--> NUMBER OF ORBIT SAMPLES:', len(samples))
        return np.round(samples, 0).tolist()

    def get_instrument_samples(self):
        samples = saltelli.sample(self.instrument_problem, self.d_value, calc_second_order=False)
        print('--> NUMBER OF INSTRUMENT SAMPLES:', len(samples))
        return np.round(samples, 0).tolist()



