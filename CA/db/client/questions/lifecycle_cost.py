from client.questions.QuestionBuilder import QuestionBuilder


easy_question = (5, 0.3)
medi_question = (5, 0.5)
hard_question = (5, 0.7)



def get_questions():
    return [

        # ------------------------ DEMO QUESTIONS ------------------------

        ###############
        ### SLIDE 1 ###
        ###############
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Space Mission Lifecycle Cost is the total mission cost.')
        .set_explanation(
            'True, lifecycle cost is the total mission cost from planning through end-of-life')
        .build_tf_question(True),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text(
        #     'Space Mission Lifecycle Cost is the total mission cost from satellite launch to satellite end of life.')
        # .set_explanation(
        #     'Lifecycle cost includes more than just the satellite lifetime, it is the total mission cost from planning through end-of-life.')
        # .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'Which of the following best describes Space Mission Lifecycle Cost')
        .set_explanation(
            'Space mission lifecycle cost is the total mission cost from planning all the way through end-of-life.')
        .build_mc_question([
            ('Mission cost from satellite launch to satellite death', False),
            ('Mission cost from planning through end-of-life', True),
            ('Total mission cost minus research costs', False),
            ('Total mission cost including a portion of costs from previous enabling missions', False)
        ]),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text('How many main phases does lifecycle cost have?')
        .set_explanation('Lifecycle cost consists of 3 main phases: 1) Research, Development, Test, and Evaluation, 2) Production, and 3) Operation and Maintenance')
        .build_mc_question([
            ('1 Phase', False),
            ('2 Phases', False),
            ('3 Phases', True),
            ('4 Phases', False)
        ]),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text('Which of the following is NOT considered a main lifecycle cost phase?')
        # .set_explanation('Lifecycle cost consists of 3 main phases: 1) Research, Development, Test, and Evaluation, 2) Production, and 3) Operation and Maintenance. Pre-Phase A is the first stage in the NASA program lifecycle.')
        # .build_mc_question([
        #     ('Development, Test, and Evaluation (RDT&E)', False),
        #     ('Production', False),
        #     ('Pre-phase A', True),
        #     ('Operations and Maintenance (O&M)', False)
        # ]),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'For very large missions, Space Mission Lifecycle Cost typically has 5 phases instead of 3 to account for complexity.')
        .set_explanation(
            'This is false, lifecycle cost always has three main phases.')
        .build_tf_question(False),

        ###############
        ### SLIDE 2 ###
        ###############

        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Lifecycle Cost\'s Research, Development, Test, and Evaluation phase consists mostly of recurring costs')
        .set_explanation(
            'This lifecycle cost phase consists mostly of non-recurring costs.')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'Lifecycle Cost\'s Research, Development, Test, and Evaluation phase can consist of both recurring and nonrecurring costs')
        .set_explanation(
            'While this phase mostly consists of nonrecurring costs, there are instances where recurring costs will be considered.')
        .build_tf_question(True),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Which of the following items are considered in Lifecycle Cost\'s Research, Development, Test, and Evaluation phase?')
        .set_explanation('All of these items are considered')
        .build_mc_question([
            ('Mission design and analysis', False),
            ('Breadboards and prototypes', False),
            ('Qualification units', False),
            ('All of the above', True)
        ]),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text(
        #     'Mission design is considered in Lifecycle Cost\'s Research, Development, Test, and Evaluation phase')
        # .set_explanation(
        #     'This is true, mission design as well as: analysis, testing of breadboards, brassboards, prototypes, etc...')
        # .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'Which of the following items are NOT considered in Lifecycle Cost\'s Research, Development, Test, and Evaluation phase?')
        .set_explanation('Only non-recurring ground station costs are considered in this phase')
        .build_mc_question([
            ('Mission design and analysis', False),
            ('Breadboards and prototypes', False),
            ('Qualification units', False),
            ('Total ground station costs', True),
            ('None of the above', False)
        ]),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'All technology development is included in Lifecycle Cost\'s Research, Development, Test, and Evaluation phase')
        .set_explanation(
            'Technology development for system components happens in the Production phase')
        .build_tf_question(False),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text(
        #     'Space Mission Lifecycle Cost\'s Research, Development, Test, and Evaluation phase includes technology development for system components')
        # .set_explanation(
        #     'Technology development for system components happens in the Production phase')
        # .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'All technology development is included in Lifecycle Cost\'s first main phase')
        .set_explanation(
            'Technology development for system components happens in the Production phase')
        .build_tf_question(False),

        ###############
        ### SLIDE 3 ###
        ###############

        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text('Which of the following is not incorporated in lifecycle cost\'s production phase?')
        .set_explanation('')
        .build_mc_question([
            ('The cost of producing flight units', False),
            ('The costs of launching flight units', True)
        ]),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'The Production phase of lifecycle cost incorporates the cost of producing flight units but not their launch costs.')
        .set_explanation('The Production phase incorporates both the cost of producing flight units and launching them')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'The second phase of lifecycle costing incorporates the cost of producing flight units but not their launch costs.')
        .set_explanation('The Production phase incorporates both the cost of producing flight units and launching them')
        .build_tf_question(False),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text('Which main lifecycle cost phase uses Theoretical First Unit models?')
        .set_explanation('')
        .build_mc_question([
            ('Production Phase', True),
            ('Operations and Maintenance Phase', False),
            ('Researching, Development, Test, and Evaluation Phase', False),
            ('All of the above', False)
        ]),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text(
        #     'Satellite theoretical first unit (TFU) cost is estimated during the lifecycle cost\'s second main phase')
        # .set_explanation(
        #     'TFU cost is estimated in the Production phase.')
        # .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'])  # hard
        .set_text('Which of the following best describes the Theoretical First Unit (TFU) for a space mission?')
        .set_explanation('')
        .build_mc_question([
            ('A theory about early satellite design', False),
            ('A unit of data used to define initial downlink speed', False),
            ('The very first satellite design iteration', False),
            ('The first flight qualified satellite off the production line.', True)
        ]),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text('During the production phase, the cost of producing multiple similar units is estimated using a')
        .set_explanation('')
        .build_mc_question([
            ('Deterministic Model', False),
            ('Learning Curve', True),
            ('Design Structure Matrix', False),
            ('Genetic Algorithm', False)
        ]),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'If multiple satellite units are being produced, a learning curve factor is applied to the Theoretical First Unit (TFU)')
        .set_explanation(
            'True, a learning curve factor is only applied if multiple satellite units are being produced.')
        .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'If multiple satellite units are being produced, the cost of subsequent units is independent of the Theoretical First Unit (TFU)')
        .set_explanation(
            'A learning curve factor is applied to the TFU. So, the TFU model is still used.')
        .build_tf_question(False),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text('Which of the following is NOT considered as production unit in lifecycle cost\'s production phase?')
        .set_explanation('Replacement Satellites and launches after the space system final operating capability are not considered in this phase.')
        .build_mc_question([
            ('Satellite First Unit', False),
            ('Replacement Satellites', True)
        ]),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'In lifecycle cost\'s production phase, all satellite units produced are considered, even replacement satellites')
        .set_explanation(
            'Replacement satellites are not considered as production units during this phase')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'During lifecycle cost\'s second main phase, launches are only considered if they are before final operating capability')
        .set_explanation(
            'True, launches after final operating capability are not considered in this phase.')
        .build_tf_question(True),

        ###############
        ### SLIDE 4 ###
        ###############

        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Lifecycle Cost\'s operations and maintenance phase includes software maintenance costs.')
        .set_explanation(
            'True, this phase does consider software maintenance.')
        .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'In space mission lifecycle cost, spacecraft unit replacement costs are only considered in the operations and maintenance phase.')
        .set_explanation(
            'True, no other phase includes satellite replacement costs.')
        .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text('In lifecycle cost\'s third main phase, which of the following is not considered?')
        .set_explanation(
            'The first satellite produced is considered in the second main phase, Production')
        .build_mc_question([
            ('Software Maintenance', False),
            ('Replacement Satellites', False),
            ('The First Satellite Produced', True),
            ('All of the above', False),
            ('None of the above', False)
        ]),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Lifecycle Cost\'s operations and maintenance phase is always the costliest phase, for any and every mission.')
        .set_explanation(
            'While this phase tends to be the most costly, this is not always this case.')
        .build_tf_question(False),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text(
        #     'Reusable systems tend to have a higher operations and maintenance cost.')
        # .set_explanation(
        #     'This is true, as more maintenance is typically needed for these systems.')
        # .build_tf_question(True),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text('Which of these systems tend to have a less costly operations and maintenance phase?')
        .set_explanation(
            'Monolithic satellite systems tend to be less costly in this area due to less replacement costs.')
        .build_mc_question([
            ('Reusable Systems', False),
            ('Monolithic Satellite Systems', True),
            ('Constellations', False),
            ('All of the above', False),
            ('None of the above', False)
        ]),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'For most space programs, mission design is the main cost driver for the operations and maintenance phase.')
        .set_explanation(
            'This is false, as the operations and maintenance phase does not consider mission design costs.')
        .build_tf_question(False),
        # QuestionBuilder(['Lifecycle Cost'])  # medium
        # .set_text('Which of the following is NOT a typical cost driver for lifecycle cost\'s operations and maintenance phase?')
        # .set_explanation(
        #     'Breadboard testing is considered in the research, test, development, and evaluation phase.')
        # .build_mc_question([
        #     ('Ground station operations', False),
        #     ('Satellite spares', False),
        #     ('Breadboard Testing', True),
        #     ('None of the above', False)
        # ]),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'The third lifecycle cost phase is typically driven by all ground station costs')
        .set_explanation(
            'While this phase is typically driven by ground station operations, it is not driven by one time ground station costs. Thus, the answer is false')
        .build_tf_question(False),

        ###############
        ### SLIDE 6 ###
        ###############

        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'The first step in lifecycle cost analysis is creating a work breakdown struction (WBS).')
        .set_explanation(
            'The first step is to identify cost drivers.')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'Which of the following is the first step in lifecycle cost analysis?')
        .set_explanation(
            'The first step is to identify cost drivers.')
        .build_mc_question([
            ('Creating a work breakdown structure', False),
            ('Identifying cost drivers', True),
            ('Breadboard Testing', False),
            ('None of the above', False)
        ]),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'If a very similar mission exists, one can always skip identifying cost drivers during lifecycle cost analysis')
        .set_explanation(
            'Cost drivers must always be identified for every mission.')
        .build_tf_question(False),
        # -----
        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Space mission lifetime is not considered a spacecraft cost driver.')
        .set_explanation(
            'Lifetime is typically a spacecraft cost driver')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'Which of the following has a smaller impact on spacecraft cost.')
        .set_explanation(
            'Spacecraft mass and orbit are both typically cost drivers. The number of contracting companies is not a cost driver.')
        .build_mc_question([
            ('Spacecraft mass', False),
            ('Spacecraft orbit', False),
            ('Number of contracting companies', True),
            ('None of these are cost drivers', False)
        ]),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text(
            'Which of the following is considered a typical spacecraft cost driver?')
        .set_explanation(
            'All of these parameters drive spacecraft cost.')
        .build_mc_question([
            ('Spacecraft mass', False),
            ('Complexity', False),
            ('Reliability', False),
            ('Delta-V budget', False),
            ('All of the above', True)
        ]),

        ###############
        ### SLIDE 7 ###
        ###############

        QuestionBuilder(['Lifecycle Cost'], easy_question)  # easy
        .set_text(
            'Work Breakdown Structures are not necessary during the lifecycle cost estimation process.')
        .set_explanation(
            'Work Breakdown Structures are necessary for organizing and normalizing costs')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], medi_question)  # medium
        .set_text(
            'Work Breakdown Structures are only used to categorize costs.')
        .set_explanation(
            'Work Breakdown Structures are used to both categorize and normalize costs.')
        .build_tf_question(False),
        QuestionBuilder(['Lifecycle Cost'], hard_question)  # hard
        .set_text('Which of the following best describes a Work Breakdown Structure (WBS)?')
        .set_explanation('')
        .build_mc_question([
            ('An organizational table used to categorize and normalize costs', True),
            ('A document for delegating work to contractors', False),
            ('A method for scheduling project tasks', False),
            ('None of the above', False)
        ])

    ]


