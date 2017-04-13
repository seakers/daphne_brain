# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table
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
    orbit_LST = Column('orbit_LST', String, nullable=True)
    repeat_cycle = Column('repeat_cycle', String, nullable=True)

    agencies = relationship('Agency', secondary=operators_table, back_populates='missions')


class Instrument(DeclarativeBase):
    """Sqlalchemy instruments model"""
    __tablename__ = 'instruments'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)

    agencies = relationship('Agency', secondary=designers_table, back_populates='instruments')
