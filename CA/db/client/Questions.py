import json



class Questions:

    def __init__(self, client):
        self.client = client

        self.question_list = [
            {
                'topics': ['Lifecycle Cost'],
                'text': 'The cost of a satellite\'s propulsion system is driven in part by propulsion system type',
                'choices': [
                    {'text': 'A. True', 'correct': True, 'id': 0},
                    {'text': 'B. False', 'correct': False, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.5,
                'discrimination': 5,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Which of the following is considered a main phase of Lifecycle Cost Estimation?',
                'choices': [
                    {'text': 'A. Research, Development, Test, and Evaluation Phase', 'correct': False, 'id': 0},
                    {'text': 'B. Production Phase', 'correct': False, 'id': 1},
                    {'text': 'C. Operations and Maintenance Phase', 'correct': False, 'id': 2},
                    {'text': 'D. All of the above', 'correct': True, 'id': 3}
                ],
                'explanation': '',
                'difficulty': 0.5,
                'discrimination': 5,
                'guessing': 0.25
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Satellite theoretical first unit (TFU) cost is estimated during the Operations and Maintenance phase.',
                'choices': [
                    {'text': 'A. True', 'correct': False, 'id': 0},
                    {'text': 'B. False', 'correct': True, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.5,
                'discrimination': 5,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'The operational and maintenance phase of a mission is typically more expensive for constellations and reusable systems.',
                'choices': [
                    {'text': 'A. True', 'correct': True, 'id': 0},
                    {'text': 'B. False', 'correct': False, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.5,
                'discrimination': 5,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'During the production phase, the cost of producing multiple similar units is estimated using a',
                'choices': [
                    {'text': 'A. Deterministic Model', 'correct': False, 'id': 0},
                    {'text': 'B. Learning Curve', 'correct': True, 'id': 1},
                    {'text': 'C. Design Structure Matrix', 'correct': False, 'id': 2},
                    {'text': 'C. Genetic Algorithm', 'correct': False, 'id': 3}
                ],
                'explanation': '',
                'difficulty': 0.5,
                'discrimination': 5,
                'guessing': 0.25
            },
        ]




    def index(self):
        for question in self.question_list:
            self.client.index_question(question['text'], json.dumps(question['choices']),
                                       question['difficulty'], question['discrimination'],
                                       question['guessing'], question['topics'], question['explanation'])
        return 0
