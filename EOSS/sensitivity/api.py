from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling
import itertools

from SALib.sample import saltelli
from SALib.analyze import sobol

# --> Database
from django.contrib.auth.models import User
from daphne_context.models import UserInformation

from auth_API.helpers import create_user_information



import numpy as np





class SensitivityClient:
    def __init__(self, request_user_info, num_instances=5):
        # --> Create sensitivity user
        self.user_id = None
        self.user_info = self.create_sensitivity_user(request_user_info)

        # --> Clients
        self.db_client = GraphqlClient(user_info=self.user_info)
        self.vassar_client = VASSARClient(user_information=self.user_info)
        self.scale_client = EvaluationScaling(self.user_info, num_instances)
        self.scale_client.initialize()

        # --> Sensitivity Variables
        self.orbits = None
        self.instruments = None
        self.architectures = None
        self.set_problem_parameters()

    def shutdown(self):
        self.scale_client.shutdown()

    def create_sensitivity_user(self, user_info_copy):
        temp_db_client = GraphqlClient(user_info=user_info_copy)

        username = 'sensitivity_user'
        email = 'sensitivity@gmail.com'
        password = 'sensitivity'

        # --> Get or create User
        user = None
        if User.objects.filter(username=username).exists():
            print('--> SENSITIVITY USER ALREADY EXISTS')
            user_query = User.objects.filter(username__exact=username)
            user = user_query[0]
            self.user_id = user.id
        else:
            print('--> CREATING NEW SENSITIVITY USER')
            user = User.objects.create_user(username, email, password)
            user.save()
            user_id = user.id
            self.user_id = user_id
            temp_db_client.insert_user_into_group(user_id)

        # --> Get or create UserInformation
        if UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext").exists():
            user_info_query = UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext")
            user_info = user_info_query[0]
        else:
            user_info = create_user_information(username=username)

        # --> Create new dataset for sensitivity analysis
        result = temp_db_client.new_dataset(user.id, user_info_copy.eosscontext.problem_id, "sensitivity")
        dataset_id = result['data']['insert_Dataset_one']['id']

        # --> Copy user information parameters
        user_info.eosscontext.group_id = user_info_copy.eosscontext.group_id
        user_info.eosscontext.problem_id = user_info_copy.eosscontext.problem_id
        user_info.eosscontext.dataset_id = dataset_id
        user_info.save()

        return user_info

    def new_dataset(self):
        result = self.db_client.new_dataset(self.user_id, self.user_info.eosscontext.problem_id, "sensitivity")
        dataset_id = result['data']['insert_Dataset_one']['id']
        self.user_info.eosscontext.dataset_id = dataset_id
        self.user_info.save()

    def set_problem_parameters(self):
        self.orbits = self.vassar_client.get_orbit_list(self.user_info.eosscontext.problem_id)
        self.instruments = self.vassar_client.get_instrument_list_ai4se(self.user_info.eosscontext.problem_id)
        self.architectures = self.db_client.get_architectures_ai4se_form()

    def get_num_inputs(self):
        return len(self.orbits) * len(self.instruments)







    # analysis_type: orbit / instrument
    def get_samples(self, analysis_type):
        d_value = (2 * self.get_num_inputs() + 2)
        print('--> D VALUE', d_value)

        problem = None
        if analysis_type == 'orbit':
            problem = self.get_orbit_analysis_problem()
        else:
            problem = self.get_instrument_analysis_problem()

        samples = saltelli.sample(problem, d_value, calc_second_order=False)
        rounded = np.round(samples, 0).tolist()
        print('--> saltelli samples', len(rounded))
        rounded.sort()
        reduced = list(rounded for rounded, _ in itertools.groupby(rounded))
        print('--> NUMBER OF SAMPLES:', len(reduced))
        return reduced




    def get_instrument_analysis_problem(self):
        # 1. Update problem parameters
        self.set_problem_parameters()

        # 2. Get number of instruments and orbits
        num_inputs = self.get_num_inputs()
        num_insts = len(self.instruments)
        num_orbs = len(self.orbits)

        # 3. Define instrument groups
        var_names = []
        var_bounds = []
        var_group = []
        counter = 1
        for x in range(0, num_orbs):
            for y in range(0, num_insts):
                group_name = 'inst_' + str(y)
                var_group.append(group_name)
                var_names.append('x' + str(counter))
                var_bounds.append([0, 1])
                counter += 1
        return {
            'groups': var_group,
            'num_vars': num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }

    def get_orbit_analysis_problem(self):
        # 1. Update problem parameters
        self.set_problem_parameters()

        # 2. Get number of instruments and orbits
        num_inputs = self.get_num_inputs()
        num_insts = len(self.instruments)
        num_orbs = len(self.orbits)

        # 3. Define instrument groups
        var_names = []
        var_bounds = []
        var_group = []
        counter = 1
        for x in range(0, num_orbs):
            group_name = 'orb_' + str(x)
            for y in range(0, num_insts):
                var_group.append(group_name)
                var_names.append('x' + str(counter))
                var_bounds.append([0, 1])
                counter += 1
        return {
            'groups': var_group,
            'num_vars': num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }





    def calculate_sensitivities(self, new_dataset=False):
        print('--> CALCULATING SENSITIVITIES')

        # 1. Reload problem parameters in case of problem formulation change
        self.set_problem_parameters()
        print('--> SET PROBLEM PARAMETERS')

        # 2. Create new dataset to store evaluations
        if new_dataset:
            self.new_dataset()
        print('--> CREATED NEW DATASET')

        # 2. Generate design samples for sensitivity calculations (2d np-array)
        batch = self.get_samples(analysis_type='orbit')
        print('--> NEW SAMPLES GENERATED')

        # 3. Evaluate samples
        self.scale_client.evaluate_batch(batch)





        return 0







