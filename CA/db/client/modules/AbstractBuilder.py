




class AbstractBuilder:

    def __init__(self, icon, topics, course=None, status=None):
        self.icon = icon
        self.topics = topics
        self.course = course
        self.status = status
        self.slides = []

        self.q_counter = 1


    def get_module(self):
        return {
            'slides': self.slides,
            'icon': self.icon,
            'slide_idx': 0,
            'topics': self.topics,
            'course': self.course,
            'status': self.status,
        }

    def add_slide(self, src):
        self.slides.append({
            'type': 'info',
            'src': src,
            'idx': len(self.slides)
        })

    def add_quiz_start_slide(self):
        self.slides.append({
            'type': 'quiz_start',
            'idx': len(self.slides)
        })

    def add_quiz_end_slide(self):
        self.slides.append({
            'type': 'quiz_end',
            'idx': len(self.slides)
        })

    def add_tf_question(self, text, answer, explanation, topics, difficulty=0.0, discrimination=0.0, graded=False):

        # --> Question Info
        question_info = {
            'type': 'question',
            'answered': False,
            'correct': False,
            'choice_id': -1,
            'idx': len(self.slides),
            'graded': graded
        }

        # --> Question
        q_text = '(T/F) ' + text
        self.q_counter += 1
        choices = [
            {'text': 'A. True', 'correct': True, 'id': 0},
            {'text': 'B. False', 'correct': False, 'id': 1},
        ]
        if answer == False:
            choices = [
                {'text': 'A. True', 'correct': False, 'id': 0},
                {'text': 'B. False', 'correct': True, 'id': 1},
            ]
        question = {
            'topics': topics,
            'text': q_text,
            'choices': choices,
            'explanation': explanation,
            'difficulty': difficulty,
            'discrimination': discrimination,
            'guessing': 0.5
        }

        question_info['question'] = question
        self.slides.append(question_info)



    def add_mc_question(self, text, choices, explanation, topics, difficulty=0.0, discrimination=0.0, graded=False):



        # --> Question Info
        question_info = {
            'type': 'question',
            'answered': False,
            'correct': False,
            'choice_id': -1,
            'idx': len(self.slides),
            'graded': graded
        }

        # --> Question
        q_text = text
        self.q_counter += 1

        question = {
            'topics': topics,
            'text': q_text,
            'choices': choices,
            'explanation': explanation,
            'difficulty': difficulty,
            'discrimination': discrimination,
            'guessing': float(1.0 / float(len(choices)))
        }

        question_info['question'] = question
        self.slides.append(question_info)