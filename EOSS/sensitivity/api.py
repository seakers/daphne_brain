from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling
from EOSS.sensitivity.sampling.AssigningSampling import AssigningSampling
from statistics import mean
from asgiref.sync import async_to_sync
import itertools
import threading
import json
import time

from SALib.sample import saltelli
from SALib.analyze import sobol

# --> Database
from django.contrib.auth.models import User
from daphne_context.models import UserInformation

from auth_API.helpers import create_user_information
from datetime import datetime



import numpy as np





class SensitivityClient:
    def __init__(self, request_user_info, num_instances=3):
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

        # --> Dir for writing files
        self.data_dir = '/app/daphne/daphne_brain/EOSS/sensitivity/data/'

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

    def purge_eval_queues(self):
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_request_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_request_queue_url)
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_response_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_response_queue_url)

    def subscribe_to_samples(self, samples):
        print('--> SUBSCRIBING TO SAMPLES:', len(samples))
        dataset_id = self.user_info.eosscontext.dataset_id
        sleep_sec = 5
        designs = []
        num_evaluated = 0
        prev_eval_num = 0
        rate_list = []

        while num_evaluated < len(samples):
            time.sleep(sleep_sec)
            aggregate_query = self.db_client.get_architectures_like_aggregate(dataset_id, samples)
            num_evaluated = int(aggregate_query['data']['Architecture_aggregate']['aggregate']['count'])

            eval_rate = (num_evaluated - prev_eval_num) / float(sleep_sec)
            if eval_rate == 0:
                eval_rate = 1
            rate_list.append(eval_rate)
            mean_rate = mean(rate_list)
            estimated_time = ((len(samples) - num_evaluated) / mean_rate) / 60.0
            prev_eval_num = num_evaluated
            print('--> CHECKING FOR COMPLETION:', num_evaluated, '/', len(samples), '| RATE:', round(mean_rate, 3), '(eval/sec)', '| TIME REMAINING:', round(estimated_time, 3), '(min)')

        query = self.db_client.get_architectures_like(dataset_id, samples)
        designs = query['data']['Architecture']

        # Make sure the appropriate number of samples are included
        if len(designs) != len(samples):
            print('--> WRONG NUMBER OF SENSITIVITY DESIGNS:', len(designs), len(samples))
            time.sleep(5)

        print('--> FINISHED EVALUATION')
        return self.parse_architectures(designs)

    def process_complete_results(self, results_dict, problem, orbits, instruments, file_name):
        all_results = {
            'S1': {},
            'ST': {}
        }
        for objective, results in results_dict.items():
            analysis = sobol.analyze(problem, results, calc_second_order=False)
            first_order = analysis['S1']
            total_order = analysis['ST']

            counter = 0
            first_order_dict = {}
            total_order_dict = {}
            for orbit in orbits:
                for instrument in instruments:
                    name = instrument + '@' + orbit
                    first_order_dict[name] = first_order[counter]
                    total_order_dict[name] = total_order[counter]
                    counter += 1
            all_results['S1'][objective] = first_order_dict
            all_results['ST'][objective] = total_order_dict

        # Write results object to file
        full_path = self.data_dir + file_name
        with open(full_path, 'w+') as f:
            f.write(json.dumps(all_results))
            f.close()

        return True


    def process_results(self, results_dict, problem, items, file_name):
        all_results = {
            'S1': {},
            'ST': {}
        }
        for objective, results in results_dict.items():
            analysis = sobol.analyze(problem, results, calc_second_order=False)
            first_order = analysis['S1']
            total_order = analysis['ST']

            # Iterate over first order sensitivities
            first_order_dict = {}
            for idx, sensitivity in enumerate(first_order):
                first_order_dict[items[idx]] = sensitivity
            total_order_dict = {}
            for idx, sensitivity in enumerate(total_order):
                total_order_dict[items[idx]] = sensitivity

            all_results['S1'][objective] = first_order_dict
            all_results['ST'][objective] = total_order_dict

        # Write results object to file
        full_path = self.data_dir + file_name
        with open(full_path, 'w+') as f:
            f.write(json.dumps(all_results))
            f.close()

        return True

    def parse_architectures(self, results):
        cost_list = []
        programmatic_risk_list = []
        fairness_list = []
        data_continuity_list = []
        oceanic_list = []
        atmosphere_list = []
        terrestrial_list = []
        print('\n\n--- PARSING ARCHITECTURES ---')
        for arch in results:

            exp_results = {}
            for exp in arch['ArchitectureScoreExplanations']:
                exp_results[exp['Stakeholder_Needs_Panel']['name']] = float(exp['satisfaction'])
            oceanic_list.append(exp_results.get("Oceanic"))
            atmosphere_list.append(exp_results.get("Atmosphere"))
            terrestrial_list.append(exp_results.get("Terrestrial"))
            cost_list.append(arch['cost'])
            print('--> EVAL NUMBER:', arch['eval_idx'])
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






    def calculate_problem_sensitivities(self, problem_name='ClimateCentric_1'):


        # 1. Set problem parameters
        self.set_problem_parameters()

        # 2. Create sampler for sensitivity evaluation
        sampling = AssigningSampling(self.instruments, self.orbits)

        # 3. Calculate orbit sensitivities
        # self.calculate_orbit_sensitivities(sampling, problem_name)

        # 4. Calculate instrument sensitivities
        self.calculate_instrument_sensitivities(sampling, problem_name)

        # 5. Calculate complete sensitivities
        # self.calculate_complete_sensitivities(sampling, problem_name)

    def calculate_complete_sensitivities(self, sampling, problem_name):
        self.purge_eval_queues()

        # 1. Get samples
        samples = sampling.get_complete_samples()

        # 2. Place all samples in evaluation queue
        samples_requested = self.scale_client.evaluate_batch(samples)

        # 3. Subscribe to architectures
        results_dict = self.subscribe_to_samples(samples_requested)

        # 4. Process results
        ddate = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        file_name = problem_name + '_CompleteSensitivities_' + str(ddate) + '.json'
        self.process_complete_results(results_dict, sampling.complete_problem, self.orbits, self.instruments, file_name)

        return 0


    def calculate_orbit_sensitivities(self, sampling, problem_name):
        self.purge_eval_queues()

        # 1. Get samples
        samples = sampling.get_orbit_samples()

        # 2. Place all samples in evaluation queue
        samples_requested = self.scale_client.evaluate_batch(samples)

        # 3. Subscribe to architectures
        results_dict = self.subscribe_to_samples(samples_requested)

        # 4. Process results
        ddate = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        file_name = problem_name + '_OrbitSensitivities_'+str(ddate)+'.json'
        self.process_results(results_dict, sampling.orbit_problem, self.orbits, file_name)

    def calculate_instrument_sensitivities(self, sampling, problem_name):
        self.purge_eval_queues()

        # 1. Get samples
        samples = sampling.get_instrument_samples()

        # 2. Place all samples in evaluation queue
        samples_requested = self.scale_client.evaluate_batch(samples)

        # 3. Subscribe to architectures
        results_dict = self.subscribe_to_samples(samples_requested)

        # 4. Process results
        ddate = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        file_name = problem_name + '_InstrumentSensitivities_'+ddate+'.json'
        self.process_results(results_dict, sampling.instrument_problem, self.instruments, file_name)








