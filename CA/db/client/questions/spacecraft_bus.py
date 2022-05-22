from client.questions.QuestionBuilder import QuestionBuilder

template_questions = [

QuestionBuilder(['Spacecraft Bus'])
.set_text('test')
.set_explanation('')
.build_mc_question([
('test', False),
('test', False),
('test', False),
('test', True)
]),


QuestionBuilder(['Spacecraft Bus'])
.set_text('test')
.set_explanation('')
.build_tf_question(True),


]



def get_questions():
    return [

        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following is NOT considered a function of the satellite bus?')
            .set_explanation('')
            .build_mc_question([
            ('Maintaining temperature through a thermal control subsystem', False),
            ('Providing power through its electrical power subsystem', False),
            ('Transmitting mission and tracking data through a communications subsystem', False),
            ('Changing mission requirements in real time', True)
        ]),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('One function of the satellite bus is to maintain control of all satellite subsystems through a command and data handling system')
        .set_explanation('')
        .build_tf_question(True),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('Each spacecraft bus subsystem is independent of each other and should be designed as such')
        .set_explanation('')
        .build_tf_question(False),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('The structure and mechanisms subsystem provides the satellite bus\' frame')
        .set_explanation('')
        .build_tf_question(True),
        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following are NOT considered components of the Spacecraft Bus?')
            .set_explanation('')
            .build_mc_question([
            ('The primary structure', False),
            ('The secondary structure', False),
            ('Deployment mechanisms', False),
            ('Pointing mechanisms', False),
            ('None of the above', True)
        ]),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('The deployment mechanisms component of the structures and mechanisms subsystem includes solar array panels, booms, and antennas')
        .set_explanation('')
        .build_tf_question(True),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('Current models can exactly predict the strength and performance of the structures and mechanisms subsystem, drastically reducing the need for risk analysis')
        .set_explanation('')
        .build_tf_question(False),
        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following should NOT be considered when designing the structures and mechanisms subsystem')
            .set_explanation('')
            .build_mc_question([
            ('Load conditions', False),
            ('Final design specification and production', False),
            ('Satellite Aesthetics', True),
            ('Mass constraints', False),
            ('None of the above', False)
        ]),
        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following is NOT considered cost drivers for a satellite bus\' structures and mechanisms subsystem?')
            .set_explanation('')
            .build_mc_question([
            ('Mechanism complexity', False),
            ('Stability requirements', False),
            ('Component accessibility', False),
            ('None of the above', True)
        ]),
        QuestionBuilder(['Spacecraft Bus'])
        .set_text('There exists both active and passive techniques that a thermal control subsystem can use to move heat away from temperature sensitive hardware')
        .set_explanation('')
        .build_tf_question(True),
        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following is NOT a primary design consideration for the thermal control subsystem')
            .set_explanation('')
            .build_mc_question([
            ('Satellite orbit', False),
            ('Material thermal properties', False),
            ('Thermal gradient constraints', False),
            ('None of the above', True)
        ]),
        QuestionBuilder(['Spacecraft Bus'])
            .set_text('Which of the following is NOT considered a primary cost driver for the thermal control subsystem?')
            .set_explanation('')
            .build_mc_question([
            ('Onboard data storage requirements', False),
            ('Payload power requirements', False),
            ('Spacecraft orbit', False),
            ('None of the above', False)
        ]),

    ]
