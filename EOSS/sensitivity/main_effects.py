import os

from django.contrib.auth.models import User
from daphne_context.models import UserInformation

from asgiref.sync import async_to_sync
from EOSS.sensitivity.sampling.RealTimeSampling import RealTimeSampling
from EOSS.graphql.api import GraphqlClient
from EOSS.vassar.api import VASSARClient
from EOSS.vassar.scaling import EvaluationScaling

from auth_API.helpers import create_user_information

from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture, \
    ContinuousInputArchitecture, AssigningProblemEntities

from EOSS.data_mining.api import DataMiningClient
from EOSS.sensitivity.helpers import feature_expression_to_string





class MainEffectClient:
    def __init__(self, request_user_info, session, current_objectives, num_instances=3):
        self.session = session
        self.current_objectives = current_objectives

        # --> Create main effect user
        self.user_id = None
        self.user_info = self.create_main_effect_user(request_user_info)

        # --> Clients
        self.db_client = GraphqlClient(user_info=self.user_info)
        self.vassar_client = VASSARClient(user_information=self.user_info)
        self.vassar_client.uninitizlize_vassar()
        self.num_instances = num_instances
        self.scale_client = EvaluationScaling(self.user_info, self.num_instances, prod=False)
        self.scale_client.initialize_experiment()

        # --> Problem Variables
        self.orbits = None
        self.instruments = None
        self.set_problem_parameters()

        # --> Datamining Client
        self.data_mining_client = DataMiningClient()
        self.initialize_datamining_client()


    def shutdown(self):
        self.purge_experiment_queues()
        self.scale_client.shutdown()

    def set_problem_parameters(self):
        self.orbits = self.vassar_client.get_orbit_list(self.user_info.eosscontext.problem_id)
        self.instruments = self.vassar_client.get_instrument_list_ai4se(self.user_info.eosscontext.problem_id)

    def initialize_datamining_client(self):

        # --> 1. Set Datamining Problem Parameters
        self.data_mining_client.startConnection()
        entities = AssigningProblemEntities(self.instruments, self.orbits)
        self.data_mining_client.client.setAssigningProblemEntities(self.session.session_key, self.user_info.eosscontext.problem_id, entities)
        self.data_mining_client.endConnection()

        return 0

    def create_main_effect_user(self, user_info_copy):
        temp_db_client = GraphqlClient(user_info=user_info_copy)

        username = 'maineffect_user'
        email = 'maineffect@gmail.com'
        password = 'maineffect'

        # --> Get or create User
        user = None
        if User.objects.filter(username=username).exists():
            print('--> MAIN EFFECT USER ALREADY EXISTS')
            user_query = User.objects.filter(username__exact=username)
            user = user_query[0]
            self.user_id = user.id
        else:
            print('--> CREATING NEW MAIN EFFECT USER')
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

        # --> Create new dataset for main effect analysis
        result = temp_db_client.new_dataset(user.id, user_info_copy.eosscontext.problem_id, "main_effect")
        dataset_id = result['data']['insert_Dataset_one']['id']

        # --> Copy user information parameters
        user_info.eosscontext.group_id = user_info_copy.eosscontext.group_id
        user_info.eosscontext.problem_id = user_info_copy.eosscontext.problem_id
        user_info.eosscontext.dataset_id = dataset_id
        user_info.eosscontext.save()
        user_info.save()

        return user_info

    def purge_experiment_queues(self):
        self.purge_vassar_request_queues()
        self.purge_eval_request_queue()

    def purge_eval_request_queue(self):
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_request_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_request_queue_url)
        if async_to_sync(self.vassar_client.queue_exists)(self.user_info.eosscontext.vassar_response_queue_url):
            self.vassar_client.purge_queue(self.user_info.eosscontext.vassar_response_queue_url)

    def purge_vassar_request_queues(self):
        if async_to_sync(self.vassar_client.queue_exists)(os.environ["VASSAR_REQUEST_URL_2"]):
            self.vassar_client.purge_queue(os.environ["VASSAR_REQUEST_URL_2"])
        if async_to_sync(self.vassar_client.queue_exists)(os.environ["VASSAR_RESPONSE_URL_2"]):
            self.vassar_client.purge_queue(os.environ["VASSAR_RESPONSE_URL_2"])

    def new_dataset(self):
        result = self.db_client.new_dataset(self.user_id, self.user_info.eosscontext.problem_id, "main_effect")
        dataset_id = result['data']['insert_Dataset_one']['id']
        self.user_info.eosscontext.dataset_id = dataset_id
        self.user_info.eosscontext.save()

    def get_current_dataset_designs(self):
        dataset_id = self.user_info.eosscontext.dataset_id
        query = self.db_client.get_architectures_all(dataset_id)
        designs = query['data']['Architecture']
        fixed_designs = []
        for design in designs:
            fixed_designs.append(
                {
                    'input': design['input'],
                    'cost': design['cost'],
                    'programmatic_risk': design['programmatic_risk'],
                    'fairness': design['fairness'],
                    'data_continuity': design['data_continuity'],
                    'id': design['id'],
                    design['ArchitectureScoreExplanations'][0]['Stakeholder_Needs_Panel']['name']:
                        design['ArchitectureScoreExplanations'][0]['satisfaction'],
                    design['ArchitectureScoreExplanations'][1]['Stakeholder_Needs_Panel']['name']:
                        design['ArchitectureScoreExplanations'][1]['satisfaction'],
                    design['ArchitectureScoreExplanations'][2]['Stakeholder_Needs_Panel']['name']:
                        design['ArchitectureScoreExplanations'][2]['satisfaction'],
                }
            )
        return fixed_designs


    def clean_features(self, features):
        cleaned_features = []

        for feature in features:
            for feat_dict in feature:
                if 'orbitAbsent' in feat_dict or 'instrumentAbsent' in feat_dict:
                    cleaned_features.append(feature)
                    break

        if len(cleaned_features) == 0:
            return None
        return cleaned_features

    def handle_objective_weight_change(self):
        return 0

    def change_feedback_objectives(self, new_objectives):
        self.current_objectives = new_objectives
        return 0

    def start_main_effect_evaluations(self):
        self.set_problem_parameters()
        self.purge_experiment_queues()
        sampling = RealTimeSampling(self.instruments, self.orbits, size=500)
        samples = sampling.get_samples()
        self.scale_client.evaluate_batch_fast(samples)
        return 0

    def formulation_change(self, change_msg):

        # ----- Different formulation changes require different actions
        # 1. User changes problem orbits / instruments
        if change_msg['instChange'] or change_msg['orbChange']:
            # -- Set new problem parameters
            self.set_problem_parameters()
            # -- Clear main effect evaluation queue
            self.purge_experiment_queues()
            # -- Use container specific private queue to tell each container to rebuild
            self.scale_client.rebuild_experiment_containers()
            # -- Create new dataset for new problem formulation
            self.new_dataset()
            # -- Set new problem parameters for datamining
            self.initialize_datamining_client()
            # -- Start new evaluation process for new formulation
            self.start_main_effect_evaluations()

        # 2. User changes objectives
        if change_msg['objChange']:
            # -- Set feedback to only consider the new objectives
            self.change_feedback_objectives(change_msg['objList'])

        # 3. User changes objective weights
        if change_msg['stakeChange']:
            self.handle_objective_weight_change()

        return 0

    def get_current_main_effect_data(self):
        sampling = RealTimeSampling(self.instruments, self.orbits)
        designs = self.get_current_dataset_designs()
        main_effects = sampling.calc_main_effects(designs)
        return main_effects


    def get_current_driving_features(self):
        # objectives = ['cost', 'data_continuity', 'programmatic_risk', 'fairness', 'Oceanic', 'Atmosphere', 'Terrestrial']

        # --> 1. Create utopia point based on current objectives
        utopia_point = []
        for objective in self.current_objectives:
            if objective in ['cost', 'programmatic_risk', 'fairness']:
                utopia_point.append(0)
            elif objective in ['Oceanic', 'Atmosphere', 'Terrestrial']:
                utopia_point.append(1)
            elif objective in ['data_continuity']:
                utopia_point.append(10000)

        # --> 2. Get current evaluated designs
        designs = self.get_current_dataset_designs()
        if len(designs) < 10:
            return None

        # --> 3. Partition designs based on pareto ranking
        behavioral = []
        non_behavioral = []
        temp = []
        for design in designs:
            id = design['id']
            dist = 0
            for idx, objective in enumerate(self.current_objectives):
                dist += ((design[objective] - utopia_point[idx]) ** 2)
            temp.append((id, dist))

        temp = sorted(temp, key=lambda x: x[1])
        for i in range(len(temp)):
            if i <= len(temp) // 15:  # Label the top 10% architectures as behavioral
                behavioral.append(temp[i][0])
            else:
                non_behavioral.append(temp[i][0])

        # --> 4. Generate features
        self.data_mining_client.startConnection()
        _designs = []
        for design in designs:
            outputs = []
            for objective in self.current_objectives:
                outputs.append(design[objective])
            _designs.append(BinaryInputArchitecture(design["id"], design["input"], outputs))
        _features = self.data_mining_client.client.getDrivingFeaturesEpsilonMOEABinary(self.session.session_key,
                                                                                       self.user_info.eosscontext.problem_id,
                                                                                       "assignation",
                                                                                       behavioral,
                                                                                       non_behavioral,
                                                                                       _designs)
        self.data_mining_client.endConnection()

        # --> 5. Extract features
        features = []
        for df in _features:
            features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})

        converted_features = []
        for feature in features:
            converted_features.append(feature_expression_to_string(feature['name'], self.orbits, self.instruments))

        return converted_features















