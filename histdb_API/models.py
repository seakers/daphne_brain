# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

import daphne_brain.settings

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(URL(**daphne_brain.settings.ALCHEMY_DATABASE))


def create_tables(engine):
    """"""
    DeclarativeBase.metadata.create_all(engine)

operators_table = Table('operators', DeclarativeBase.metadata,
                        Column('agency_id', Integer, ForeignKey('agencies.id')),
                        Column('mission_id', Integer, ForeignKey('missions.id')))

designers_table = Table('designers', DeclarativeBase.metadata,
                        Column('agency_id', Integer, ForeignKey('agencies.id')),
                        Column('instrument_id', Integer, ForeignKey('instruments.id')))

type_of_instrument_table = Table('type_of_instrument', DeclarativeBase.metadata,
                                 Column('instrument_id', Integer, ForeignKey('instruments.id')),
                                 Column('instrument_type_id', Integer, ForeignKey('instrument_types.id')))

geometry_of_instrument_table = Table('geometry_of_instrument', DeclarativeBase.metadata,
                                     Column('instrument_id', Integer, ForeignKey('instruments.id')),
                                     Column('instrument_geometry_id', Integer, ForeignKey('geometry_types.id')))

instruments_in_mission_table = Table('instruments_in_mission', DeclarativeBase.metadata,
                                     Column('mission_id', Integer, ForeignKey('missions.id')),
                                     Column('instrument_id', Integer, ForeignKey('instruments.id')))

measurements_of_instrument_table = Table('measurements_of_instrument', DeclarativeBase.metadata,
                                         Column('instrument_id', Integer, ForeignKey('instruments.id')),
                                         Column('measurement_id', Integer, ForeignKey('measurements.id')))

instrument_wavebands_table = Table('instrument_wavebands', DeclarativeBase.metadata,
                                     Column('instrument_id', Integer, ForeignKey('instruments.id')),
                                     Column('waveband_id', Integer, ForeignKey('wavebands.id')))

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
    __tablename__ = 'broad_measurement_categories'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    measurement_categories = relationship('MeasurementCategory', back_populates='broad_measurement_category')


class MeasurementCategory(DeclarativeBase):
    """Sqlalchemy measurement categories model"""
    __tablename__ = 'measurement_categories'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    broad_measurement_category_id = Column(Integer, ForeignKey('broad_measurement_categories.id'))
    broad_measurement_category = relationship('BroadMeasurementCategory', back_populates='measurement_categories')
    measurements = relationship('Measurement', back_populates='measurement_category')


class Measurement(DeclarativeBase):
    """Sqlalchemy measurements model"""
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', String)
    measurement_category_id = Column(Integer, ForeignKey('measurement_categories.id'))
    measurement_category = relationship('MeasurementCategory', back_populates='measurements')
    instruments = relationship('Instrument', secondary=measurements_of_instrument_table, back_populates='measurements')


class Agency(DeclarativeBase):
    """Sqlalchemy agencies model"""
    __tablename__ = 'agencies'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    country = Column('country', String)
    website = Column('website', String)

    missions = relationship('Mission', secondary=operators_table, back_populates='agencies')
    instruments = relationship('Instrument', secondary=designers_table, back_populates='agencies')


class Mission(DeclarativeBase):
    """Sqlalchemy missions model"""
    __tablename__ = 'missions'

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
    orbit_altitude = Column('orbit_altitude', String, nullable=True)
    orbit_longitude = Column('orbit_longitude', String, nullable=True)
    orbit_LST = Column('orbit_lst', String, nullable=True)
    repeat_cycle = Column('repeat_cycle', String, nullable=True)

    agencies = relationship('Agency', secondary=operators_table, back_populates='missions')
    instruments = relationship('Instrument', secondary=instruments_in_mission_table, back_populates='missions')


class InstrumentType(DeclarativeBase):
    """Sqlalchemy instrument types model"""
    __tablename__ = 'instrument_types'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    instruments = relationship('Instrument', secondary=type_of_instrument_table, back_populates='types')


class GeometryType(DeclarativeBase):
    """Sqlalchemy geometry types model"""
    __tablename__ = 'geometry_types'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)

    instruments = relationship('Instrument', secondary=geometry_of_instrument_table, back_populates='geometries')

class Waveband(DeclarativeBase):
    """Sqlalchemy wavebands model"""
    __tablename__ = 'wavebands'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    wavelengths = Column('wavelengths', String, nullable=True)

    instruments = relationship('Instrument', secondary=instrument_wavebands_table, back_populates='wavebands')

class Instrument(DeclarativeBase):
    """Sqlalchemy instruments model"""
    __tablename__ = 'instruments'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)
    status = Column('status', String)
    maturity = Column('maturity', String, nullable=True)
    technology = Column('technology', Enum(*technologies, name='technologies'), nullable=True)
    sampling = Column('sampling', Enum('Imaging', 'Sounding', 'Other', 'TBD', name='sampling_values'))
    data_access = Column('data_access', Enum('Open Access', 'Constrained Access', 'Very Constrained Access',
                                             'No Access', name='data_access_values'), nullable=True)
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
