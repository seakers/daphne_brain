import json

from client.questions.mission_payloads import get_questions as get_mp_questions
from client.questions.spacecraft_bus import get_questions as get_sb_questions
from client.questions.lifecycle_cost import get_questions as get_lc_questions

class Questions:

    def __init__(self, client):
        self.client = client

        self.question_list = []
        self.question_list += self.lifecycle_cost_questions()
        self.question_list += get_sb_questions()

    def lifecycle_cost_questions(self):
        return [
            {
                'topics': ['Lifecycle Cost'],
                'text': 'The cost of a satellite\'s propulsion system is driven in part by propulsion system type',
                'choices': [
                    {'text': 'A. True', 'correct': True, 'id': 0},
                    {'text': 'B. False', 'correct': False, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.6,
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
                'difficulty': 0.4,
                'discrimination': 6,
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
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Which of the following best describes a Work Breakdown Structure (WBS)?',
                'choices': [
                    {'text': 'A. An organizational table used to categorize and normalize costs', 'correct': True, 'id': 0},
                    {'text': 'B. A document for delegating work to contractors', 'correct': False, 'id': 1},
                    {'text': 'C. A method for scheduling project tasks', 'correct': False, 'id': 2},
                    {'text': 'D. None of the above', 'correct': False, 'id': 3}
                ],
                'explanation': '',
                'difficulty': 0.4,
                'discrimination': 7,
                'guessing': 0.25
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Which of the following is NOT considered a main lifecycle cost phase?',
                'choices': [
                    {'text': 'A. Development, Test, and Evaluation (RDT&E)', 'correct': False, 'id': 0},
                    {'text': 'B. Production', 'correct': False, 'id': 1},
                    {'text': 'C. Pre-phase A', 'correct': True, 'id': 2},
                    {'text': 'D. Operations and Maintenance (O&M)', 'correct': False, 'id': 3}
                ],
                'explanation': '',
                'difficulty': 0.45,
                'discrimination': 5,
                'guessing': 0.25
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Lifecycle Cost\'s Research, Development, Test, and Evaluation phase (RDT&E) includes design, analysis, and testing of breadboards, brassboards, prototypes, and qualification units',
                'choices': [
                    {'text': 'A. True', 'correct': True, 'id': 0},
                    {'text': 'B. False', 'correct': False, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.6,
                'discrimination': 6,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'The Production phase of lifecycle cost incorporates the cost of producing flight units. However, it doesn\'t incorporate their launch costs.',
                'choices': [
                    {'text': 'A. True', 'correct': False, 'id': 0},
                    {'text': 'B. False', 'correct': True, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.75,
                'discrimination': 7,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Replacement satellites and launches after the space system final operating capability has been established are not considered production units.',
                'choices': [
                    {'text': 'A. True', 'correct': True, 'id': 0},
                    {'text': 'B. False', 'correct': False, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.55,
                'discrimination': 5,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'The operations and maintenance phase consists of ongoing operations and maintenance costs, excluding software maintenance.',
                'choices': [
                    {'text': 'A. True', 'correct': False, 'id': 0},
                    {'text': 'B. False', 'correct': True, 'id': 1}
                ],
                'explanation': '',
                'difficulty': 0.6,
                'discrimination': 8,
                'guessing': 0.5
            },
            {
                'topics': ['Lifecycle Cost'],
                'text': 'Which of the following best describes the Theoretical First Unit (TFU) for a space mission?',
                'choices': [
                    {'text': 'A. A theory early satellite design', 'correct': False, 'id': 0},
                    {'text': 'B. A unit of data used to define initial downlink speed', 'correct': False, 'id': 1},
                    {'text': 'C. The very first satellite design iteration', 'correct': False, 'id': 2},
                    {'text': 'D. The first flight qualified satellite off the production line.', 'correct': True, 'id': 3}
                ],
                'explanation': '',
                'difficulty': 0.67,
                'discrimination': 6,
                'guessing': 0.25
            },
        ]


    def index(self):
        for question in self.question_list:
            self.client.index_question(question['text'], json.dumps(question['choices']),
                                       question['difficulty'], question['discrimination'],
                                       question['guessing'], question['topics'], question['explanation'])
        return 0
