from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling

from SALib.sample import saltelli
from SALib.analyze import sobol

# --> Database
from django.contrib.auth.models import User
from daphne_context.models import UserInformation

from auth_API.helpers import create_user_information



import numpy as np





class SensitivityClient:
    def __init__(self, request_user_info, num_instances=3):
        # --> Create sensitivity user
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
        else:
            print('--> CREATING NEW SENSITIVITY USER')
            user = User.objects.create_user(username, email, password)
            user.save()
            user_id = user.id
            temp_db_client.insert_user_into_group(user_id)

        # --> Get or create UserInformation
        if UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext").exists():
            user_info_query = UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext")
            user_info = user_info_query[0]
        else:
            user_info = create_user_information(username=username)

        # --> Create new dataset for sensitivity analysis
        result = temp_db_client.new_dataset(user.id, user_info_copy.eosscontext.problem_id, "sensitivity")
        print(result)
        dataset_id = result['data']['insert_Dataset_one']['id']

        # --> Copy user information parameters
        user_info.eosscontext.group_id = user_info_copy.eosscontext.group_id
        user_info.eosscontext.problem_id = user_info_copy.eosscontext.problem_id
        user_info.eosscontext.dataset_id = dataset_id
        user_info.save()

        return user_info

    def set_problem_parameters(self):
        self.orbits = self.vassar_client.get_orbit_list(self.user_info.eosscontext.problem_id)
        self.instruments = self.vassar_client.get_instrument_list_ai4se(self.user_info.eosscontext.problem_id)
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






