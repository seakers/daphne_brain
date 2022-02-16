import json


class Message:

    def __init__(self, client):
        self.client = client

        self.welcome_text = "Welcome to Daphne Academy! I am Daphne, a virtual assistant created to help you along your learning journey."
        self.warning_text = "PSA: I'm currently on leave getting some upgrades, but I'll shoot you a message when I'm back and ready to help."

    def index(self):
        for user in self.client.get_users():
            self.client.index_message(user.id, self.welcome_text, 'Daphne')
            # self.client.index_message(user.id, self.warning_text, 'Daphne')



