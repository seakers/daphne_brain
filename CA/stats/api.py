import json

from operator import itemgetter

from CA.stats.models.IIIPL import IIIPL
from CA.stats.estimators.MLE_Estimator import MLE_Estimator
from CA.stats.estimators.MAP_Estimator import MAP_Estimator



from EOSS.graphql.api import GraphqlClient

ex_question = {
    'text': 'No baselined topic was found, could not generate a question',
    'choices': json.dumps([
        {'text': 'Choice 1', 'correct': True},
        {'text': 'Choice 2', 'correct': False},
        {'text': 'Choice 3', 'correct': False},
        {'text': 'Choice 4', 'correct': False}
    ]),
    'topic_ids': json.dumps([1])
}

class StatsClient:

    def __init__(self, user_info):
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.graphql_client = GraphqlClient()




    def get_answered_questions(self, topic_id):
        answers = []

        # --> 1. Get all slide questions
        slide_questions = self.graphql_client.get_ca_graded_slide_questions(self.user_id, topic_id)
        for question in slide_questions:
            q_model = IIIPL(
                float(question['discrimination']),
                float(question['difficulty']),
                float(question['guessing'])
            )
            correct = 0
            if question['slides'][0]['correct'] == True:
                correct = 1

            answers.append((correct, q_model))

        # --> 2. Get all questions from previous exams
        exam_questions = self.graphql_client.get_ca_graded_test_questions(self.user_id, topic_id)
        for question in exam_questions:
            q_model = IIIPL(
                float(question['discrimination']),
                float(question['difficulty']),
                float(question['guessing'])
            )
            for occurance in question['test']:
                correct = 0
                if occurance['correct'] == True:
                    correct = 1
                answers.append((correct, q_model))
                
        return answers




    def update_model(self, topic_id):
        print('--> UPDATING TOPIC:', topic_id)

        # --> 1. Get all previously answered graded questions
        answers = self.get_answered_questions(topic_id)

        # --> 2. Print aggregated answers
        for x in answers:
            print(x)

        # --> 3. Use model to find new ability parameter estimate
        map_estimate = MAP_Estimator(answers).estimate().x
        print('--> MAP ESTIMATE:', map_estimate)

        # --> 4. Update user database
        result = self.graphql_client.set_user_ability_parameters(self.user_id, topic_id, map_estimate)



    def select_question(self):

        # --> 1. Determine lowest user topic ability parameter
        sorter_parameters = self.graphql_client.get_user_ability_parameters(self.user_id)
        if len(sorter_parameters) == 0:
            return ex_question
        lowest_topic_id = sorter_parameters[0]['Topic']['id']
        current_estimate = sorter_parameters[0]['value']
        print('--> Theta:', current_estimate)

        # --> 2. Get set of potential questions for topic (that have not been seen before)
        all_questions = self.graphql_client.get_topic_questions(lowest_topic_id)

        # --> 3. Get ids of questions that have already been asked
        repeat_ids = []
        exam_list = self.graphql_client.get_previously_asked_test_questions(self.user_id)
        if len(exam_list) > 0:
            already_asked = exam_list[0]
            for q in already_asked['questions']:
                repeat_ids.append(int(q['question_id']))
        slide_list = self.graphql_client.get_previously_asked_module_questions(self.user_id, lowest_topic_id)
        for slide in slide_list:
            question_id = int(slide['question']['id'])
            if question_id not in repeat_ids:
                repeat_ids.append(question_id)

        # --> 4. Remove repeat questions
        questions = []
        for question in all_questions:
            if int(question['id']) not in repeat_ids:
                questions.append(question)
        print('--> NUM QUESTIONS valid/total:', str(len(questions)) + '/' + str(len(all_questions)))

        if len(questions) == 0:
            questions = all_questions

        # --> 5. Get previous answers for finding question contribution
        previous_answers = self.get_answered_questions(lowest_topic_id)
        # for answer in previous_answers:
        #     print('--> ANSWER:', answer)

        # --> 6. Iterate over questions to find the highest contributing one
        contributions = []
        difficulties = []
        for question in questions:
            contribution = self.calculate_contribution(current_estimate, question, previous_answers)
            ideal_theta = self.calculate_ideal_theta(current_estimate, question)
            difficulties.append(float(question['difficulty']))
            contributions.append(contribution)
            print('--> ID:', question['id'], current_estimate, ideal_theta, contribution)

        question = questions[contributions.index(max(contributions))]
        question_close = questions[self.find_closest_difficulty_idx(current_estimate, difficulties)]

        # --> 7. Correctly format selected question and return
        q_return = {
            'text': str(question_close['text']),
            'choices': str(question_close['choices']),
            'topic_ids': json.dumps([int(x['topic_id']) for x in question_close['topics']]),
            'question_id': question_close['id']
        }
        return q_return


    def find_closest_difficulty_idx(self, current_estimation, difficulties):
        closest_idx = 0
        min_distance = 100
        for idx, difficulty in enumerate(difficulties):
            q_distance = abs(current_estimation - difficulty)
            if q_distance < min_distance:
                min_distance = q_distance
                closest_idx = idx
        return closest_idx


    def calculate_contribution(self, current_estimate, question, previous_answers):

        # --> 1. Get question model
        q_model = IIIPL(
            float(question['discrimination']),
            float(question['difficulty']),
            float(question['guessing'])
        )

        # --> 2. Get estimate if question answered incorrectly
        previous_answers.append((0, q_model))
        incorrect_prob = q_model.prob_incorrect(current_estimate)
        incorrect_estimate = MAP_Estimator(previous_answers).estimate().x
        # incorrect_delta = abs(current_estimate - incorrect_estimate)
        incorrect_delta = incorrect_estimate - current_estimate
        incorrect_contribution = incorrect_delta * incorrect_prob
        del previous_answers[-1]

        # --> 3. Get estimate if question answered correctly
        previous_answers.append((1, q_model))
        correct_prob = q_model.prob_correct(current_estimate)
        correct_estimate = MAP_Estimator(previous_answers).estimate().x
        # correct_delta = abs(current_estimate - correct_estimate)
        correct_delta = correct_estimate - current_estimate
        correct_contribution = correct_delta * correct_prob
        del previous_answers[-1]

        # --> 4. Find question contribution
        contribution = float(incorrect_contribution + correct_contribution)

        sub_text = question['text']
        if len(sub_text) > 30:
            sub_text = sub_text[0:30]
        print('--> Question:', round(contribution, 4), '-->', sub_text)
        return contribution


    def calculate_ideal_theta(self, current_estimate, question):
        a = float(question['discrimination'])
        b = float(question['difficulty'])
        c = float(question['guessing'])

        print('--> QUESTION PARAMETERS:', a, b, c)


        # --> 1. Get question model
        q_model = IIIPL(a, b, c)

        # --> 2. Get probability user get question correct / incorrect
        correct_prob = q_model.prob_correct(current_estimate)
        incorrect_prob = q_model.prob_incorrect(current_estimate)

        # --> 3. Calculate ideal theta for question
        lhs = (a * a) * (incorrect_prob / correct_prob)
        rhs = ((correct_prob - c) * (correct_prob - c)) / ((1 - c) * (1 - c))
        ideal_theta = lhs * rhs

        return ideal_theta









