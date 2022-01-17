




class Topic:

    def __init__(self, client):
        self.client = client

        self.topics = [
            'Lifecycle Cost',
            'Cost Estimation Methods',
            'Work Breakdown Structure',
            'Cost Estimating Relationships',
        ]


    def index(self):

        for topic in self.topics:
            # --> 1. Index excel exercise
            topic_id = self.client.index_topic(topic)

            # --> 2. For each user, index ExcelExerciseCompletion for the exercise
            for user in self.client.get_users():
                self.client.index_ability_parameter(user.id, topic_id, None)
        return 0

