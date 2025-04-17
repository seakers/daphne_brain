import os

from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, Boolean, ARRAY, and_, CheckConstraint, DateTime, Time, Table

# user = os.environ['USER']
# password = os.environ['PASSWORD']
# postgres_host = os.environ['POSTGRES_HOST']
# postgres_port = os.environ['POSTGRES_PORT']
user = 'daphneeo'
password = 'daphneeo'
postgres_host = 'localhost'
postgres_port = '5433'
vassar_db_name = 'daphneeo'
db_string = f'postgresql+psycopg2://{user}:{password}@{postgres_host}:{postgres_port}/{vassar_db_name}'
engine = create_engine(db_string, echo=True)
DeclarativeBase = declarative_base(bind=engine)

class Client:

    user = 'daphneeo'
    password = 'daphneeo'
    postgres_host = 'localhost'
    postgres_port = '5433'
    vassar_db_name = 'daphneeo'
    db_string = f'postgresql+psycopg2://{user}:{password}@{postgres_host}:{postgres_port}/{vassar_db_name}'

    def __init__(self):
        self.engine = create_engine(self.db_string, echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        if 'auth_user' not in inspector.get_table_names():
            DeclarativeBase.metadata.create_all(self.engine, checkfirst=True)
            print("Created tables including auth_user")

    def get_session(self):
        return self.session

    # QUERY
    def get_measurement_attribute_id(self, name, group_id=1):
        meas_attrs = self.session.query(Measurement_Attribute.id, Measurement_Attribute.name).filter(Measurement_Attribute.name == name).filter(Measurement_Attribute.group_id == group_id).first()
        meas_attr_id = meas_attrs[0]
        return meas_attr_id

    def get_measurements(self):
        measurements = [row[0] for row in self.session.query(Measurement.name).all()]
        return measurements

    def get_instrument_types(self):
        types = [row[0] for row in self.session.query(InstrumentType.name).all()]
        return types

    def get_missions(self):
        missions = [row[0] for row in self.session.query(Mission.name).all()]
        return missions

    def get_agencies(self):
        agencies = [row[0] for row in self.session.query(Agency.name).all()]
        return agencies

    def get_agencies(self):
        agencies = [row[0] for row in self.session.query(Agency.name).all()]
        return agencies

    def get_stakeholders(self):
        stakeholders = [row[0] for row in self.session.query(Stakeholder_Needs_Panel.name).all()]
        return stakeholders

    def get_objectives(self):
        objectives = [row[0] for row in self.session.query(Stakeholder_Needs_Objective.name).all()]
        return objectives

    def get_subobjectives(self):
        subobjectives = [row[0] for row in self.session.query(Stakeholder_Needs_Subobjective.name).all()]
        return subobjectives

    def get_instrument_attributes(self):
        instr_attributes = [row[0] for row in self.session.query(Instrument_Attribute.name).all()]
        return instr_attributes

    def get_vassar_instruments(self):
        vassar_instruments = [row[0] for row in self.session.query(VassarInstrument.name).all()]
        return vassar_instruments

    def get_vassar_measurements(self):
        vassar_measurements = [row[0] for row in self.session.query(VassarMeasurement.name).all()]
        return vassar_measurements



 #   _____ _       _           _
 #  / ____| |     | |         | |
 # | |  __| | ___ | |__   __ _| |
 # | | |_ | |/ _ \| '_ \ / _` | |
 # | |__| | | (_) | |_) | (_| | |
 #  \_____|_|\___/|_.__/ \__,_|_|

class auth_user(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'auth_user'
    __table_args__ = {'autoload': True}

class Group(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Group'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

class Join__AuthUser_Group(DeclarativeBase):
    __tablename__ = 'Join__AuthUser_Group'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    admin = Column('admin', Boolean, default=False)

class Problem(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Problem'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    reload_problem = Column('reload_problem', Boolean, default=False)

class Join__Problem_VassarInstrument(DeclarativeBase):
    __tablename__ = 'Join__Problem_Instrument'
    id            = Column(Integer, primary_key=True)
    problem_id    = Column('problem_id', Integer, ForeignKey('Problem.id'))
    instrument_id = Column('instrument_id', Integer, ForeignKey('VassarInstrument.id'))

class Join__Problem_Orbit(DeclarativeBase):
    __tablename__ = 'Join__Problem_Orbit'
    id            = Column(Integer, primary_key=True)
    problem_id    = Column('problem_id', Integer, ForeignKey('Problem.id'))
    orbit_id = Column('orbit_id', Integer, ForeignKey('Orbit.id'))

class Join__Problem_Launch_Vehicle(DeclarativeBase):
    __tablename__ = 'Join__Problem_Launch_Vehicle'
    id            = Column(Integer, primary_key=True)
    problem_id    = Column('problem_id', Integer, ForeignKey('Problem.id'))
    launch_vehicle_id = Column('launch_vehicle_id', Integer, ForeignKey('Launch_Vehicle.id'))


class Dataset(DeclarativeBase):
    """Sqlalchemy Dataset model"""
    __tablename__ = 'Dataset'
    id = Column(Integer, primary_key=True)
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id'))
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'), nullable=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'), nullable=True)
    name = Column('name', String)


class Launch_Vehicle(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Launch_Vehicle'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)

class VassarInstrument(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Instrument'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)

class Orbit(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Orbit'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)

class VassarMeasurement(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Measurement'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    synergy_rule = Column('synergy_rule', Boolean, default=False)

class Join__VassarInstrument_VassarMeasurement(DeclarativeBase):
    __tablename__ = 'Join__Instrument_Measurement'
    id            = Column(Integer, primary_key=True)
    measurement_id = Column('measurement_id', Integer, ForeignKey('Measurement.id'))
    instrument_id = Column('instrument_id', Integer, ForeignKey('Instrument.id'))
    problem_id    = Column('problem_id', Integer, ForeignKey('Problem.id'))

class Measurement_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Measurement_Attribute'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    slot_type = Column('slot_type', String)
    type = Column('type', String)

class Join__Measurement_Attribute_Values(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Measurement_Attribute_Values'
    id = Column(Integer, primary_key=True)
    attribute_id = Column('attribute_id', Integer, ForeignKey('Measurement_Attribute.id'))
    value_id = Column('value_id', Integer, ForeignKey('Accepted_Value.id'))

class Instrument_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Instrument_Attribute'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    slot_type = Column('slot_type', String)
    type = Column('type', String)

class Join__Instrument_Attribute_Values(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Instrument_Attribute_Values'
    id = Column(Integer, primary_key=True)
    attribute_id = Column('attribute_id', Integer, ForeignKey('Instrument_Attribute.id'))
    value_id = Column('value_id', Integer, ForeignKey('Accepted_Value.id'))

class Orbit_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Orbit_Attribute'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    slot_type = Column('slot_type', String)
    type = Column('type', String)

class Join__Orbit_Attribute(DeclarativeBase):
    __tablename__ = 'Join__Orbit_Attribute'
    id = Column(Integer, primary_key=True)
    orbit_id = Column('orbit_id', Integer, ForeignKey('Orbit.id')) # nullable
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    orbit_attribute_id = Column('orbit_attribute_id', Integer, ForeignKey('Orbit_Attribute.id'))
    value = Column('value', String, default=False)

class Join__Orbit_Attribute_Values(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Orbit_Attribute_Values'
    id = Column(Integer, primary_key=True)
    attribute_id = Column('attribute_id', Integer, ForeignKey('Orbit_Attribute.id'))
    value_id = Column('value_id', Integer, ForeignKey('Accepted_Value.id'))


class Launch_Vehicle_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Launch_Vehicle_Attribute'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    name = Column('name', String)
    slot_type = Column('slot_type', String)
    type = Column('type', String)

class Join__Launch_Vehicle_Attribute(DeclarativeBase):
    __tablename__ = 'Join__Launch_Vehicle_Attribute'
    id = Column(Integer, primary_key=True)
    value = Column('value', String, default=False)
    launch_vehicle_id = Column('launch_vehicle_id', Integer, ForeignKey('Launch_Vehicle.id')) # nullable
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    launch_vehicle_attribute_id = Column('launch_vehicle_attribute_id', Integer, ForeignKey('Launch_Vehicle_Attribute.id'))

class Join__Launch_Vehicle_Attribute_Values(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Launch_Vehicle_Attribute_Values'
    id = Column(Integer, primary_key=True)
    attribute_id = Column('attribute_id', Integer, ForeignKey('Launch_Vehicle_Attribute.id'))
    value_id = Column('value_id', Integer, ForeignKey('Accepted_Value.id'))

class Mission_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Mission_Attribute'
    id = Column(Integer, primary_key=True)
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id'))
    name = Column('name', String)
    slot_type = Column('slot_type', String)
    type = Column('type', String)

class Join__Mission_Attribute_Values(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Mission_Attribute_Values'
    id = Column(Integer, primary_key=True)
    attribute_id = Column('attribute_id', Integer, ForeignKey('Mission_Attribute.id'))
    value_id = Column('value_id', Integer, ForeignKey('Accepted_Value.id'))

class Inheritence_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Inheritence_Attribute'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    template1 = Column('template1', String)
    copySlotType1 = Column('copySlotType1', String)
    copySlotName1 = Column('copySlotName1', String)
    matchingSlotType1 = Column('matchingSlotType1', String)
    matchingSlotName1 = Column('matchingSlotName1', String)
    template2 = Column('template2', String)
    matchingSlotName2 = Column('matchingSlotName2', String)
    copySlotName2 = Column('copySlotName2', String)
    module = Column('module', String)

class Fuzzy_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Fuzzy_Attribute'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    name = Column('name', String)
    parameter = Column('parameter', String)
    unit = Column('unit', String)

class Fuzzy_Value(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Fuzzy_Value'
    id = Column(Integer, primary_key=True)
    fuzzy_attribute_id = Column(Integer, ForeignKey('Fuzzy_Attribute.id'))
    value = Column('value', String)
    minimum = Column('minimum', Float)
    mean = Column('mean', Float)
    maximum = Column('maximum', Float)

class Accepted_Value(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Accepted_Value'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    value = Column('value', String)

class Architecture(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Architecture'
    id = Column(Integer, primary_key=True)
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id'))
    dataset_id = Column('dataset_id', Integer, ForeignKey('Dataset.id'))
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    input = Column('input', String)
    science = Column('science', Float)
    cost = Column('cost', Float)
    ga = Column('ga', Boolean, default=False)
    improve_hv = Column('improve_hv', Boolean, default=False)
    eval_status = Column('eval_status', Boolean, default=True) # if false, arch needs to be re-evaluated
    critique = Column('critique', String)

class ArchitectureCostInformation(DeclarativeBase):
    __tablename__ = 'ArchitectureCostInformation'
    id = Column(Integer, primary_key=True)
    architecture_id = Column('architecture_id', Integer, ForeignKey('Architecture.id'))
    mission_name = Column('mission_name', String)
    launch_vehicle = Column('launch_vehicle', String)
    mass = Column('mass', Float)
    power = Column('power', Float)
    cost = Column('cost', Float)
    others = Column('others', Float)






# ARCHITECTURE STUFF
class ArchitecturePayload(DeclarativeBase):
    __tablename__ = 'ArchitecturePayload'
    id = Column(Integer, primary_key=True)
    arch_cost_id = Column('arch_cost_id', Integer, ForeignKey('ArchitectureCostInformation.id'))
    instrument_id = Column('instrument_id', Integer, ForeignKey('VassarInstrument.id'))

class ArchitectureBudget(DeclarativeBase):
    __tablename__ = 'ArchitectureBudget'
    id = Column(Integer, primary_key=True)
    mission_attribute_id = Column('mission_attribute_id', Integer, ForeignKey('Mission_Attribute.id'))
    arch_cost_id = Column('arch_cost_id', Integer, ForeignKey('ArchitectureCostInformation.id'))
    value = Column('value', Float)

class ArchitectureScoreExplanation(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'ArchitectureScoreExplanation'
    id = Column(Integer, primary_key=True)
    architecture_id = Column('architecture_id', Integer, ForeignKey('Architecture.id'))
    panel_id = Column('panel_id', Integer, ForeignKey('Stakeholder_Needs_Panel.id'))
    satisfaction = Column('satisfaction', Float)

class PanelScoreExplanation(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'PanelScoreExplanation'
    id = Column(Integer, primary_key=True)
    architecture_id = Column('architecture_id', Integer, ForeignKey('Architecture.id'))
    objective_id = Column('objective_id', Integer, ForeignKey('Stakeholder_Needs_Objective.id'))
    satisfaction = Column('satisfaction', Float)

class ObjectiveScoreExplanation(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'ObjectiveScoreExplanation'
    id = Column(Integer, primary_key=True)
    architecture_id = Column('architecture_id', Integer, ForeignKey('Architecture.id'))
    subobjective_id = Column('subobjective_id', Integer, ForeignKey('Stakeholder_Needs_Subobjective.id'))
    satisfaction = Column('satisfaction', Float)


 #  _                     _
 # | |                   | |
 # | |     ___   ___ __ _| |
 # | |    / _ \ / __/ _` | |
 # | |___| (_) | (_| (_| | |
 # |______\___/ \___\__,_|_|

# measurement attribute values vary across instruments
class Join__VassarInstrument_Capability(DeclarativeBase):
    __tablename__ = 'Join__Instrument_Capability'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    instrument_id = Column('instrument_id', Integer, ForeignKey('Instrument.id')) # nullable
    measurement_id = Column('measurement_id', Integer, ForeignKey('Measurement.id'))
    measurement_attribute_id = Column('measurement_attribute_id', Integer, ForeignKey('Measurement_Attribute.id'))
    requirement_rule_case_id = Column('requirement_rule_case_id', Integer, ForeignKey('Requirement_Rule_Case.id'))
    descriptor = Column('descriptor', String, default=False)
    value = Column('value', String, default=False)

# instrument attribute values vary across problems
class Join__VassarInstrument_Characteristic(DeclarativeBase):
    __tablename__ = 'Join__Instrument_Characteristic'
    id = Column(Integer, primary_key=True)
    group_id = Column('group_id', Integer, ForeignKey('Group.id'))
    instrument_id = Column('instrument_id', Integer, ForeignKey('VassarInstrument.id')) # nullable
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id')) # nullable
    instrument_attribute_id = Column('instrument_attribute_id', Integer, ForeignKey('Instrument_Attribute.id'))
    value = Column('value', String, default=False)



class Requirement_Rule_Attribute(DeclarativeBase):
    __tablename__ = 'Requirement_Rule_Attribute'
    id = Column(Integer, primary_key=True)
    measurement_id = Column('measurement_id', Integer, ForeignKey('Measurement.id'))
    measurement_attribute_id = Column('measurement_attribute_id', Integer, ForeignKey('Measurement_Attribute.id'))
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id'))
    subobjective_id = Column('subobjective_id', Integer, ForeignKey('Stakeholder_Needs_Subobjective.id'))
    type = Column('type', String, default=False)
    thresholds = Column('thresholds', ARRAY(String))
    scores = Column('scores', ARRAY(Float))
    justification = Column('justification', String, default=False)










class Stakeholder_Needs_Panel(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Stakeholder_Needs_Panel'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    name = Column('name', String)
    description = Column('description', String)
    weight = Column('weight', Float)
    index_id = Column('index_id', String, nullable=True)

class Stakeholder_Needs_Objective(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Stakeholder_Needs_Objective'
    id = Column(Integer, primary_key=True)
    panel_id = Column(Integer, ForeignKey('Stakeholder_Needs_Panel.id'))
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    name = Column('name', String)
    description = Column('description', String)
    weight = Column('weight', Float)

class Stakeholder_Needs_Subobjective(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Stakeholder_Needs_Subobjective'
    id = Column(Integer, primary_key=True)
    objective_id = Column(Integer, ForeignKey('Stakeholder_Needs_Objective.id'))
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    name = Column('name', String)
    description = Column('description', String)
    weight = Column('weight', Float)







class Requirement_Rule_Case(DeclarativeBase):
    __tablename__ = 'Requirement_Rule_Case'
    id = Column(Integer, primary_key=True)
    # FK
    problem_id = Column('problem_id', Integer, ForeignKey('Problem.id'))  # nullable
    objective_id = Column(Integer, ForeignKey('Stakeholder_Needs_Objective.id'))
    subobjective_id = Column('subobjective_id', Integer, ForeignKey('Stakeholder_Needs_Subobjective.id'))
    measurement_id = Column('measurement_id', Integer, ForeignKey('Measurement.id'))
    # Fields
    rule = Column('rule', String, default=False)
    value = Column('value', String, default=False)
    text = Column('text', String, default=False)
    description = Column('description', String, default=False)



class Join__Case_Attribute(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__Case_Attribute'
    id = Column(Integer, primary_key=True)
    # FK1
    rule_id = Column(Integer, ForeignKey('Requirement_Rule_Case.id'))
    measurement_attribute_id = Column(Integer, ForeignKey('Measurement_Attribute.id'))
    # Fields
    operation = Column('operation', String, nullable=True)
    value = Column('value', String)

class Walker_Mission_Analysis(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Walker_Mission_Analysis'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))
    sats_per_plane = Column('sats_per_plane', Float)
    num_planes = Column('num_planes', Float)
    orbit_altitude = Column('orbit_altitude', Float)
    orbit_inclination = Column('orbit_inclination', String)
    instrument_fov = Column('instrument_fov', Float)
    avg_revisit_time_global = Column('avg_revisit_time_global', Float)
    avg_revisit_time_tropics = Column('avg_revisit_time_tropics', Float)
    avg_revisit_time_northern_hemisphere = Column('avg_revisit_time_northern_hemisphere', Float)
    avg_revisit_time_southern_hemisphere = Column('avg_revisit_time_southern_hemisphere', Float)
    avg_revisit_time_cold_regions = Column('avg_revisit_time_cold_regiouis', Float)
    avg_revisit_time_us = Column('avg_revisit_time_us', Float)
    mission_architecture = Column('mission_architecture', String)

class Launch_Vehicle_Mission_Analysis(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Launch_Vehicle_Mission_Analysis'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))


    vehicle_id = Column('vehicle_id', String)

    payload_geo = Column('payload_geo', ARRAY(Float))

    diameter = Column('diameter', Float)

    height = Column('height', Float)

    payload_leo_polar = Column('payload_leo_polar', ARRAY(Float))

    payload_sso = Column('payload_sso', ARRAY(Float))

    payload_leo_equat = Column('payload_leo_equat', ARRAY(Float))

    payload_meo = Column('payload_meo', ARRAY(Float))

    payload_heo = Column('payload_heo', ARRAY(Float))

    payload_iss = Column('payload_iss', ARRAY(Float))

    cost = Column('cost', Float)

class Power_Mission_Analysis(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Power_Mission_Analysis'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('Problem.id'))

    orbit_id = Column('orbit_id', String)
    orbit_type = Column('orbit_type', String)
    altitude = Column('altitude', Float)
    inclination = Column('inclination', Float)
    RAAN = Column('RAAN', String)
    fraction_of_sunlight = Column('fraction_of_sunlight', String)
    period = Column('period', Float)
    worst_sun_angles = Column('worst_sun_angles', Float)
    max_eclipse_time = Column('max_eclipse_time', Float)


### CEOS TABLES

operators_table = Table('ceos_operators', DeclarativeBase.metadata,
                        Column('agency_id', Integer, ForeignKey('ceos_agencies.id')),
                        Column('mission_id', Integer, ForeignKey('ceos_missions.id')))

designers_table = Table('ceos_designers', DeclarativeBase.metadata,
                        Column('agency_id', Integer, ForeignKey('ceos_agencies.id')),
                        Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')))

type_of_instrument_table = Table('ceos_type_of_instrument', DeclarativeBase.metadata,
                                 Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')),
                                 Column('instrument_type_id', Integer, ForeignKey('ceos_instrument_types.id')))

geometry_of_instrument_table = Table('ceos_geometry_of_instrument', DeclarativeBase.metadata,
                                     Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')),
                                     Column('instrument_geometry_id', Integer, ForeignKey('ceos_geometry_types.id')))

instruments_in_mission_table = Table('ceos_instruments_in_mission', DeclarativeBase.metadata,
                                     Column('mission_id', Integer, ForeignKey('ceos_missions.id')),
                                     Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')))

measurements_of_instrument_table = Table('ceos_measurements_of_instrument', DeclarativeBase.metadata,
                                         Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')),
                                         Column('measurement_id', Integer, ForeignKey('ceos_measurements.id')))

instrument_wavebands_table = Table('ceos_instrument_wavebands', DeclarativeBase.metadata,
                                   Column('instrument_id', Integer, ForeignKey('ceos_instruments.id')),
                                   Column('waveband_id', Integer, ForeignKey('ceos_wavebands.id')))

technologies = ('Absorption-band MW radiometer/spectrometer', 'Atmospheric lidar', 'Broad-band radiometer',
                'Cloud and precipitation radar', 'Communications system', 'Data collection system',
                'Doppler lidar', 'Electric field sensor', 'GNSS radio-occultation receiver',
                'GNSS receiver', 'Gradiometer/accelerometer', 'High resolution optical imager',
                'High-resolution nadir-scanning IR spectrometer',
                'High-resolution nadir-scanning SW spectrometer', 'Imaging radar (SAR)',
                'Laser retroreflector', 'Lidar altimeter', 'Lightning imager',
                'Limb-scanning IR spectrometer', 'Limb-scanning MW spectrometer',
                'Limb-scanning SW spectrometer', 'Magnetometer', 'Medium-resolution IR spectrometer',
                'Medium-resolution spectro-radiometer', 'Multi-channel/direction/polarisation radiometer',
                'Multi-purpose imaging MW radiometer', 'Multi-purpose imaging Vis/IR radiometer',
                'Narrow-band channel IR radiometer', 'Non-scanning MW radiometer', 'Radar altimeter',
                'Radar scatterometer', 'Radio-positioning system', 'Satellite-to-satellite ranging system',
                'Solar irradiance monitor', 'Space environment monitor', 'Star tracker')


class BroadMeasurementCategory(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'ceos_broad_measurement_categories'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    measurement_categories = relationship('MeasurementCategory', back_populates='broad_measurement_category')


class MeasurementCategory(DeclarativeBase):
    """Sqlalchemy measurement categories model"""
    __tablename__ = 'ceos_measurement_categories'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    broad_measurement_category_id = Column(Integer, ForeignKey('ceos_broad_measurement_categories.id'))
    broad_measurement_category = relationship('BroadMeasurementCategory', back_populates='measurement_categories')
    measurements = relationship('Measurement', back_populates='measurement_category')


class Measurement(DeclarativeBase):
    """Sqlalchemy measurements model"""
    __tablename__ = 'ceos_measurements'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    measurement_category_id = Column(Integer, ForeignKey('ceos_measurement_categories.id'))
    measurement_category = relationship('MeasurementCategory', back_populates='measurements')
    instruments = relationship('Instrument', secondary=measurements_of_instrument_table, back_populates='measurements')


class Agency(DeclarativeBase):
    """Sqlalchemy agencies model"""
    __tablename__ = 'ceos_agencies'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    country = Column('country', String)
    website = Column('website', String)

    missions = relationship('Mission', secondary=operators_table, back_populates='agencies')
    instruments = relationship('Instrument', secondary=designers_table, back_populates='agencies')


class Mission(DeclarativeBase):
    """Sqlalchemy missions model"""
    __tablename__ = 'ceos_missions'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)
    status = Column('status', String)
    launch_date = Column('launch_date', DateTime, nullable=True)
    eol_date = Column('eol_date', DateTime, nullable=True)
    applications = Column('applications', String)
    orbit_type = Column('orbit_type', String, nullable=True)
    orbit_period = Column('orbit_period', String, nullable=True)
    orbit_sense = Column('orbit_sense', String, nullable=True)
    orbit_inclination = Column('orbit_inclination', String, nullable=True)
    orbit_inclination_num = Column('orbit_inclination_num', Float, nullable=True)
    orbit_inclination_class = Column('orbit_inclination_class', String, CheckConstraint(
        "orbit_inclination_class IN ('Equatorial', 'Near Equatorial', 'Mid Latitude', 'Near Polar', 'Polar')"),
                                     nullable=True)
    orbit_altitude = Column('orbit_altitude', String, nullable=True)
    orbit_altitude_num = Column('orbit_altitude_num', Integer, nullable=True)
    orbit_altitude_class = Column('orbit_altitude_class', String, CheckConstraint(
        "orbit_altitude_class IN ('VL', 'L', 'M', 'H', 'VH')"), nullable=True)
    orbit_longitude = Column('orbit_longitude', String, nullable=True)
    orbit_LST = Column('orbit_lst', String, nullable=True)
    orbit_LST_time = Column('orbit_lst_time', Time, nullable=True)
    orbit_LST_class = Column('orbit_lst_class', String, CheckConstraint(
        "orbit_lst_class IN ('DD', 'AM', 'Noon', 'PM')"), nullable=True)
    repeat_cycle = Column('repeat_cycle', String, nullable=True)
    repeat_cycle_num = Column('repeat_cycle_num', Float, nullable=True)
    repeat_cycle_class = Column('repeat_cycle_class', String, CheckConstraint(
        "repeat_cycle_class IN ('Long', 'Short')"), nullable=True)

    agencies = relationship('Agency', secondary=operators_table, back_populates='missions')
    instruments = relationship('Instrument', secondary=instruments_in_mission_table, back_populates='missions')


class InstrumentType(DeclarativeBase):
    """Sqlalchemy instrument types model"""
    __tablename__ = 'ceos_instrument_types'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    instruments = relationship('Instrument', secondary=type_of_instrument_table, back_populates='types')


class GeometryType(DeclarativeBase):
    """Sqlalchemy geometry types model"""
    __tablename__ = 'ceos_geometry_types'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    instruments = relationship('Instrument', secondary=geometry_of_instrument_table, back_populates='geometries')


class Waveband(DeclarativeBase):
    """Sqlalchemy wavebands model"""
    __tablename__ = 'ceos_wavebands'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    wavelengths = Column('wavelengths', String, nullable=True)

    instruments = relationship('Instrument', secondary=instrument_wavebands_table, back_populates='wavebands')


class Instrument(DeclarativeBase):
    """Sqlalchemy instruments model"""
    __tablename__ = 'ceos_instruments'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)
    status = Column('status', String)
    maturity = Column('maturity', String, nullable=True)
    technology = Column('technology', String, CheckConstraint("technology IN ('" + "', '".join(technologies) + "')"),
                        nullable=True)
    sampling = Column('sampling', String, CheckConstraint("sampling IN ('Imaging', 'Sounding', 'Other', 'TBD')"))
    data_access = Column('data_access', String, CheckConstraint(
        "data_access IN ('Open Access', 'Constrained Access', 'Very Constrained Access', 'No Access')"), nullable=True)
    data_format = Column('data_format', String, nullable=True)
    measurements_and_applications = Column('measurements_and_applications', String, nullable=True)
    resolution_summary = Column('resolution_summary', String, nullable=True)
    best_resolution = Column('best_resolution', String, nullable=True)
    swath_summary = Column('swath_summary', String, nullable=True)
    max_swath = Column('max_swath', String, nullable=True)
    accuracy_summary = Column('accuracy_summary', String, nullable=True)
    waveband_summary = Column('waveband_summary', String, nullable=True)

    agencies = relationship('Agency', secondary=designers_table, back_populates='instruments')
    types = relationship('InstrumentType', secondary=type_of_instrument_table, back_populates='instruments')
    geometries = relationship('GeometryType', secondary=geometry_of_instrument_table, back_populates='instruments')
    missions = relationship('Mission', secondary=instruments_in_mission_table, back_populates='instruments')
    measurements = relationship('Measurement', secondary=measurements_of_instrument_table, back_populates='instruments')
    wavebands = relationship('Waveband', secondary=instrument_wavebands_table, back_populates='instruments')


class TechTypeMostCommonOrbit(DeclarativeBase):
    """Sqlalchemy TechTypeMostCommonOrbit model"""
    __tablename__ = 'ceos_techtype_most_common_orbits'

    id = Column(Integer, primary_key=True)
    techtype = Column('techype', String)
    orbit = Column('orbit', String, nullable=True)


class MeasurementMostCommonOrbit(DeclarativeBase):
    """Sqlalchemy MeasurementMostCommonOrbit model"""
    __tablename__ = 'ceos_measurement_most_common_orbits'

    id = Column(Integer, primary_key=True)
    measurement = Column('measurement', String)
    orbit = Column('orbit', String, nullable=True)
