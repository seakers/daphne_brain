import random
from statistics import mean

import numpy as np
import scipy.stats as st


class RealTimeSampling:


    # -- Assume 30 evaluation containers are running
    # -- Assume


    def __init__(self, instruments, orbits, size=10000):
        self.instruments = instruments
        self.orbits = orbits
        self.num_inputs = len(self.instruments) * len(self.orbits)
        self.designs = self.generate_design_set(size)
        self.objectives = ['cost', 'data_continuity', 'programmatic_risk', 'fairness', 'Oceanic', 'Atmosphere', 'Terrestrial']

        # --> RESULTS
        self.results = []

    def generate_design_set(self, size):
        designs = []
        for x in range(size):
            designs.append(self.generate_design())
        return designs

    def generate_design(self):
        return [random.randint(0, 1) for x in range(0, self.num_inputs)]

    def update_results(self, results):
        self.results = results

    def get_samples(self):
        return self.designs


    def calc_main_effects(self, results):
        self.update_results(results)
        inst_effects, all_effects = self.instrument_effects()
        return {
            'instruments': inst_effects,
            'orbits': self.orbit_effects(),
            'all': all_effects
        }




    def orbit_effects(self, results=None):
        if results:
            self.update_results(results)
        effects = {}
        num_insts = len(self.instruments)
        num_orbs = len(self.orbits)
        for orb_idx, orbit in enumerate(self.orbits):
            orb_effects = []
            for inst_idx, instrument in enumerate(self.instruments):
                bit_idx = (orb_idx * num_insts) + inst_idx
                orb_effects.append(self.split_results(bit_idx))
            effects[orbit] = self.merge_effects(orb_effects)
        return effects

    def instrument_effects(self, results=None):
        if results:
            self.update_results(results)
        effects = {}
        single_effects = {}
        num_insts = len(self.instruments)
        num_orbs = len(self.orbits)
        for inst_idx, instrument in enumerate(self.instruments):
            inst_effects = []
            for orb_idx, orbit in enumerate(self.orbits):
                single_name = instrument + '__' + orbit
                bit_idx = (orb_idx * num_insts) + inst_idx
                results = self.split_results(bit_idx)
                single_effects[single_name] = results
                inst_effects.append(results)
            effects[instrument] = self.merge_effects(inst_effects)
        return effects, single_effects

    def merge_effects(self, inst_effects):
        merged = {}
        for objective in self.objectives:
            obj_effects = []
            obj_c_low = []
            obj_c_high = []
            for effect in inst_effects:
                if effect[objective][0]:
                    obj_effects.append(effect[objective][0])
                if effect[objective][1]:
                    obj_c_low.append(effect[objective][1])
                if effect[objective][2]:
                    obj_c_high.append(effect[objective][2])

            merged[objective] = [mean(obj_effects), mean(obj_c_low), mean(obj_c_high)]
        return merged

    def init_bit_split(self):
        split_dict = {}
        for objective in self.objectives:
            split_dict[objective] = []
        return split_dict

    def split_results(self, bit_index):
        bit_false = self.init_bit_split()
        bit_true = self.init_bit_split()
        for result in self.results:
            if result['input'][bit_index] == '0':
                for objective in self.objectives:
                    bit_false[objective].append(result[objective])
            else:
                for objective in self.objectives:
                    bit_true[objective].append(result[objective])
        result_dict = {}
        for objective in self.objectives:
            result_dict[objective] = self.find_local_results(bit_true[objective], bit_false[objective])

        return result_dict

    def find_local_results(self, bit_true_samples, bit_false_samples):
        bit_true_mean, bit_true_interval_low, bit_true_interval_high = self.find_confidence_interval(bit_true_samples)
        bit_false_mean, bit_false_interval_low, bit_false_interval_high = self.find_confidence_interval(bit_false_samples)

        if bit_true_interval_low is None and bit_false_interval_low is None:
            return [None, None, None]
        if bit_true_interval_low is None:
            return [None, None, None]
        if bit_false_interval_low is None:
            return [None, None, None]

        t_low_err = abs(bit_true_mean - bit_true_interval_low)
        t_high_err = abs(bit_true_mean - bit_true_interval_high)
        f_low_err = abs(bit_false_mean - bit_false_interval_low)
        f_high_err = abs(bit_false_mean - bit_false_interval_high)

        diff_mean = bit_true_mean - bit_false_mean
        diff_c_low = diff_mean - (t_low_err + f_high_err)
        diff_c_high = diff_mean + (t_high_err + f_low_err)

        return [diff_mean, diff_c_low, diff_c_high]



    def find_confidence_interval(self, samples):
        num_samples = len(samples)

        sample_mean = None
        c_interval_low = None
        c_interval_high = None

        if num_samples == 0:
            return sample_mean, c_interval_low, c_interval_high
        elif num_samples < 30:
            results = st.t.interval(alpha=0.95, df=num_samples-1, loc=np.mean(samples), scale=st.sem(samples))
            c_interval_low = results[0]
            c_interval_high = results[1]
        else:
            results = st.norm.interval(alpha=0.95, loc=np.mean(samples), scale=st.sem(samples))
            c_interval_low = results[0]
            c_interval_high = results[1]

        sample_mean = np.mean(samples)
        return sample_mean, c_interval_low, c_interval_high










