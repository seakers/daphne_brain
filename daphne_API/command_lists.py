from sqlalchemy.orm import sessionmaker
import daphne_API.historian.models as models
from VASSAR_API.api import VASSARClient

general_commands = [
    ('0000', 'Stop')
]

datamining_commands = [

]

analyst_commands = [
    ('2000', 'Why does design ${design_id} have this science benefit?'),
    ('2008', 'What is the ${instrument_parameter} of ${vassar_instrument}?')
]

critic_commands = [
    ('3000', 'What do you think of design ${design_id}?'),
    ('3005', 'What do you think of this design?')
    #'What does agent ${agent} think of design ${design_id}?'
]

historian_commands = [
    #'Which missions can measure ${measurement} [between ${year} and ${year}]?',
    #'Which missions do we currently use to measure ${measurement}?',
    #'Which instruments can measure ${measurement} [between ${year} and ${year}]?',
    #'Which instruments do we currently use to measure ${measurement}?',
    #'Which missions have flown ${technology} [between ${year} and ${year}]?',
    #'Which missions are currently flying ${technology}?',
    ('4006', 'Which orbit is the most typical for ${technology}?'),
    ('4007', 'Which orbit is the most typical for ${measurement}?'),
    #'When was mission ${mission} launched?'
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


instruments_alias = [
    "A: ACE_ORCA, Ocean colour instruments, Medium-resolution spectro-radiometer",
    "B: ACE_POL, Multiple direction/polarisation radiometers, Multi-channel/direction/polarisation radiometer",
    "C: ACE_LID, Lidars, Atmospheric lidar",
    "D: CLAR_ERB, Hyperspectral imagers, Multi-purpose imaging Vis/IR radiometer",
    "E: ACE_CPR, Cloud profile and rain radars, Cloud and precipitation radar",
    "F: DESD_SAR, Imaging microwave radars, Imaging radar (SAR)",
    "G: DESD_LID, Lidars, Lidar altimeter",
    "H: GACM_VIS, Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "I: GACM_SWIR, Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "J: HYSP_TIR, Imaging multi-spectral radiometers (vis/IR), Medium-resolution IR spectrometer",
    "K: POSTEPS_IRS, Atmospheric temperature and humidity sounders, Medium-resolution IR spectrometer",
    "L: CNES_KaRIN, Radar altimeters, Radar altimeter"
]