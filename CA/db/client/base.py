from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
import os

user = os.environ['USER']
password = os.environ['PASSWORD']
postgres_host = os.environ['POSTGRES_HOST']
postgres_port = os.environ['POSTGRES_PORT']
vassar_db_name = 'daphne'
db_string = f'postgresql+psycopg2://{user}:{password}@{postgres_host}:{postgres_port}/{vassar_db_name}'


engine = create_engine(db_string, echo=True)
DeclarativeBase = declarative_base(engine)