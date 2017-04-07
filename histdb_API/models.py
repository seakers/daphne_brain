from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
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


class Agency(DeclarativeBase):
    """Sqlalchemy agencies model"""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    country = Column('country', String)
    website = Column('website', String)

    missions = relationship("Mission", back_populates='agency', cascade="all, delete-orphan")


class Mission(DeclarativeBase):
    """Sqlalchemy missions model"""
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    full_name = Column('full_name', String, nullable=True)
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    status = Column('status', String)
    launch_date = Column('launch_date', DateTime, nullable=True)
    eol_date = Column('eol_date', DateTime, nullable=True)
    applications = Column('applications', String)
    orbit_details = Column('orbit_details', String)

    agency = relationship("Agency", back_populates="missions")