

from EOSS.sensitivities.service.AssignationAnalysis import AssignationAnalysis
from EOSS.sensitivities.service.PartitionAnalysis import PartitionAnalysis





# This class is the API for the Sensitivities Service
class SensitivitiesClient:

    def __init__(self):
        self.counter = 0


    def assignation_sensitivities(self, arch_dict_list):
        analyzer = AssignationAnalysis(arch_dict_list)
        science_sensitivities, cost_sensitivities = analyzer.sobol_analysis()

        print(science_sensitivities['S1'])
        print(science_sensitivities['S1_conf'])




        return 0



    def partition_sensitivities(self, arch_dict_list):
        analyzer = PartitionAnalysis(arch_dict_list)
        results = analyzer.sobol_analysis()



        return 0