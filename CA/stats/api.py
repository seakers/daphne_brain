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

        # --> 2. Get set of potential questions for topic (that have not been seen before)
        questions = self.graphql_client.get_topic_questions(lowest_topic_id)

        # --> 3. Get previous answers for finding question contribution
        previous_answers = self.get_answered_questions(lowest_topic_id)

        # --> 4. Iterate over questions to find the highest contributing one
        contributions = []
        for question in questions:
            contribution = self.calculate_contribution(current_estimate, question, previous_answers)
            contributions.append(contribution)
        question = questions[contributions.index(max(contributions))]

        # --> 5. Correctly format selected question and return
        q_return = {
            'text': str(question['text']),
            'choices': str(question['choices']),
            'topic_ids': json.dumps([int(x['topic_id']) for x in question['topics']]),
            'question_id': question['id']
        }
        print('--> RETURN QUESTION', q_return)
        return q_return




    def calculate_contribution(self, current_estimate, question, previous_answers):

        # --> 1. Get question model
        q_model = IIIPL(
            float(question['discrimination']),
            float(question['difficulty']),
            float(question['guessing'])
        )

        # --> 2. Get estimate if question answered incorrectly
        previous_answers.append((0, q_model))
        incorrect_estimate = MAP_Estimator(previous_answers).estimate().x
        del previous_answers[-1]

        # --> 3. Get estimate if question answered correctly
        previous_answers.append((0, q_model))
        correct_estimate = MAP_Estimator(previous_answers).estimate().x

        # --> 4. Find question contribution
        contribution = float(abs(current_estimate - incorrect_estimate) + abs(current_estimate - correct_estimate))
        print('--> QUESTION CONTRIBUTION:', contribution, question['text'])
        return contribution












