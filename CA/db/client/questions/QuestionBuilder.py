


class QuestionBuilder:

    def __init__(self, topics, parameters=(5, 0.5)):
        self.topics = topics

        self.text = 'No text given for question'
        self.explanation = None

        self.discrimination = parameters[0]
        self.difficulty = parameters[1]
        self.guessing = None

    def set_text(self, text):
        self.text = text
        return self

    def set_explanation(self, explanation):
        self.explanation = explanation
        return self

    def build_tf_question(self, answer):
        choices = [
            {'text': 'A. True', 'correct': True, 'id': 0},
            {'text': 'B. False', 'correct': False, 'id': 1}
        ]
        if answer is False:
            choices = [
                {'text': 'A. True', 'correct': False, 'id': 0},
                {'text': 'B. False', 'correct': True, 'id': 1}
            ]

        return {
            'topics': self.topics,
            'text': self.text,
            'choices': choices,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'discrimination': self.discrimination,
            'guessing': 0.5
        }

    def build_mc_question(self, choices):
        prefixes = ['A. ', 'B. ', 'C. ', 'D. ', 'E. ', 'F. ', 'G. ']
        guessing = float(1.0/len(choices))

        q_choices = []
        for idx, choice in enumerate(choices):
            q_choices.append(
                {
                    'text': str(prefixes[idx] + choice[0]),
                    'correct': choice[1],
                    'id': idx
                }
            )
        return {
            'topics': self.topics,
            'text': self.text,
            'choices': q_choices,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'discrimination': self.discrimination,
            'guessing': guessing
        }





