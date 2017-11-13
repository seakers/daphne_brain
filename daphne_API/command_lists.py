from sqlalchemy.orm import sessionmaker
import daphne_API.historian.models as models
from VASSAR_API.api import VASSARClient

general_commands = [
    'stop'
]

ifeed_commands = [

]

vassar_commands = [
    'why does design ${design_id} have this science benefit?'
]

critic_commands = [
    'what do you think of design ${design_id}?'
]

historian_commands = [
    'which missions can measure ${measurement} [between ${year} and ${year}]?',
    'which missions do we currently use to measure ${measurement}?',
    'which instruments can measure ${measurement} [between ${year} and ${year}]?',
    'which instruments do we currently use to measure ${measurement}?',
    'which missions have flown ${technology} [between ${year} and ${year}]?',
    'which missions are currently flying ${technology}?',
    'which orbit is the most typical for ${technology}?',
    'which orbit is the most typical for ${measurement}?',
    'when was mission ${mission} launched?'
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
