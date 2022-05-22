import json

from client.questions.mission_payloads import get_questions as get_mp_questions
from client.questions.spacecraft_bus import get_questions as get_sb_questions
from client.questions.lifecycle_cost import get_questions as get_lc_questions

class Questions:

    def __init__(self, client):
        self.client = client

        self.question_list = []
        self.question_list += get_lc_questions()
        self.question_list += get_sb_questions()

    def index(self):
        for question in self.question_list:
            self.client.index_question(question['text'], json.dumps(question['choices']),
                                       question['difficulty'], question['discrimination'],
                                       question['guessing'], question['topics'], question['explanation'])
        return 0
