from django.conf import settings
from sqlalchemy.orm import sessionmaker

if 'EOSS' in settings.ACTIVE_MODULES:
    import EOSS.historian.models as models
    import EOSS.data.problem_specific as problem_specific


general_commands = [
    ('0000', 'Stop')
]

engineer_commands = [
    ('2000', 'Why does design ${design_id} have this science benefit?'),
    ('2012', 'Why does this design have this science benefit?'),
    ('2017', 'Why does this design have this cost?'),
    ('2001', 'How does ${design_id} satisfy ${subobjective}?'),
    ('2002', 'Why does ${design_id} not satisfy ${subobjective}?'),
    ('2008', 'What is the ${engineer_instrument_parameter} of ${engineer_instrument}?'),
    ('2010', 'What is the requirement for ${engineer_instrument_parameter} for ${engineer_measurement}?'),
    ('2013', 'Explain the stakeholder ${engineer_stakeholder} science benefit for this design.'),
    ('2014', 'Explain the objective ${engineer_objective} science benefit for this design.'),
    ('2016', 'Which instruments improve the science score for stakeholder ${engineer_stakeholder}?'),
    ('2015', 'Which instruments improve the science score for objective ${engineer_objective}?'),
    ('2008', 'What is the ${engineer_instrument_parameter} of ${engineer_instrument}?'),
]

analyst_commands = [
    ('1000', 'What are the driving features?'),
]

explorer_commands = [
]

historian_commands = [
    ('4000', 'Which missions [from ${historian_space_agency}] can measure ${historian_measurement} [between ${year} and ${year}]?'),
    ('4001', 'Which missions [from ${historian_space_agency}] do we currently use to measure ${measurement}?'),
    ('4002', 'Which instruments [from ${historian_space_agency}] can measure ${historian_measurement} [between ${year} and ${year}]?'),
    ('4003', 'Which instruments [from ${historian_space_agency}] do we currently use to measure ${historian_measurement}?'),
    ('4004', 'Which missions [from ${historian_space_agency}] have flown ${historian_technology} [between ${year} and ${year}]?'),
    ('4005', 'Which missions [from ${historian_space_agency}] are currently flying ${historian_technology}?'),
    ('4006', 'Which orbit is the most typical for ${historian_technology}?'),
    ('4007', 'Which orbit is the most typical for ${historian_measurement}?'),
    ('4008', 'When was mission ${historian_mission} launched?'),
    ('4009', 'Which missions have been designed by ${historian_space_agency}?'),
    ('4010', 'Show me a timeline of missions [from ${historian_space_agency}] which measure ${historian_measurement}')
]

critic_commands = [
    ('3000', 'What do you think of design ${design_id}?'),
    ('3005', 'What do you think of this design?')
    #'What does agent ${agent} think of design ${design_id}?'
]


def commands_list(command_list, restricted_list=None):
    if restricted_list is not None:
        return [command[1] for command in command_list if command[0] in restricted_list]
    else:
        return [command[1] for command in command_list]


def general_commands_list(restricted_list=None):
    return commands_list(general_commands, restricted_list)


def engineer_commands_list(restricted_list=None):
    return commands_list(engineer_commands, restricted_list)


def analyst_commands_list(restricted_list=None):
    return commands_list(analyst_commands, restricted_list)


def explorer_commands_list(restricted_list=None):
    return commands_list(explorer_commands, restricted_list)


def historian_commands_list(restricted_list=None):
    return commands_list(historian_commands, restricted_list)


def critic_commands_list(restricted_list=None):
    return commands_list(critic_commands, restricted_list)


def orbits_info(problem):
    return problem_specific.get_orbits_info(problem)


def instruments_info(problem):
    return problem_specific.get_instruments_info(problem)


def engineer_instrument_list(problem):
    return [instr["name"] for instr in problem_specific.get_instrument_dataset(problem)]


def engineer_instrument_parameter_list(problem):
    return problem_specific.get_instruments_sheet(problem)['Attributes-for-object-Instrument']


def engineer_measurement_list(problem):
    return problem_specific.get_param_names(problem)


def engineer_stakeholder_list(problem):
    return problem_specific.get_stakeholders_list(problem)


def engineer_objectives_list(vassar_client, problem):
    vassar_client.start_connection()
    objectives = vassar_client.get_objective_list(problem)
    objectives.sort(key=lambda obj: int(obj[3:]))
    objectives.sort(key=lambda obj: obj[0:2])
    vassar_client.end_connection()
    return objectives


def engineer_subobjectives_list(vassar_client, problem):
    vassar_client.start_connection()
    objectives = vassar_client.get_subobjective_list(problem)
    objectives.sort(key=lambda obj: obj[3:])
    objectives.sort(key=lambda obj: obj[0:2])
    vassar_client.end_connection()
    return objectives


def historian_measurements_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip() for measurement in session.query(models.Measurement).all()]
    return measurements


def historian_missions_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [mission.name.strip() for mission in session.query(models.Mission).all()]
    return missions


def historian_technologies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in models.technologies]
    technologies = technologies + [type.name.strip() for type in session.query(models.InstrumentType).all()]
    return technologies


def historian_agencies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [agency.name.strip() for agency in session.query(models.Agency).all()]
    return agencies


