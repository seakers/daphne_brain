from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling
from asgiref.sync import async_to_sync
import itertools
import threading
import json

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
        self.result_obj = {}
        self.orbits = None
        self.instruments = None
        self.architectures = None
        self.set_problem_parameters()

        # --> Evaluations
        self.orb_problem = None
        self.inst_problem = None
        self.requested_orb_evals = None
        self.requested_inst_evals = None

        self.climate_problem_1 = '/app/daphne/daphne_brain/EOSS/sensitivity/ClimateCentricSensitivity_1.json'
        self.climate_problem_2 = '/app/daphne/daphne_brain/EOSS/sensitivity/ClimateCentricSensitivity_2.json'

        self.orb_written = False
        self.inst_written = False

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
        user_info.eosscontext.save()
        user_info.save()

        return user_info

    def new_dataset(self):
        result = self.db_client.new_dataset(self.user_id, self.user_info.eosscontext.problem_id, "sensitivity")
        dataset_id = result['data']['insert_Dataset_one']['id']
        self.user_info.eosscontext.dataset_id = dataset_id
        self.user_info.eosscontext.save()

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
        print('--> saltelli samples', analysis_type, len(rounded))
        return rounded, problem

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
                group_name = self.instruments[y]
                var_group.append(group_name)
                var_names.append('x' + str(counter))
                var_bounds.append([0, 1])
                counter += 1
        problem = {
            'groups': var_group,
            'num_vars': num_inputs,
            'names': var_names,
            'bounds': var_bounds
        }
        print('--> CREATED PROBLEM: ', problem)
        return problem

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
            group_name = self.orbits[x]
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

    def parse_architectures(self, results):
        cost_list = []
        programmatic_risk_list = []
        fairness_list = []
        data_continuity_list = []
        oceanic_list = []
        atmosphere_list = []
        terrestrial_list = []
        for arch in results:
            exp_results = {}
            for exp in arch['ArchitectureScoreExplanations']:
                exp_results[exp['Stakeholder_Needs_Panel']['name']] = float(exp['satisfaction'])
            oceanic_list.append(exp_results.get("Oceanic"))
            atmosphere_list.append(exp_results.get("Atmosphere"))
            terrestrial_list.append(exp_results.get("Terrestrial"))
            cost_list.append(arch['cost'])
            programmatic_risk_list.append(arch['programmatic_risk'])
            fairness_list.append(arch['fairness'])
            data_continuity_list.append(arch['data_continuity'])
        return {
            'cost': np.array(cost_list),
            'programmatic_risk': np.array(programmatic_risk_list),
            'fairness': np.array(fairness_list),
            'data_continuity': np.array(data_continuity_list),
            'Oceanic': np.array(oceanic_list),
            'Atmosphere': np.array(atmosphere_list),
            'Terrestrial': np.array(terrestrial_list)
        }

    def process_sobol_results(self, results, key, req_type='instruments'):
        objs = None
        if req_type == 'instruments':
            objs = self.instruments
        else:
            objs = self.orbits
        first_order = results['S1']
        total_order = results['ST']

        if key not in self.result_obj:
            self.result_obj[key] = {}
        if req_type not in self.result_obj[key]:
            self.result_obj[key][req_type] = {}

        for idx, sen in enumerate(first_order):
            first_order_sen = sen
            total_order_sen = total_order[idx]
            obj = objs[idx]
            obj_dict = {
                'S1': first_order_sen,
                'ST': total_order_sen
            }
            self.result_obj[key][req_type][obj] = obj_dict
        return results




    def apply_sobol(self, problem, obj_dict, req_type='instruments'):
        results = {
            'cost': self.process_sobol_results(sobol.analyze(problem, obj_dict['cost'], calc_second_order=False), 'cost', req_type=req_type),
            'programmatic_risk': self.process_sobol_results(sobol.analyze(problem, obj_dict['programmatic_risk'], calc_second_order=False), 'programmatic_risk', req_type=req_type),
            'fairness': self.process_sobol_results(sobol.analyze(problem, obj_dict['fairness'], calc_second_order=False), 'fairness', req_type=req_type),
            'data_continuity': self.process_sobol_results(sobol.analyze(problem, obj_dict['data_continuity'], calc_second_order=False), 'data_continuity', req_type=req_type),
            'Oceanic': self.process_sobol_results(sobol.analyze(problem, obj_dict['Oceanic'], calc_second_order=False), 'Oceanic', req_type=req_type),
            'Atmosphere': self.process_sobol_results(sobol.analyze(problem, obj_dict['Atmosphere'], calc_second_order=False), 'Atmosphere', req_type=req_type),
            'Terrestrial': self.process_sobol_results(sobol.analyze(problem, obj_dict['Terrestrial'], calc_second_order=False), 'Terrestrial', req_type=req_type),
        }
        return results


    def write_file(self):
        with open(self.climate_problem_1, 'w') as f:
            f.write(json.dumps(self.result_obj))
            f.close()
        self.result_obj = {}






    def get_orbit_sensitivities(self):
        if self.orb_written:
            return self.orb_written

        query_results = self.db_client.get_architectures_like(self.user_info.eosscontext.dataset_id, self.requested_orb_evals)
        results = query_results['data']['Architecture']
        print('--> NUM SENSITIVITY ORBS EVALUATED SO FAR', len(results))
        if len(results) < len(self.requested_orb_evals):
            return False
        obj_dict = self.parse_architectures(results)
        sensitivities = self.apply_sobol(self.orb_problem, obj_dict, req_type='orbits')
        self.orb_written = True
        print('--> ORBIT SENSITIVITIES', sensitivities)
        return True

    def get_instrument_sensitivities(self):
        if self.inst_written:
            return self.inst_written

        query_results = self.db_client.get_architectures_like(self.user_info.eosscontext.dataset_id, self.requested_inst_evals)
        results = query_results['data']['Architecture']
        print('--> NUM SENSITIVITY INSTS EVALUATED SO FAR', len(results))
        if len(results) < len(self.requested_inst_evals):
            return False
        obj_dict = self.parse_architectures(results)
        sensitivities = self.apply_sobol(self.inst_problem, obj_dict, req_type='instruments')
        self.inst_written = True
        print('--> INSTRUMENT SENSITIVITIES', sensitivities)
        return True


    def start_formulation_calcs(self, new_dataset=False):
        print('--> CALCULATING SENSITIVITIES')

        # 1. Reload problem parameters in case of problem formulation change, clear eval queues
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_request_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_request_queue_url)
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_response_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_response_queue_url)
        self.set_problem_parameters()
        print('--> SET PROBLEM PARAMETERS')

        # 2. Create new dataset to store evaluations
        if new_dataset:
            self.new_dataset()
        print('--> CREATED NEW DATASET')

        # 2. Generate design samples for sensitivity calculations (2d np-array)
        orb_batch, self.orb_problem = self.get_samples(analysis_type='orbit')
        inst_batch, self.inst_problem = self.get_samples(analysis_type='instrument')
        print('--> NEW SAMPLES GENERATED')

        # 3. Create evaluation requests and send to the eval queue
        self.requested_orb_evals = self.scale_client.evaluate_batch(orb_batch)
        self.requested_inst_evals  = self.scale_client.evaluate_batch(inst_batch)

        return True







