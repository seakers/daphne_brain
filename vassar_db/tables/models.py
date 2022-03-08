from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Time, Enum, ForeignKey, Table, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
import os
import pandas as pd

DeclarativeBase = declarative_base()

# --------------------------------> User / Group / Problem
class User(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    password = Column('password', String)

class Group(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Group'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

class Problem(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Problem'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)
def index_problems(dir_path, session):
    print("Indexing problems from:", dir_path)
    problems = os.listdir(dir_path)
    for problem in problems:
        entry = Problem(name=problem)
        session.add(entry)
        session.commit()
    for instance in session.query(Problem):
        print(instance.name, instance.id)




User_Group_Join = Table('User_Group_Join', DeclarativeBase.metadata,
                        Column('user_id', Integer, ForeignKey('User.id')),
                        Column('group_id', Integer, ForeignKey('Group.id')))

Group_Problem_Join = Table('Group_Problem_Join', DeclarativeBase.metadata,
                        Column('group_id', Integer, ForeignKey('Group.id')),
                        Column('problem_id', Integer, ForeignKey('Problem.id')))



# --------------------------------> Instrument
class Instrument(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Instrument'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

Group_Instrument_Join = Table('Group_Instrument_Join', DeclarativeBase.metadata,
                        Column('group_id', Integer, ForeignKey('Group.id')),
                        Column('instrument_id', Integer, ForeignKey('Instrument.id')))







