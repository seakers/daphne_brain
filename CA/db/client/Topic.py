




class Topic:

    def __init__(self, client):
        self.client = client
        self.additional_topics = []


    def index(self):

        # --> 1. Index any additional topics
        for topic in self.additional_topics:
            topic_id = self.client.index_topic(topic)


        # --> 2. Index all topics for all users
        topics = self.client.get_all_topics()
        users = self.client.get_users()
        for topic in topics:
            for user in users:
                self.client.index_ability_parameter(user.id, topic.id, None)

        return 0

