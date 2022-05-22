from client.modules.AbstractBuilder import AbstractBuilder



def get_module():

    builder = AbstractBuilder('mdi-recycle-variant', ['Lifecycle Cost'], 'Cost Estimation')

    builder.add_slide('LifecycleCost')
    builder.add_slide('Slide1LCCD')
    builder.add_slide('Slide2LCCD')

    builder.add_quiz_start_slide()

    builder.add_tf_question(
        'Aperture Diameter is a cost driver for the Attitude Determination and Control Subsystem (ADCS).',
        False,
        'Explanation',
        ['Lifecycle Cost'],
        difficulty=0.3,
        discrimination=4,
        graded=True
    )
    builder.add_mc_question(
        'For which of the following subsystems is mass a cost driver?',
        [
            {'text': 'A. Spacecraft Bus', 'correct': False, 'id': 0},
            {'text': 'B. Attitude Determination and Control System (ADCS)', 'correct': False, 'id': 1},
            {'text': 'C. Propulsion', 'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': True, 'id': 3}
        ],
        'Explanation',
        ['Lifecycle Cost'],
        difficulty=0.45,
        discrimination=4,
        graded=True
    )
    builder.add_tf_question(
        'Beginning of life power is a cost driver for the satellite payload.',
        False,
        '',
        ['Lifecycle Cost'],
        difficulty=0.4,
        discrimination=4,
        graded=True
    )
    builder.add_mc_question(
        'Which of the following is considered a main phase of Lifecycle Cost Estimation?',
        [
            {'text': 'A. Research, Development, Test, and Evaluation Phase', 'correct': False, 'id': 0},
            {'text': 'B. Production Phase', 'correct': False, 'id': 1},
            {'text': 'C. Operations and Maintenance Phase', 'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': True, 'id': 3}
        ],
        'Explanation',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=5,
        graded=True
    )
    builder.add_tf_question(
        'Satellite theoretical first unit (TFU) cost is estimated during the Operations and Maintenance phase.',
        True,
        '',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=5,
        graded=True
    )
    


    builder.add_quiz_end_slide()




    return builder.get_module()



