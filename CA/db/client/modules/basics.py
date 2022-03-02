from client.modules.AbstractBuilder import AbstractBuilder



def get_module():
    builder = AbstractBuilder('mdi-alphabetical', ['Lifecycle Cost', 'Cost Estimation Methods'])

    builder.add_slide('LifecycleCost')
    builder.add_mc_question(
        'Which of these is considered to be a recurring cost element?',
        [
            {'text': 'A. Satellite fabrication for a single sat mission', 'correct': False, 'id': 0},
            {'text': 'B. Operations', 'correct': True, 'id': 1},
            {'text': 'C. Development', 'correct': False, 'id': 2},
            {'text': 'D. None of the above', 'correct': False, 'id': 3}
        ],
        'Because only once satellite has to be fabricated in A, this would be considered a non-recurring cost element. Operations costs is the correct answer.',
        ['Cost Estimation Methods']
    )
    builder.add_slide('Approaches')
    builder.add_mc_question(
        'Which cost estimation approach uses Cost Estimation Relationships (CERs)?',
        [
            {'text': 'A. Top-down', 'correct': True, 'id': 0},
            {'text': 'B. Bottom-up', 'correct': False, 'id': 1},
            {'text': 'C. Analogy', 'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': False, 'id': 3}
        ],
        'A is correct.',
        ['Cost Estimating Relationships']
    )
    builder.add_slide('NASAModel')

    return builder.get_module()


