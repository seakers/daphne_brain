import json

from client.modules.basics import slides as basics
from client.modules.bottom_up_ca import slides as bottom_up_ca
from client.modules.parametric_ca import slides as parametric_ca
from client.modules.cost_over_time import slides as cost_over_time
from client.modules.eoc_learning_curve import slides as eoc_learning_curve
from client.modules.software_cost_estimation import slides as software_cost_estimation
from client.modules.space_system_cost_drivers import slides as space_system_cost_drivers


class LearningModule:

    def __init__(self, client):
        self.client = client

        self.modules = {
            'Basics': {
                'slides': basics,
                'icon': 'mdi-alphabetical',
                'slide_idx': 0,
                'topics': ['Lifecycle Cost', 'Cost Estimation Methods']
            },
            # 'Bottom-up Cost Estimation': {
            #     'slides': bottom_up_ca,
            #     'icon': 'mdi-tray-arrow-up',
            #     'slide_idx': 0,
            #     'topics': ['Work Breakdown Structures', 'Bottom-up Cost Estimation']
            # },
            # 'Parametric Cost Estimation': {
            #     'slides': parametric_ca,
            #     'icon': 'mdi-function-variant',
            #     'slide_idx': 0,
            #     'topics': ['Cost Estimating Relationships']
            # },
            # 'Cost Over Time': {
            #     'slides': cost_over_time,
            #     'icon': 'mdi-clipboard-text-clock-outline',
            #     'slide_idx': 0,
            #     'topics': ['Cash Flows', 'Net Present Value', 'Discount Rate', 'Inflation']
            # },
            # 'Economies of Scale': {
            #     'slides': eoc_learning_curve,
            #     'icon': 'mdi-scale-unbalanced',
            #     'slide_idx': 0,
            #     'topics': ['Learning Curve']
            # },
            # 'Software Cost Estimation': {
            #     'slides': software_cost_estimation,
            #     'icon': 'mdi-desktop-classic',
            #     'slide_idx': 0,
            #     'topics': ['COCOMO']
            # },
            'Space System Cost Drivers': {
                'slides': space_system_cost_drivers,
                'icon': 'mdi-satellite-variant',
                'slide_idx': 0,
                'topics': ['Orbits', 'Spacecraft', 'Payloads']
            }
        }

    def index_info_slide(self, slide, module_id):

        # --> 1. Index slide for each user
        users = self.client.get_users()
        user_ids = [None]
        for user in users:
            user_ids.append(user.id)
        for user_id in user_ids:
            self.client.index_info_slide(module_id, slide['type'], slide['src'], user_id, slide['idx'])

    def index_question_slide(self, slide, module_id):

        # --> 1. Index question and get question_id
        question = slide['question']
        question_id = self.client.index_question(question['text'], json.dumps(question['choices']),
                                                 question['difficulty'], question['discrimination'],
                                                 question['guessing'], question['topics'], question['explanation'])

        # --> 2. Index slide for each user
        users = self.client.get_users()
        user_ids = [None]
        for user in users:
            user_ids.append(user.id)
        for user_id in user_ids:
            # (self, module_id, type, question_id, answered, correct, choice_id, user_id, idx)
            self.client.index_question_slide(module_id, slide['type'], question_id, slide['answered'], slide['correct'],
                                             slide['choice_id'], user_id, slide['idx'])

    def index(self):

        for module, info in self.modules.items():
            slides = info['slides']
            icon = info['icon']
            slide_idx = info['slide_idx']
            topics = info['topics']
            # --> 1. Index learning module
            module_id = self.client.index_learning_module(module, icon, topics)

            # --> 2. Index Join__User_LearningModule for all users
            for user in self.client.get_users():
                self.client.index_join_user_learning_module(user.id, module_id, slide_idx)

            # --> 3. Index Learning Module Slides
            for slide in slides:
                if slide['type'] == 'info':
                    self.index_info_slide(slide, module_id)
                else:
                    self.index_question_slide(slide, module_id)
