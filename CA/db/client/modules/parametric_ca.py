from client.modules.AbstractBuilder import AbstractBuilder


ex_choices = [
    {'text': 'A. text',
     'correct': False, 'id': 0},
    {'text': 'B. text',
     'correct': False, 'id': 1},
    {'text': 'C. text',
     'correct': False, 'id': 2},
    {'text': 'D. text', 'correct': True, 'id': 3}
]



def get_module():
    builder = AbstractBuilder('mdi-tag-arrow-down', ['Cost Estimating Relationships'], 'Cost Estimation')

    builder.add_slide('AERO401Slide8')
    builder.add_slide('AERO401Slide9')
    builder.add_slide('AERO401Slide10')
    builder.add_slide('AERO401Slide11')

    builder.add_quiz_start_slide()

    builder.add_mc_question(
        'Parametric cost estimation question 1',
        ex_choices,
        'Explanation',
        ['Parametric Cost Estimation'],
        difficulty=0.5,
        discrimination=4,
        graded=True
    )

    builder.add_mc_question(
        'Parametric cost estimation question 2',
        ex_choices,
        'Explanation',
        ['Parametric Cost Estimation'],
        difficulty=0.6,
        discrimination=5,
        graded=True
    )

    builder.add_mc_question(
        'Parametric cost estimation question 3',
        ex_choices,
        'Explanation',
        ['Parametric Cost Estimation'],
        difficulty=0.7,
        discrimination=6,
        graded=True
    )


    builder.add_quiz_end_slide()


    return builder.get_module()






slides = [
    {
        'type': 'info',
        'src': 'AERO401Slide8',
        'idx': 0
    },
    {
        'type': 'info',
        'src': 'AERO401Slide9',
        'idx': 1
    },
    {
        'type': 'question',
        'answered': False,
        'correct': False,
        'choice_id': -1,
        'idx': 2,
        'question': {
            'topics': ['Work Breakdown Structure'],
            'text': 'Q1. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua?',
            'choices': [
                {'text': 'A. ', 'correct': False, 'id': 0},
                {'text': 'B. ', 'correct': False, 'id': 1},
                {'text': 'C. ', 'correct': False, 'id': 2},
                {'text': 'D. ', 'correct': True, 'id': 3}
            ],
            'explanation': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua',
            'difficulty': 0.0,
            'discrimination': 0.0,
            'guessing': 0.25
        }
    },
    {
        'type': 'info',
        'src': 'AERO401Slide10',
        'idx': 3
    },
    {
        'type': 'question',
        'answered': False,
        'correct': False,
        'choice_id': -1,
        'idx': 4,
        'question': {
            'topics': ['Work Breakdown Structure'],
            'text': 'Q2. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua?',
            'choices': [
                {'text': 'A. ', 'correct': False, 'id': 0},
                {'text': 'B. ', 'correct': False, 'id': 1},
                {'text': 'C. ', 'correct': False, 'id': 2},
                {'text': 'D. ', 'correct': True, 'id': 3}
            ],
            'explanation': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua',
            'difficulty': 0.0,
            'discrimination': 0.0,
            'guessing': 0.25
        }
    },
    {
        'type': 'info',
        'src': 'AERO401Slide11',
        'idx': 5
    },
    {
        'type': 'question',
        'answered': False,
        'correct': False,
        'choice_id': -1,
        'idx': 6,
        'question': {
            'topics': ['Work Breakdown Structure'],
            'text': 'Q3. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua?',
            'choices': [
                {'text': 'A. ', 'correct': False, 'id': 0},
                {'text': 'B. ', 'correct': False, 'id': 1},
                {'text': 'C. ', 'correct': False, 'id': 2},
                {'text': 'D. ', 'correct': True, 'id': 3}
            ],
            'explanation': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua',
            'difficulty': 0.0,
            'discrimination': 0.0,
            'guessing': 0.25
        }
    },
    {
        'type': 'question',
        'answered': False,
        'correct': False,
        'choice_id': -1,
        'idx': 7,
        'question': {
            'topics': ['Work Breakdown Structure'],
            'text': 'Q4. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua?',
            'choices': [
                {'text': 'A. ', 'correct': False, 'id': 0},
                {'text': 'B. ', 'correct': False, 'id': 1},
                {'text': 'C. ', 'correct': False, 'id': 2},
                {'text': 'D. ', 'correct': True, 'id': 3}
            ],
            'explanation': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua',
            'difficulty': 0.0,
            'discrimination': 0.0,
            'guessing': 0.25
        }
    },
]


