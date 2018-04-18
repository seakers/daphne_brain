from sqlalchemy.orm import sessionmaker
import daphne_API.historian.models as models
import pandas

instruments_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric/Climate-centric AttributeSet.xls', sheet_name='Instrument')
measurements_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric/Climate-centric AttributeSet.xls', sheet_name='Measurement')
param_names = []
for row in measurements_sheet.itertuples(index=True, name='Measurement'):
    if row[2] == 'Parameter':
        for i in range(6, len(row)):
            param_names.append(row[i])


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

def analyst_instrument_parameter_list():
    return instruments_sheet['Attributes-for-object-Instrument']


def analyst_instrument_list():
    return ["ACE_ORCA","ACE_POL","ACE_LID","CLAR_ERB","ACE_CPR","DESD_SAR","DESD_LID","GACM_VIS","GACM_SWIR","HYSP_TIR","POSTEPS_IRS","CNES_KaRIN"]


def analyst_measurement_list():
    return param_names


def analyst_stakeholder_list():
    return ["Atmospheric","Oceanic","Terrestrial"]


orbits_info = [
    "<b>Orbit name: Orbit information</b>",
    "LEO-600-polar-NA: Low Earth, Medium Altitude (600 km), Polar",
    "SSO-600-SSO-AM: Low Earth, Sun-synchronous, Medium Altitude (600 km), Morning",
    "SSO-600-SSO-DD: Low Earth, Sun-synchronous, Medium Altitude (600 km), Dawn-Dusk",
    "SSO-800-SSO-DD: Low Earth, Sun-synchronous, High Altitude (600 km), Dawn-Dusk",
    "SSO-800-SSO-PM: Low Earth, Sun-synchronous, High Altitude (600 km), Afternoon"
]


instruments_info = [
    "<b>Instrument name: Instrument technology, Instrument type</b>",
    "ACE_ORCA: Ocean colour instruments, Medium-resolution spectro-radiometer",
    "ACE_POL: Multiple direction/polarisation radiometers, Multi-channel/direction/polarisation radiometer",
    "ACE_LID: Lidars, Atmospheric lidar",
    "CLAR_ERB: Hyperspectral imagers, Multi-purpose imaging Vis/IR radiometer",
    "ACE_CPR: Cloud profile and rain radars, Cloud and precipitation radar",
    "DESD_SAR: Imaging microwave radars, Imaging radar (SAR)",
    "DESD_LID: Lidars, Lidar altimeter",
    "GACM_VIS: Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "GACM_SWIR: Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "HYSP_TIR: Imaging multi-spectral radiometers (vis/IR), Medium-resolution IR spectrometer",
    "POSTEPS_IRS: Atmospheric temperature and humidity sounders, Medium-resolution IR spectrometer",
    "CNES_KaRIN: Radar altimeters, Radar altimeter"
]