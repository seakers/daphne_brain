import json


from client.modules.bottom_up_ca import slides as bottom_up_ca
from client.modules.parametric_ca import slides as parametric_ca
from client.modules.cost_over_time import slides as cost_over_time
from client.modules.eoc_learning_curve import slides as eoc_learning_curve
from client.modules.software_cost_estimation import slides as software_cost_estimation
from client.modules.space_system_cost_drivers import slides as space_system_cost_drivers


from client.modules.basics import get_module as get_basic_module
from client.modules.remote_sensing import get_module as get_rms_module
from client.modules.spacecraft_bus import get_module as get_sb_module
from client.modules.bottom_up_ca import get_module as get_buca_module
from client.modules.eoc_learning_curve import get_module as get_eocl_module
from client.modules.parametric_ca import get_module as get_pca_module



class LearningModule:

    def __init__(self, client):
        self.client = client

        self.modules = {
            'Basics': get_basic_module(),
            'Spacecraft Bus': get_sb_module(),
            'Mission Payloads': get_rms_module(),
            # 'Bottom Up Estimation': get_buca_module(),
            # 'Economies of Scale': get_eocl_module(),
            'Parametric Estimation': get_pca_module()
        }


    def index_info_slide(self, slide, module_id):

        # --> 1. Get user ids
        users = self.client.get_users()
        user_ids = [None]
        for user in users:
            user_ids.append(user.id)

        # --> 2. Index slide for each user
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

    def index_quiz_start_slide(self, slide, module_id):

        # --> 1. Get user ids
        users = self.client.get_users()
        user_ids = [None]
        for user in users:
            user_ids.append(user.id)

        # --> 2. Index slide for each user
        for user_id in user_ids:
            self.client.index_quiz_start_slide(module_id, slide['type'], user_id, slide['idx'])
        return 0

    def index_quiz_end_slide(self, slide, module_id):

        # --> 1. Get user ids
        users = self.client.get_users()
        user_ids = [None]
        for user in users:
            user_ids.append(user.id)

        # --> 2. Index slide for each user
        for user_id in user_ids:
            self.client.index_quiz_start_slide(module_id, slide['type'], user_id, slide['idx'])
        return 0

    def index(self):

        for module, info in self.modules.items():
            slides = info['slides']
            icon = info['icon']
            slide_idx = info['slide_idx']
            topics = info['topics']
            course = info['course']
            status = info['status']
            # --> 1. Index learning module
            module_id = self.client.index_learning_module(module, icon, topics, course, status)

            # --> 2. Index Join__User_LearningModule for all users
            for user in self.client.get_users():
                self.client.index_join_user_learning_module(user.id, module_id, slide_idx)

            # --> 3. Index Learning Module Slides
            for slide in slides:
                if slide['type'] == 'info':
                    self.index_info_slide(slide, module_id)
                elif slide['type'] == 'question':
                    self.index_question_slide(slide, module_id)
                elif slide['type'] == 'quiz_start':
                    self.index_quiz_start_slide(slide, module_id)
                elif slide['type'] == 'quiz_end':
                    self.index_quiz_end_slide(slide, module_id)
