from CA.stats.models.IIIPL import IIIPL
from CA.stats.estimators.MLE_Estimator import MLE_Estimator
from CA.stats.estimators.MAP_Estimator import MAP_Estimator



from EOSS.graphql.api import GraphqlClient



class StatsClient:

    def __init__(self, user_info):
        self.user_info = user_info
        self.user_id = user_info.user.id
        self.graphql_client = GraphqlClient()


    def update_model(self, topic_id):
        print('--> UPDATING TOPIC:', topic_id)
        answers = []


        # --> 1. Gather all graded slide questions on this topic
        slide_questions = self.graphql_client.get_ca_graded_slide_questions(self.user_id, topic_id)
        for question in slide_questions:
            correct = 0
            if question['slides'][0]['correct'] == True:
                correct = 1

            q_model = IIIPL(
                float(question['discrimination']),
                float(question['difficulty']),
                float(question['guessing'])
            )
            answers.append((correct, q_model))


        # --> 2. Gather all graded test questions on this topic
        test_questions = self.graphql_client.get_ca_graded_test_questions(self.user_id, topic_id)


        # --> 3. Print aggregated answers
        for x in answers:
            print(x)

        # --> 4. Use model to find new ability parameter estimate
        map_estimate = MAP_Estimator(answers).estimate().x
        print('--> MAP ESTIMATE:', map_estimate)

        # --> 5. Update user database
        result = self.graphql_client.set_user_ability_parameters(self.user_id, topic_id, map_estimate)
