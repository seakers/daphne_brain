from client.questions.QuestionBuilder import QuestionBuilder



def get_questions():
    return [
        QuestionBuilder(['Lifecycle Cost'])
            .set_text('The cost of a satellite\'s propulsion system is driven in part by propulsion system type')
            .set_explanation('')
            .build_tf_question(True),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('The operational and maintenance phase of a mission is typically more expensive for constellations and reusable systems.')
            .set_explanation('')
            .build_tf_question(True),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('During the production phase, the cost of producing multiple similar units is estimated using a')
            .set_explanation('')
            .build_mc_question([
            ('Deterministic Model', False),
            ('Learning Curve', True),
            ('Design Structure Matrix', False),
            ('Genetic Algorithm', False)
        ]),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('Which of the following best describes a Work Breakdown Structure (WBS)?')
            .set_explanation('')
            .build_mc_question([
            ('An organizational table used to categorize and normalize costs', True),
            ('A document for delegating work to contractors', False),
            ('A method for scheduling project tasks', False),
            ('None of the above', False)
        ]),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('Which of the following is NOT considered a main lifecycle cost phase?')
            .set_explanation('')
            .build_mc_question([
            ('Development, Test, and Evaluation (RDT&E)', False),
            ('Production', False),
            ('Pre-phase A', True),
            ('Operations and Maintenance (O&M)', False)
        ]),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('Lifecycle Cost\'s Research, Development, Test, and Evaluation phase (RDT&E) includes design, analysis, and testing of breadboards, brassboards, prototypes, and qualification units')
            .set_explanation('')
            .build_tf_question(True),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('Replacement satellites and launches after the space system final operating capability has been established are not considered production units.')
            .set_explanation('')
            .build_tf_question(True),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('The operations and maintenance phase consists of ongoing operations and maintenance costs, excluding software maintenance.')
            .set_explanation('')
            .build_tf_question(False),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('The Production phase of lifecycle cost incorporates the cost of producing flight units. However, it doesn\'t incorporate their launch costs.')
            .set_explanation('')
            .build_tf_question(False),

        QuestionBuilder(['Lifecycle Cost'])
            .set_text('Which of the following best describes the Theoretical First Unit (TFU) for a space mission?')
            .set_explanation('')
            .build_mc_question([
            ('A theory about early satellite design', False),
            ('A unit of data used to define initial downlink speed', False),
            ('The very first satellite design iteration', False),
            ('The first flight qualified satellite off the production line.', True)
        ]),
    ]


