import json

from client.modules.basics import basics
from client.modules.bottom_up_ca import bottom_up_ca


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
            'Bottom-up Cost Estimation': {
                'slides': bottom_up_ca,
                'icon': 'mdi-arrow-expand-up',
                'slide_idx': 0,
                'topics': ['Work Breakdown Structures', 'Bottom-up Cost Estimation']
            },
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
