from sqlalchemy.orm import sessionmaker
import daphne_API.historian.models as models
from VASSAR_API.api import VASSARClient

general_commands = [
    'Stop'
]

datamining_commands = [

]

analyst_commands = [
    'Why does design ${design_id} have this science benefit?'
]

critic_commands = [
    'What do you think of design ${design_id}?',
    'What does agent ${agent} think of design ${design_id}?'
]

historian_commands = [
    'Which missions can measure ${measurement} [between ${year} and ${year}]?',
    'Which missions do we currently use to measure ${measurement}?',
    'Which instruments can measure ${measurement} [between ${year} and ${year}]?',
    'Which instruments do we currently use to measure ${measurement}?',
    'Which missions have flown ${technology} [between ${year} and ${year}]?',
    'Which missions are currently flying ${technology}?',
    'Which orbit is the most typical for ${technology}?',
    'Which orbit is the most typical for ${measurement}?',
    'When was mission ${mission} launched?'
]


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


def objectives_list():
    VASSAR = VASSARClient()
    VASSAR.startConnection()
    objectives = VASSAR.client.getObjectiveList()
    VASSAR.endConnection()
    return objectives


orbits_alias = [
    "1: LEO-600-polar-NA (Inclined, non-sun-synchronous)",
    "2: SSO-600-SSO-AM (Sun-synchronous Medium Altitude Morning)",
    "3: SSO-600-SSO-DD (Sun-synchronous Medium Altitude Dawn-Dusk)",
    "4: SSO-800-SSO-DD (Sun-synchronous High Altitude Dawn-Dusk)",
    "5: SSO-800-SSO-PM (Sun-synchronous High Altitude Afternoon)"
]
