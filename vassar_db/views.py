from rest_framework.views import APIView
from rest_framework.response import Response
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from auth_API.helpers import get_or_create_user_information
import vassar_db.tables as tb
import vassar_db.queries as qs
import os

user = os.environ['USER']
password = os.environ['PASSWORD']
postgres_host = os.environ['POSTGRES_HOST']
postgres_port = os.environ['POSTGRES_PORT']
vassar_db_name = 'daphne'
db_string = f'postgresql+psycopg2://{user}:{password}@{postgres_host}:{postgres_port}/{vassar_db_name}'



def create_session():
    engine = create_engine(db_string, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


# This class will get all the tables when the problem builder page is called
class GetTables(APIView):
    def post(self, request, format=None):
        session = create_session()
        print("GETTING TABLES")
        interface = qs.TableReturn('Problem', session)
        interface.get_table()
        for instance in session.query(tb.Problem):
            print(instance.name, instance.id)
        return Response({'status': 'good'})







# Already handled for UserInformation
class NewUser(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        return Response({'status': 'good'})


class NewGroup(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        return Response({'status': 'good'})


class EditGroup(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        return Response({'status': 'good'})


class NewProblem(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        self.set_base_problem(request.data['base_problem'])
        self.create_problem(request.data)
        return Response({'status': 'good'})

    # Set base problem if users is building off another
    def set_base_problem(self, base_problem):
        return 0

    # Create and index the problem
    def create_problem(self, data):
        return 0


class EditProblem(APIView):
    def post(self, request, format=None):
        session = create_session()
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if request.data['problem_element'] == 'attribute':
            cursor = AttributeQuery(request.data, session)
        elif request.data['problem_element'] == 'aggregation_rule':
            cursor = AggregationRuleQuery(request.data, session)
        elif request.data['problem_element'] == 'mission_analysis':
            cursor = MissionAnalysisQuery(request.data, session)
        return Response({'status': 'ok'})


    
class NewInstrument(APIView):
    def post(self, request, format=None):
        return Response({'status': 'good'})


class EditInstrument(APIView):
    def post(self, request, format=None):
        return Response({'status': 'good'})






