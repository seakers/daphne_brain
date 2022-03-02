import os

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Time, Enum, ForeignKey, Table, CheckConstraint, Boolean, ARRAY, and_
import pandas as pd
from datetime import datetime

from client.base import DeclarativeBase


class Client:

    user = os.environ['USER']
    password = os.environ['PASSWORD']
    postgres_host = os.environ['POSTGRES_HOST']
    postgres_port = os.environ['POSTGRES_PORT']
    vassar_db_name = 'daphne'
    db_string = f'postgresql+psycopg2://{user}:{password}@{postgres_host}:{postgres_port}/{vassar_db_name}'

    def __init__(self):
        self.engine = create_engine(self.db_string, echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def initialize(self):
        self.drop_tables()
        self.create_tables()

    def get_session(self):
        return self.session

    def create_tables(self):
        DeclarativeBase.metadata.create_all(self.engine)

    # DELETE ALL TABLES BUT: auth_user
    def drop_tables(self):
        to_delete = []
        for table, table_obj in DeclarativeBase.metadata.tables.items():
            print(table, '\n')
            if table not in ['auth_user', 'Join__AuthUser_Group', 'Group']:
                to_delete.append(table_obj)
        DeclarativeBase.metadata.drop_all(self.engine, to_delete)


    def get_users(self):
        users = self.session.query(auth_user.id, auth_user.username).all()
        return users

    def get_topic_id(self, name):
        topics = self.session.query(Topic.id, Topic.name).filter(Topic.name == name).first()
        if topics is None:
            return self.index_topic(name)
        topic_id = topics[0]
        return topic_id



    def index_excel_exercise(self, name):
        entry = ExcelExercise(name=name)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_excel_exercise_completion(self, user_id, exercise_id, is_completed, reason):
        entry = ExcelExerciseCompletion(user_id=user_id, exercise_id=exercise_id, is_completed=is_completed, reason=reason)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_topic(self, name):
        entry = Topic(name=name)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_ability_parameter(self, user_id, topic_id, value):
        entry = AbilityParameter(user_id=user_id, topic_id=topic_id, value=value)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_learning_module(self, name, icon, topics, course=None):
        entry = LearningModule(name=name, icon=icon, course=course)
        self.session.add(entry)
        self.session.commit()
        module_id = entry.id
        for topic in topics:
            topic_id = self.get_topic_id(topic)
            join_entry = Join__LearningModule_Topic(topic_id=topic_id, module_id=entry.id)
            self.session.add(join_entry)
            self.session.commit()
        return module_id

    def index_question(self, text, choices, difficulty, discrimination, guessing, topics, explanation):
        entry = Question(text=text, choices=choices, difficulty=difficulty, discrimination=discrimination, guessing=guessing, explanation=explanation)
        self.session.add(entry)
        self.session.commit()
        for topic in topics:
            topic_id = self.get_topic_id(topic)
            join_entry = Join__Question_Topic(topic_id=topic_id, question_id=entry.id)
            self.session.add(join_entry)
            self.session.commit()
        return entry.id

    def index_join_user_learning_module(self, user_id, module_id, slide_idx):
        entry = Join__User_LearningModule(user_id=user_id, module_id=module_id, slide_idx=slide_idx)
        self.session.add(entry)
        self.session.commit()
        return entry.id


    def index_info_slide(self, module_id, type, src, user_id, idx):
        entry = Slide(module_id=module_id, type=type, src=src, user_id=user_id, idx=idx)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_question_slide(self, module_id, type, question_id, answered, correct, choice_id, user_id, idx):
        entry = Slide(module_id=module_id, type=type, question_id=question_id, answered=answered, correct=correct, choice_id=choice_id, user_id=user_id, idx=idx, attempts=0)
        self.session.add(entry)
        self.session.commit()
        return entry.id



    def index_message(self, user_id, text, sender):
        entry = Message(user_id=user_id, text=text, sender=sender)
        self.session.add(entry)
        self.session.commit()
        return entry.id


    def index_authuser_group(self, user_id, group_id, admin=False):
        entry = Join__AuthUser_Group(user_id=user_id, group_id=group_id, admin=admin)
        self.session.add(entry)
        self.session.commit()
        return entry.id

    def index_demo_user(self, username, email, password):
        entry = auth_user(username=username, email=email, password=password, is_superuser=False, first_name='', last_name='', is_staff=False, is_active=True, date_joined=datetime.now())
        self.session.add(entry)
        self.session.commit()
        return entry.id



    def index_user(self, user_id):

        # --> 1. Index ExcelExerciseCompletion for all ExcelExercises

        # --> 2. Index ability parameters all with null starting value ofc

        # --> 3. Index Join__User_LearningModule to add modules to user
        #           - Clone user_id == null slides per learning module to entries with correct user_id
        return 0

    def index_content(self):

        # --> 1. Index Excel Exercises

        # --> 2. Index Topics

        # --> 3. Index LearningModule table
            # --> Index learning module questions
                # --> Index question topic in Join__Question_Topic
            # --> Index learning module slides
            # --> Index Slides per module indexed


        return 0














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

class ExcelExercise(DeclarativeBase):
    __tablename__ = 'ExcelExercise'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)

class ExcelExerciseCompletion(DeclarativeBase):
    __tablename__ = 'ExcelExerciseCompletion'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    exercise_id = Column('exercise_id', Integer, ForeignKey('ExcelExercise.id'))
    is_completed = Column('is_completed', Boolean, default=False)
    reason = Column('reason', String, default="Has not been started")




class Message(DeclarativeBase):
    __tablename__ = 'Message'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    text = Column('text', String)
    sender = Column('sender', String)
    cleared = Column('cleared', Boolean, default=False)
    date = Column('date', DateTime, default=func.now())




class Topic(DeclarativeBase):
    __tablename__ = 'Topic'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)


class AbilityParameter(DeclarativeBase):
    __tablename__ = 'AbilityParameter'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    topic_id = Column('topic_id', Integer, ForeignKey('Topic.id'))
    value = Column('value', Float, nullable=True, default=None)


class Join__Question_Topic(DeclarativeBase):
    __tablename__ = 'Join__Question_Topic'
    id = Column(Integer, primary_key=True)
    question_id = Column('question_id', Integer, ForeignKey('Question.id'))
    topic_id = Column('topic_id', Integer, ForeignKey('Topic.id'))


class Join__LearningModule_Topic(DeclarativeBase):
    __tablename__ = 'Join__LearningModule_Topic'
    id = Column(Integer, primary_key=True)
    topic_id = Column('topic_id', Integer, ForeignKey('Topic.id'))
    module_id = Column('module_id', Integer, ForeignKey('LearningModule.id'))



class Question(DeclarativeBase):
    __tablename__ = 'Question'
    id = Column(Integer, primary_key=True)
    text = Column('text', String)
    choices = Column('choices', String)
    difficulty = Column('difficulty', Float)
    discrimination = Column('discrimination', Float)
    guessing = Column('guessing', Float)
    explanation = Column('explanation', String)






class Test(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Test'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    date = Column('date', DateTime)
    duration = Column('duration', Integer)
    num_questions = Column('num_questions', Integer)
    type = Column('type', String)
    in_progress = Column('in_progress', Boolean)
    score = Column('score', String, nullable=True, default=None) # Null when test has not been completed




class TestQuestion(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'TestQuestion'
    id = Column(Integer, primary_key=True)
    test_id = Column('test_id', Integer, ForeignKey('Test.id'))
    question_id = Column('question_id', Integer, ForeignKey('Question.id'))
    answered = Column('answered', Boolean)
    correct = Column('correct', Boolean)
    choice_id = Column('choice_id', Integer)





class LearningModule(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'LearningModule'
    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    icon = Column('icon', String)
    course = Column('course', String, nullable=True)



class Join__User_LearningModule(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Join__User_LearningModule'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    module_id = Column('module_id', Integer, ForeignKey('LearningModule.id'))
    slide_idx = Column('slide_idx', Integer, default=0)






class Slide(DeclarativeBase):
    """Sqlalchemy broad measurement categories model"""
    __tablename__ = 'Slide'
    id = Column(Integer, primary_key=True)
    module_id = Column('module_id', Integer, ForeignKey('LearningModule.id'))
    type = Column('type', String)
    src = Column('src', String, nullable=True)
    question_id = Column('question_id', Integer, ForeignKey('Question.id'), nullable=True)
    answered = Column('answered', Boolean)
    correct = Column('correct', Boolean)
    choice_id = Column('choice_id', Integer)
    user_id = Column('user_id', Integer, ForeignKey('auth_user.id'))
    idx = Column('idx', Integer)
    attempts = Column('attempts', Integer, nullable=True, default=None)
