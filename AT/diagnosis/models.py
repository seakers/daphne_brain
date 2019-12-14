from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Time, Enum, ForeignKey, Table, \
    CheckConstraint
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
    return create_engine(URL(**daphne_brain.settings.ECLSS_DATABASE))


def create_tables(engine):
    """"""
    DeclarativeBase.metadata.create_all(engine)


symptom_to_action = Table('eclss_symptom_to_action', DeclarativeBase.metadata,
                          Column('symptomid', Integer, ForeignKey('eclss_symptoms.id')),
                          Column('actionid', Integer, ForeignKey('eclss_action.id')))
symptom_to_cause = Table('eclss_symptom_to_cause', DeclarativeBase.metadata,
                         Column('symptomid', Integer, ForeignKey('eclss_symptoms.id')),
                         Column('causeid', Integer, ForeignKey('eclss_cause.id')))
symptom_to_component = Table('eclss_symptoms_to_related_components', DeclarativeBase.metadata,
                             Column('symptomid', Integer, ForeignKey('eclss_symptoms.id')),
                             Column('componentsid', Integer, ForeignKey('eclss_related_components.id')))
symptom_to_risk = Table('eclss_symptom_to_risk', DeclarativeBase.metadata,
                        Column('symptomid', Integer, ForeignKey('eclss_symptoms.id')),
                        Column('riskid', Integer, ForeignKey('eclss_risk.id')))


class ECLSSAnomalies(DeclarativeBase):
    """Sqlalchemy symptom description table"""
    __tablename__ = 'eclss_symptoms'
    id = Column(Integer, primary_key=True)
    description = Column('description_of_anomaly', String)


class ECLSSActions(DeclarativeBase):
    """Sqlalchemy actions table"""
    __tablename__ = 'eclss_action'
    id = Column(Integer, primary_key=True)
    description = Column('description_action', String)


class ECLSSCause(DeclarativeBase):
    """Sqlalchemy cause description table"""
    __tablename__ = 'eclss_cause'
    id = Column(Integer, primary_key=True)
    description = Column('cause_of_anomaly', String)


class ECLSSRelatedComponents(DeclarativeBase):
    """Sqlalchemy anomaly related components table"""
    __tablename__ = 'eclss_related_components'
    id = Column(Integer, primary_key=True)
    description = Column('components', String)


class ECLSSRisk(DeclarativeBase):
    """Sqlalchemy risk description table"""
    __tablename__ = 'eclss_risk'
    id = Column(Integer, primary_key=True)
    description = Column('risk', String)
