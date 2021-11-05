import random
from statistics import mean


class RealTimeSampling:


    # -- Assume 30 evaluation containers are running
    # -- Assume


    def __init__(self, instruments, orbits, size=5000):
        self.instruments = instruments
        self.orbits = orbits
        self.num_inputs = len(self.instruments) * len(self.orbits)
        self.designs = self.generate_design_set(size)
        self.objectives = ['cost', 'data_continuity', 'programmatic_risk', 'fairness', 'oceanic', 'terrestrial', 'atmosphere']

        # --> RESULTS
        self.results = []

    def generate_design_set(self, size):
        designs = []
        for x in range(size):
            designs.append(self.generate_design())
        return designs

    def generate_design(self):
        return [random.randint(0, 1) for x in range(self.num_inputs)]

    def update_results(self, results):
        self.results = results

    def get_samples(self):
        return self.designs

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
        num_insts = len(self.instruments)
        num_orbs = len(self.orbits)
        for inst_idx, instrument in enumerate(self.instruments):
            inst_effects = []
            for orb_idx, orbit in enumerate(self.orbits):
                bit_idx = (orb_idx * num_insts) + inst_idx
                inst_effects.append(self.split_results(bit_idx))
            effects[instrument] = self.merge_effects(inst_effects)
        return effects

    def merge_effects(self, inst_effects):
        merged = {}
        for objective in self.objectives:
            obj_effects = []
            for effect in inst_effects:
                obj_effects.append(effect[objective])
            merged[objective] = mean(obj_effects)
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
            result_dict[objective] = mean(bit_true[objective]) - mean(bit_false[objective])
        return result_dict










