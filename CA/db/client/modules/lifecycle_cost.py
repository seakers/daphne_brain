from client.modules.AbstractBuilder import AbstractBuilder



def get_module():

    builder = AbstractBuilder('mdi-recycle-variant', ['Lifecycle Cost'], 'Cost Estimation')

    builder.add_slide('LC_1')
    builder.add_slide('LC_2')
    builder.add_slide('LC_3')
    builder.add_slide('LC_4')
    builder.add_slide('LC_5')

    builder.add_mc_question(
        'Which of the following is NOT a main lifecycle cost phase',
        [
            {'text': 'A. Operations and Maintenance', 'correct': False, 'id': 0},
            {'text': 'B. Production', 'correct': False, 'id': 1},
            {'text': 'C. Decommissioning', 'correct': True, 'id': 2},
            {'text': 'D. None of the above', 'correct': False, 'id': 4}
        ],
        'The three lifecycle cost phases are: 1) Research, Development, Test, and Evaluation, 2) Production, and 3) Operations and Maintenance.',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=5,
        graded=False
    )

    builder.add_tf_question(
        'The Research, Development, Test, and Evaluation phase includes costs from technology development for system components.',
        False,
        'Technology development for system components is included in the Production phase',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=5,
        graded=False
    )

    builder.add_slide('LC_6')
    builder.add_slide('LC_7')
    builder.add_slide('LC_8')

    builder.add_quiz_start_slide()

    # ---------------------------------------------------------------

    builder.add_tf_question(
        'Space Mission Lifecycle Cost is the total mission cost from satellite launch to satellite end of life.',
        False,
        'Lifecycle cost includes more than just the satellite lifetime, it is the total mission cost from planning through end-of-life.',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_mc_question(
        'Which of the following is NOT considered a main lifecycle cost phase?',
        [
            {'text': 'Development, Test, and Evaluation (RDT&E)', 'correct': False, 'id': 0},
            {'text': 'Production', 'correct': False, 'id': 1},
            {'text': 'Pre-phase A', 'correct': True, 'id': 2},
            {'text': 'Operations and Maintenance (O&M)', 'correct': False, 'id': 3}
        ],
        'Lifecycle cost consists of 3 main phases: 1) Research, Development, Test, and Evaluation, 2) Production, and 3) Operation and Maintenance. Pre-Phase A is the first stage in the NASA program lifecycle.',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_tf_question(
        'Mission design is considered in Lifecycle Cost\'s Research, Development, Test, and Evaluation phase.',
        True,
        'This is true, mission design as well as: analysis, testing of breadboards, brassboards, prototypes, etc...',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_tf_question(
        'Space Mission Lifecycle Cost\'s Research, Development, Test, and Evaluation phase includes technology development for system components',
        False,
        'Technology development for system components happens in the Production phase',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_tf_question(
        'Satellite theoretical first unit (TFU) cost is estimated during the lifecycle cost\'s second main phase',
        True,
        'TFU cost is estimated in the Production phase',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_tf_question(
        'Reusable systems tend to have a higher operations and maintenance cost',
        True,
        'This is true, as more maintenance is typically needed for these systems.',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )

    builder.add_mc_question(
        'Which of the following is NOT a typical cost driver for lifecycle cost\'s operations and maintenance phase?',
        [
            {'text': 'Ground station operations', 'correct': False, 'id': 0},
            {'text': 'Satellite spares', 'correct': False, 'id': 1},
            {'text': 'Breadboard Testing', 'correct': True, 'id': 2},
            {'text': 'None of the above', 'correct': False, 'id': 3}
        ],
        'Breadboard testing is considered in the research, test, development, and evaluation phase.',
        ['Lifecycle Cost'],
        difficulty=0.5,
        discrimination=10,
        graded=True
    )








    # ---------------------------------------------------------------

    builder.add_quiz_end_slide()

    # builder.add_tf_question(
    #     'Lifecycle Cost is the total mission cost from satellite launch to satellite end of life',
    #     False,
    #     'Lifecycle cost includes more than just the satellite lifetime, it is the total mission cost from planning through end-of-life.',
    #     ['Lifecycle Cost'],
    #     difficulty=0.3,
    #     discrimination=4,
    #     graded=True
    # )
    # builder.add_mc_question(
    #     'For which of the following subsystems is mass a cost driver?',
    #     [
    #         {'text': 'A. Spacecraft Bus', 'correct': False, 'id': 0},
    #         {'text': 'B. Attitude Determination and Control System (ADCS)', 'correct': False, 'id': 1},
    #         {'text': 'C. Propulsion', 'correct': False, 'id': 2},
    #         {'text': 'D. All of the above', 'correct': True, 'id': 3}
    #     ],
    #     'Explanation',
    #     ['Lifecycle Cost'],
    #     difficulty=0.45,
    #     discrimination=4,
    #     graded=True
    # )
    # builder.add_tf_question(
    #     'Aperture Diameter is a cost driver for the Attitude Determination and Control Subsystem (ADCS).',
    #     False,
    #     'Explanation',
    #     ['Lifecycle Cost'],
    #     difficulty=0.3,
    #     discrimination=4,
    #     graded=True
    # )
    # builder.add_mc_question(
    #     'For which of the following subsystems is mass a cost driver?',
    #     [
    #         {'text': 'A. Spacecraft Bus', 'correct': False, 'id': 0},
    #         {'text': 'B. Attitude Determination and Control System (ADCS)', 'correct': False, 'id': 1},
    #         {'text': 'C. Propulsion', 'correct': False, 'id': 2},
    #         {'text': 'D. All of the above', 'correct': True, 'id': 3}
    #     ],
    #     'Explanation',
    #     ['Lifecycle Cost'],
    #     difficulty=0.45,
    #     discrimination=4,
    #     graded=True
    # )
    # builder.add_tf_question(
    #     'Beginning of life power is a cost driver for the satellite payload.',
    #     False,
    #     '',
    #     ['Lifecycle Cost'],
    #     difficulty=0.4,
    #     discrimination=4,
    #     graded=True
    # )
    # builder.add_mc_question(
    #     'Which of the following is considered a main phase of Lifecycle Cost Estimation?',
    #     [
    #         {'text': 'A. Research, Development, Test, and Evaluation Phase', 'correct': False, 'id': 0},
    #         {'text': 'B. Production Phase', 'correct': False, 'id': 1},
    #         {'text': 'C. Operations and Maintenance Phase', 'correct': False, 'id': 2},
    #         {'text': 'D. All of the above', 'correct': True, 'id': 3}
    #     ],
    #     'Explanation',
    #     ['Lifecycle Cost'],
    #     difficulty=0.5,
    #     discrimination=5,
    #     graded=True
    # )

    







    return builder.get_module()



