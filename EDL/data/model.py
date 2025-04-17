from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Time, Enum, ForeignKey, Table, \
    CheckConstraint, ARRAY
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

import daphne_brain.settings as settings

# Import pandas
import pandas
import pandas as pd

# https://stackoverflow.com/questions/44395499/joining-pandas-dataframe-with-sql-table-for-efficient-select-statement


# Define Table
DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(URL(**settings.EDL_DATABASE))  # connection and configuration is assembled


def create_tables(engine):
    """"""
    DeclarativeBase.metadata.create_all(
        engine)  # passses in our engine as a source of database connectivity. MetaData emits schema generation commands to the database


####################################################################################################################

class Entry(DeclarativeBase):
    """SQLalchemy entry model"""
    __tablename__ = 'entry'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    entry_strategy = Column('entry_strategy', String, CheckConstraint("entry_strategy IN('Guided', 'Unguided')"))
    entry_form = Column('entry_form', String, CheckConstraint("entry_form IN ('Orbit', 'Direct')"))
    entry_interfaceX = Column('entry_interfacex', Float, nullable=True)
    entry_interfaceY = Column('entry_interfacey', Float, nullable=True)
    entry_interfaceZ = Column('entry_interfacez', Float, nullable=True)
    orbital_direction = Column('orbital_direction', String,
                               CheckConstraint("orbital_direction IN ('Posigrade', 'Retrograde')"))
    entry_vehicle = Column('entry_vehicle', String,
                           CheckConstraint("entry_vehicle IN ('Capsule', 'Lifting body', 'Aerobot')"))
    entry_velocity = Column('entry_velocity', Float)
    entry_velocity_unit = Column('entry_velocity_unit', String,
                                 CheckConstraint("entry_velocity_unit IN ('km/s', 'ft/s')"))
    entry_lift_control = Column('entry_lift_control', String,
                                CheckConstraint("entry_lift_control IN ('CM offset','No offset')"))
    entry_attitude_control = Column('entry_attitude_control', String,
                                    CheckConstraint("entry_attitude_control IN ('3-axis RCS','2 RPM passive')"))
    entry_guidance = Column('entry_guidance', String, CheckConstraint("entry_guidance IN ('Apollo','Unguided')"))
    entry_angle_of_attack = Column('entry_angle_of_attack', Float)
    entry_angle_of_attack_unit = Column('entry_angle_of_attack_unit', String,
                                        CheckConstraint("entry_angle_of_attack_unit IN ('deg','rad')"))
    ballistic_coefficient = Column('ballistic_coefficient', Float)
    ballistic_coefficient_unit = Column('ballistic_coefficient_unit', String,
                                        CheckConstraint("ballistic_coefficient_unit IN ('kg/m^2')"))
    ld_ratio = Column('ld_ratio', Float)
    peak_deceleration = Column('peak_deceleration', Float)
    peak_deceleration_unit = Column('peak_deceleration_unit', String,
                                    CheckConstraint("peak_deceleration_unit IN ('G', 'km/s^2','ft/s^2')"))
    missions = relationship('Mission', back_populates='entry')  # link to mission


#######################################################################################################################

class ParachuteDescent(DeclarativeBase):
    "SQLalchemy model for parachute"
    __tablename__ = 'parachute_descent'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    missions = relationship('Mission',
                            back_populates='parachute_descent')  # "parachute deploy tiene un field llamado parachute que se relationa con parachute deploy, (relationship is bidirectionl)"

    descent_attitude_control = Column('descent_attitude_control', String,
                                      CheckConstraint(
                                          "descent_attitude_control IN ('RCS Roll Rate','RCS Rate','None')"))

    parachute_deploy_id = Column(Integer, ForeignKey('parachute_deploy_cond.id'))
    parachute_deploy_cond = relationship('ParachuteDeployConditions', back_populates='parachute_descent')

    sensing_id = Column(Integer, ForeignKey('descent_sensing.id'))
    descent_sensing = relationship('ParachuteDescentSensing', back_populates='parachute_descent')

    heat_shield_id = Column(Integer, ForeignKey('heat_shield.id'))
    heat_shield = relationship('HeatShield', back_populates='parachute_descent')

    backshell_separation_id = Column(Integer, ForeignKey('backshell_separation.id'))
    backshell_separation = relationship('BackshellSeparation', back_populates='parachute_descent')


class ParachuteDeployConditions(DeclarativeBase):
    """SQLAlchemy parachute deploy model"""
    __tablename__ = 'parachute_deploy_cond'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    parachute_descent = relationship('ParachuteDescent',
                                     back_populates='parachute_deploy_cond')  # link to parachute descent

    drag_coeff = Column('drag_coeff', Float)
    deploy_mach_no = Column('deploy_mach_no', Float)
    deploy_dyn_pressure = Column('deploy_dyn_pressure', Integer)
    deploy_dyn_pressure_unit = Column('deploy_dyn_pressure_unit', String,
                                      CheckConstraint("deploy_dyn_pressure_unit IN ('Pa', 'psi')"))
    wind_rel_velocity = Column('wind_rel_velocity', Float, nullable=True)
    wind_rel_velocity_unit = Column('wind_rel_velocity_unit', String,
                                    CheckConstraint("wind_rel_velocity_unit IN ('km/s', 'm/s', 'ft/s')"))
    altitude_deploy = Column('altitude_deploy', Integer)
    altitude_deploy_unit = Column('altitude_deploy_unit', String,
                                  CheckConstraint("altitude_deploy_unit IN ('km', 'ft')"))


class ParachuteDescentSensing(DeclarativeBase):
    """SQLAlchemy parachute deploy model"""
    __tablename__ = 'descent_sensing'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    parachute_descent = relationship('ParachuteDescent',
                                     back_populates='descent_sensing')  # link to parachute descent

    horizontal_velocity_sensing = Column('horizontal_velocity_sensing', String,
                                         CheckConstraint("horizontal_velocity_sensing IN ('Doppler RADAR', 'None',"
                                                         " 'Imaging/IMU')"))
    altitude_sensing = Column('altitude_sensing', String, CheckConstraint("altitude_sensing IN ('RADAR', 'None')"))


class HeatShield(DeclarativeBase):
    __tablename__ = 'heat_shield'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    parachute_descent = relationship('ParachuteDescent',
                                     back_populates='heat_shield')  # link to parachute descent

    hs_geometry = Column('hs_geometry', String, CheckConstraint("hs_geometry IN ('70 deg cone')"))
    hs_diameter = Column('hs_diameter', Float)
    hs_diameter_unit = Column('hs_diameter_unit', String, CheckConstraint("hs_diameter_unit IN ('in','cm','m')"))
    hs_tps = Column('hs_tps', String, CheckConstraint("hs_tps IN ('SLA-561')"))
    hs_thickness = Column('hs_thickness', Float)
    hs_thickness_unit = Column('hs_thickness_unit', String, CheckConstraint("hs_thickness_unit IN ('in','cm','m')"))
    hs_total_integrated_heating = Column('hs_total_integrated_heating', Integer)
    hs_total_integrated_heating_unit = Column('hs_total_integrated_heating_unit', String,
                                              CheckConstraint("hs_total_integrated_heating_unit IN ('J/m^2')"))
    hs_peak_heat_rate = Column('hs_peak_heat_rate', Integer)
    hs_peak_heat_rate_unit = Column('hs_peak_heata_rate_unit', String,
                                    CheckConstraint("hs_peak_heata_rate_unit IN ('W/m^2')"))
    hs_peak_stagnation_pressure = Column('hs_peak_stagnation_pressure', Integer)
    hs_peak_stagnation_pressure_unit = Column('hs_peak_stagnation_pressure_unit', String,
                                              CheckConstraint("hs_peak_stagnation_pressure_unit IN ('Pa','psi')"))


class BackshellSeparation(DeclarativeBase):
    __tablename__ = 'backshell_separation'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    parachute_descent = relationship('ParachuteDescent',
                                     back_populates='backshell_separation')  # link to parachute descent

    bs_separation_altitude = Column('bs_separation_altitude', Float)
    bs_separation_altitude_unit = Column('bs_separation_altitude_unit', String,
                                         CheckConstraint("bs_separation_altitude_unit IN ('in','cm','km','m')"))
    bs_separation_velocity = Column('bs_separation_velocity', Float)
    bs_separation_velocity_unit = Column('bs_separation_velocity_unit', String,
                                         CheckConstraint("bs_separation_velocity_unit IN ('in/s','cm/s','km/s','m/s')"))
    bs_separation_mechanism = Column('bs_separation_mechanism', String,
                                     CheckConstraint("bs_separation_mechanism IN ('Pyros', 'None')"))


######################################################################################################################

class PoweredDescent(DeclarativeBase):
    """SQLAlchemy powered descent model"""
    __tablename__ = 'powered_descent'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    missions = relationship('Mission', back_populates='powered_descent')
    horizontal_velocity_control = Column('horizontal_velocity_control', String,
                                         CheckConstraint("horizontal_velocity_control IN ('Throttled Pitch', "
                                                         "'Lateral SRMs', 'Passive')"))
    terminal_descent_decelerator = Column('terminal_descent_decelerator', String,
                                          CheckConstraint("terminal_descent_decelerator IN ('Mono-prop N2H4', "
                                                          "'Solid Rockets', 'None')"))
    terminal_descent_velocity_control = Column('terminal_descent_velocity_control', String,
                                               CheckConstraint("terminal_descent_velocity_control IN ('Throttled', "
                                                               "'Sep. Cutoff', 'Duty Cycle Pulse')"))
    vertical_descent_rate = Column('vertical_descent_rate', Float)
    fuel_burn = Column('fuel_burn', Float)


#######################################################################################################################

class Touchdown(DeclarativeBase):
    """SQLalchemy landing model"""
    __tablename__ = 'touchdown'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    missions = relationship('Mission', back_populates='touchdown')

    touchdown_vertical_velocity = Column('touchdown_vertical_velocity', Float)
    touchdown_vertical_velocity_unit = Column('touchdown_vertical_velocity_unit', String,
                                              CheckConstraint(
                                                  "touchdown_vertical_velocity_unit IN ('in/s','cm/s','km/s','m/s')"))
    touchdown_horizontal_velocity = Column('touchdown_horizontal_velocity', Float)
    touchdown_horizontal_velocity_unit = Column('touchdown_horizontal_velocity_unit', String,
                                                CheckConstraint(
                                                    "touchdown_horizontal_velocity_unit IN ('in/s','cm/s','km/s','m/s')"))
    touchdown_attenuation = Column('touchdown_attenuation', String,
                                   CheckConstraint(
                                       "touchdown_attenuation IN ('Crushable legs', '4-pi airbag', 'Wheels')"))

    touchdown_rock_height_capability = Column('touchdown_rock_height_capability', Float)
    touchdown_rock_height_capability_unit = Column('touchdown_rock_height_capability_unit', String,
                                                   CheckConstraint(
                                                       "touchdown_rock_height_capability_unit IN ('in','cm','km','m')"))
    touchdown_slope_capability = Column('touchdown_slope_capability', Float)
    touchdown_slope_capability_unit = Column('touchdown_slope_capability_unit', String,
                                             CheckConstraint(
                                                 "touchdown_slope_capability_unit IN ('deg','rad')"))
    touchdown_sensor = Column('touchdown_sensor', String,
                              CheckConstraint(
                                  "touchdown_sensor IN ('None', 'Accelerometer', 'Clock', 'Hall Effect', 'Throttle Down')"))
    touchdown_sensing = Column('touchdown_sensing', String,
                               CheckConstraint(
                                   "touchdown_sensing IN ('None', 'Leg crush motion', 'Roll stop', 'Time out', 'Off load')"))
    threesig_landed_ellipse_major_axis = Column('three-sig_landed_ellipse_major_axis', Float)
    threesig_landed_ellipse_minor_axis = Column('three-sig_landed_ellipse_minor_axis', Float)
    maneuver = Column('maneuver', String, CheckConstraint("maneuver IN ('Skycrane', 'None')"))


class Mission(DeclarativeBase):
    """SQLalchemy missions model"""
    __tablename__ = 'missions'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)
    status = Column('status', String)
    launch_date = Column('launch_date', Integer)
    launch_vehicle = Column('launch_vehicle', String)
    applications = Column('applications', String, nullable=True)
    entry_mass = Column('entry_mass', Integer)
    entry_mass_unit = Column('entry_mass_unit', String, CheckConstraint("entry_mass_unit IN('kg','lb')"), nullable=True)
    touchdown_mass = Column('touchdown_mass', Integer)
    touchdown_mass_unit = Column('touchdown_mass_unit', String, CheckConstraint("touchdown_mass_unit IN('kg','lb')"),
                                 nullable=True)
    useful_landed_mass = Column('useful_landed_mass', Integer)
    useful_landed_mass_unit = Column('useful_landed_mass_unit', String,
                                     CheckConstraint("useful_landed_mass_unit IN('kg','lb')"), nullable=True)
    landing_site = Column('landing_site', String)
    landing_site_elevation = Column('landing_site_elevation', Float)
    landing_site_elevation_unit = Column('landing_site_elevation_unit', String,
                                         CheckConstraint("landing_site_elevation_unit IN('km','ft')"), nullable=True)

    entry_id = Column(Integer, ForeignKey('entry.id'))  # connects to a foreign table "segment"
    entry = relationship('Entry', back_populates="missions")

    parachute_descent_id = Column(Integer, ForeignKey('parachute_descent.id'))
    parachute_descent = relationship('ParachuteDescent', back_populates='missions')

    powered_descent_id = Column(Integer, ForeignKey('powered_descent.id'))
    powered_descent = relationship('PoweredDescent', back_populates='missions')

    touchdown_id = Column(Integer, ForeignKey('touchdown.id'))
    touchdown = relationship('Touchdown', back_populates='missions')

    #
    #
    #

    simulation_data = Column('simulation_data', String)

