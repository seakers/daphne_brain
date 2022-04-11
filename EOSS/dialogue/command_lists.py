from django.conf import settings
from sqlalchemy.orm import sessionmaker

from EOSS.vassar.api import VASSARClient

from asgiref.sync import async_to_sync, sync_to_async
from EOSS.graphql.client.Dataset import DatasetGraphqlClient
from EOSS.graphql.client.Admin import AdminGraphqlClient
from EOSS.graphql.client.Problem import ProblemGraphqlClient
from EOSS.graphql.client.Abstract import AbstractGraphqlClient

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
    ('2010', 'What is the requirement for ${engineer_measurement_parameter} for ${engineer_measurement}?'),
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


def orbits_info(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_orbits_info(vassar_client, problem_id)


def instruments_info(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_instruments_info(vassar_client, problem_id)


def engineer_instrument_list(vassar_client: VASSARClient, problem_id: int):
    return [instr["name"] for instr in problem_specific.get_instrument_dataset(problem_id)]


def engineer_instrument_parameter_list(vassar_client: VASSARClient, group_id: int):
    return problem_specific.get_instruments_parameters(vassar_client, group_id)


def engineer_measurement_list(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_problem_measurements(vassar_client, problem_id)


def engineer_measurement_parameter_list(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_measurement_parameters(vassar_client, problem_id)


def engineer_stakeholder_list(vassar_client: VASSARClient, problem_id: int):
    result = async_to_sync(AbstractGraphqlClient.get_stakeholders)(problem_id, True, False, False)
    return [stake['name'] for stake in result['panel']]
    # return problem_specific.get_stakeholders_list(vassar_client, problem_id)


def engineer_objectives_list(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_objectives_list(vassar_client, problem_id)


def engineer_subobjectives_list(vassar_client: VASSARClient, problem_id: int):
    return problem_specific.get_subobjectives_list(vassar_client, problem_id)


def historian_measurements_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    measurements = [measurement.name.strip() for measurement in session.query(models.Measurement).order_by(models.Measurement.name).all()]
    return measurements


def historian_missions_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    missions = [mission.name.strip() for mission in session.query(models.Mission).order_by(models.Mission.nam).all()]
    return missions


def historian_technologies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    technologies = [technology for technology in models.technologies]
    technologies = technologies + [type.name.strip() for type in session.query(models.InstrumentType).order_by(models.InstrumentType.name).all()]
    return technologies


def historian_agencies_list():
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    agencies = [agency.name.strip() for agency in session.query(models.Agency).order_by(models.Agency.name).all()]
    return agencies


