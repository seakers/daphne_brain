from client.modules.AbstractBuilder import AbstractBuilder

def get_module():

    status = {
        'color': '#E65100',
        'text': 'beta'
    }

    builder = AbstractBuilder('mdi-satellite-variant', ['Spacecraft Subsystems'], 'Space Training 101', status)

    builder.add_slide('DODS_15')  # Spacecraft bus
    builder.add_slide('DODS_16')
    builder.add_slide('DODS_17')
    builder.add_slide('DODS_18')
    builder.add_slide('DODS_19')
    builder.add_slide('DODS_20')
    builder.add_slide('DODS_21')  # Cost drivers

    builder.add_tf_question(
        'One function of the satellite bus is to point the onboard payload.',
        True,
        'This is true',
        ['Spacecraft Subsystems']
    )

    builder.add_mc_question(
        'Which of the following are considered functions of the spacecraft bus?',
        [
            {'text': 'A. Maintains temperature',
             'correct': False, 'id': 0},
            {'text': 'B. Provides power',
             'correct': False, 'id': 1},
            {'text': 'C. Transmits mission and tracking data to ground',
             'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': True, 'id': 3}
        ],
        'The spacecraft bus is responsible for all of these functions',
        ['Spacecraft Subsystems']
    )



    builder.add_slide('DODS_22')  # Structures & Mechanisms Subsystem
    builder.add_slide('DODS_23')
    builder.add_slide('DODS_24')  # Cost drivers




    builder.add_slide('DODS_25')  # Thermal Control
    builder.add_slide('DODS_26')
    builder.add_slide('DODS_27')
    builder.add_slide('DODS_28')  # Cost drivers




    builder.add_slide('DODS_29')  # EPS
    builder.add_slide('DODS_30')
    builder.add_slide('DODS_31')
    builder.add_slide('DODS_32')
    builder.add_slide('DODS_33')
    builder.add_slide('DODS_34')
    builder.add_slide('DODS_35')
    builder.add_slide('DODS_36')
    builder.add_slide('DODS_37')
    builder.add_slide('DODS_38')  # Cost drivers





    builder.add_slide('DODS_39')  # ADCS
    builder.add_slide('DODS_40')
    builder.add_slide('DODS_41')
    builder.add_slide('DODS_42')
    builder.add_slide('DODS_43')
    builder.add_slide('DODS_44')
    builder.add_slide('DODS_45')
    builder.add_slide('DODS_46')
    builder.add_slide('DODS_47')  # Cost drivers




    builder.add_slide('DODS_48')  # Propulsion
    builder.add_slide('DODS_49')
    builder.add_slide('DODS_50')  # Cost drivers



    builder.add_slide('DODS_51')  # TT&C C&DH
    builder.add_slide('DODS_52')
    builder.add_slide('DODS_53')  # Cost drivers



    # builder.add_slide('DODS_54')  # Typical Vehicle Level Test Program


    builder.add_slide('DODS_55')  # Quiz Questions

    builder.add_mc_question(
        'Which of the following parameters should be considered when designing a spacecraft\'s structures and mechanisms subsystem?',
        [
            {'text': 'A. Mass and geometry',
             'correct': False, 'id': 0},
            {'text': 'B. Thermal properties',
             'correct': False, 'id': 1},
            {'text': 'C. Load conditions',
             'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': True, 'id': 3}
        ],
        'All of the above are design considerations',
        ['Spacecraft Subsystems']
    )

    builder.add_tf_question(
        'Heaters provide passive thermal control to the satellite.',
        False,
        'This is false',
        ['Spacecraft Subsystems']
    )

    builder.add_mc_question(
        'Why do satellites need both solar arrays and batteries?',
        [
            {'text': 'A. Having two different power sources adds redundancy to the EPS',
             'correct': False, 'id': 0},
            {'text': 'B. When satellites have a long eclipse time, they need batteries to continue nominal operations',
             'correct': True, 'id': 1},
            {'text': 'C. Solar arrays are needed because they diffuse extra heat generated by the batteries',
             'correct': False, 'id': 2},
            {'text': 'D. None  of the above', 'correct': False, 'id': 3}
        ],
        'While choice A seems enticing (redundancy improves reliability), it is not the primary purpose both are needed. Choice B is correct.',
        ['Spacecraft Subsystems']
    )

    builder.add_tf_question(
        'The electrical power subsystem distributes the same converted voltage to all subsystems.',
        False,
        'This is false',
        ['Spacecraft Subsystems']
    )

    builder.add_mc_question(
        'Which of the following is a main process of the Attitude Determination and Control subsystem?',
        [
            {'text': 'A. Controls the power flowing to different subsystems',
             'correct': False, 'id': 0},
            {'text': 'B. Controls battery power levels',
             'correct': False, 'id': 1},
            {'text': 'C. Controlling telemetry data communication',
             'correct': False, 'id': 2},
            {'text': 'D. None  of the above', 'correct': True, 'id': 3}
        ],
        'None of these are processes of the ADCS.',
        ['Spacecraft Subsystems']
    )

    builder.add_mc_question(
        'Which of these are considered to be main cost drivers for the TT&C subsystem?',
        [
            {'text': 'A. Spacecraft complexity',
             'correct': False, 'id': 0},
            {'text': 'B. Redundancy',
             'correct': False, 'id': 1},
            {'text': 'C. Nuclear Survivability',
             'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': True, 'id': 3}
        ],
        'All of these are main cost drivers.',
        ['Spacecraft Subsystems']
    )


    # builder.add_slide('DODS_56')  # Backup
    # builder.add_slide('DODS_57')  # Mission/Payload Class




    return builder.get_module()


















