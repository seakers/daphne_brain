from sqlalchemy.orm import sessionmaker
import daphne_API.historian.models as models
import daphne_API.problem_specific as problem_specific


general_commands = [
    ('0000', 'Stop')
]

datamining_commands = [

]

analyst_commands = [
    ('2000', 'Why does design ${design_id} have this science benefit?'),
    ('2012', 'Why does this design have this science benefit?'),
    ('2013', 'Explain the stakeholder ${analyst_stakeholder} science benefit for this design.'),
    ('2014', 'Explain the objective ${analyst_objective} science benefit for this design.'),
    ('2016', 'Which instruments improve the science score for stakeholder ${analyst_stakeholder}?'),
    ('2015', 'Which instruments improve the science score for objective ${analyst_objective}?'),
    ('2008', 'What is the ${analyst_instrument_parameter} of ${analyst_instrument}?'),
    ('2010', 'What is the requirement for ${analyst_instrument_parameter} for ${analyst_measurement}?')
]

critic_commands = [
    ('3000', 'What do you think of design ${design_id}?'),
    ('3005', 'What do you think of this design?')
    #'What does agent ${agent} think of design ${design_id}?'
]

historian_commands = [
    ('4000', 'Which missions [from ${space_agency}] can measure ${measurement} [between ${year} and ${year}]?'),
    ('4001', 'Which missions [from ${space_agency}] do we currently use to measure ${measurement}?'),
    #'Which instruments can measure ${measurement} [between ${year} and ${year}]?',
    #'Which instruments do we currently use to measure ${measurement}?',
    #'Which missions have flown ${technology} [between ${year} and ${year}]?',
    #'Which missions are currently flying ${technology}?',
    ('4006', 'Which orbit is the most typical for ${technology}?'),
    ('4007', 'Which orbit is the most typical for ${measurement}?'),
    ('4008', 'When was mission ${mission} launched?'),
    ('4009', 'Which missions have been designed by ${space_agency}?'),
    ('4010', 'Show me a timeline of missions [from ${space_agency}] which measure ${measurement}')
]


def commands_list(command_list, restricted_list=None):
    if restricted_list is not None:
        return [command[1] for command in command_list if command[0] in restricted_list]
    else:
        return [command[1] for command in command_list]


def general_commands_list(restricted_list=None):
    return commands_list(general_commands, restricted_list)


def datamining_commands_list(restricted_list=None):
    return commands_list(datamining_commands, restricted_list)


def analyst_commands_list(restricted_list=None):
    return commands_list(analyst_commands, restricted_list)


def critic_commands_list(restricted_list=None):
    return commands_list(critic_commands, restricted_list)


def historian_commands_list(restricted_list=None):
    return commands_list(historian_commands, restricted_list)


def measurements_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip() for measurement in session.query(models.Measurement).all()]
    return measurements


def missions_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [mission.name.strip() for mission in session.query(models.Mission).all()]
    return missions


def technologies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in models.technologies]
    technologies = technologies + [type.name.strip() for type in session.query(models.InstrumentType).all()]
    return technologies


def agencies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [agency.name.strip() for agency in session.query(models.Agency).all()]
    return agencies


def objectives_list(vassar_client):
    vassar_client.startConnection()
    objectives = vassar_client.client.getObjectiveList()
    objectives.sort(key=lambda obj: int(obj[3:]))
    objectives.sort(key=lambda obj: obj[0:2])
    vassar_client.endConnection()
    return objectives

def analyst_instrument_parameter_list(problem):
    return problem_specific.get_instruments_sheet(problem)['Attributes-for-object-Instrument']


def analyst_instrument_list(problem):
    return [instr["name"] for instr in problem_specific.get_instrument_dataset(problem)]


def analyst_measurement_list(problem):
    return problem_specific.get_param_names(problem)


def analyst_stakeholder_list(problem):
    return problem_specific.get_stakeholders_list(problem)


def orbits_info(problem):
    return problem_specific.get_orbits_info(problem)


def instruments_info(problem):
    return problem_specific.get_instruments_info(problem)
