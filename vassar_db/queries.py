from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Time, Enum, ForeignKey, Table, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
import vassar_db.tables as tb



class TableReturn:
    def __init__(self, table_name, session):
        self.session = session
        self.table_name = table_name

    def get_table(self):
        headers = []
        rows = []
        if self.table_name == 'Problem':
            headers = self.session.query(tb.Problem).column_descriptions
            for instance in self.session.query(tb.Problem):
                rows.append([instance.name, instance.id])
                print(instance.name, instance.id)
        print(headers)
        print(rows)

















# class VassarQuery:
#     def __init__(self, data, user):
#         self.aggregation_tables = ['Stakeholder_Needs_Panel', 'Stakeholder_Needs_Objective', 'Stakeholder_Needs_Subobjective']
#         self.data = data
#         self.user = user                   # Username form UserInformation table
#         self.problem = data['problem']     # Problem the user is interatcing with
#         self.operation = data['operation'] # Operation to perform on table: insert | modify | delete
#         self.target = data['target']       # Table to perform operation on
#         self.row_data = data['row_data']   # List containing data for operation

#     # This function will execute the query encoded in the request.data object
#     def execute(self):
#         if self.target in self.aggregation_tables:
#             self.aggregation_operation()
#         return 0


#     def aggregation_operation(self):
#         if self.target == 'Stakeholder_Needs_Panel':
#         elif self.target == 'Stakeholder_Needs_Objective':
#         elif self.target == 'Stakeholder_Needs_Subobjective':



# Editable Aggregation Rules: panel, objective, subobjective



class ProblemQuery:
    def __init__(self, data, session):
        self.aggregation_tables = ['Stakeholder_Needs_Panel', 'Stakeholder_Needs_Objective', 'Stakeholder_Needs_Subobjective']
        self.data = data
        self.user = user
        self.problem = data['problem']     # Problem the user is interatcing with
        self.target = data['target']       # Table to perform operation on
        self.operation = data['operation'] # Operation to perform on table: insert | modify | delete
        self.row_data = data['row_data']   # List containing data for operation



class AggregationRuleQuery(ProblemQuery):
    def execute(self):
        if self.target == 'Stakeholder_Needs_Panel':
            self.panel_query()
        elif self.target == 'Stakeholder_Needs_Objective':
            self.objective_query()
        elif self.target == 'Stakeholder_Needs_Subobjective':
            self.subobjective_query()
        return 0

    def panel_query(self):



        return 0

    def objective_query(self):
        return 0

    def subobjective_query(self):
        return 0

















# # Editable Attributes (types): instrument, mission, orbit, launch vehicles, requirement rules
# class AttributeQuery(ProblemQuery):
#     def execute(self):
#         if self.operation == 'insert':
#             self.insert()
#         elif self.operation == 'modify':
#             self.modify()
#         elif self.operation == 'delete':
#             self.delete()
#         return 0

#     def insert(self):
#         if self.type == 'instrument':
#             obj = Instrument_Attribute()
#         elif self.type == 'mission':
#         elif self.type == 'orbit':
#         elif self.type == 'launch vehicles':
#         elif self.type == 'requirement rules':
#         return 0

#     def modify(self):
#         if self.type == 'instrument':
#         elif self.type == 'mission':
#         elif self.type == 'orbit':
#         elif self.type == 'launch vehicles':
#         elif self.type == 'requirement rules':
#         return 0

#     def delete(self):
#         if self.type == 'instrument':
#         elif self.type == 'mission':
#         elif self.type == 'orbit':
#         elif self.type == 'launch vehicles':
#         elif self.type == 'requirement rules':
#         return 0

# # Editable Analysis: walker, power, launch vehicle
# class MissionAnalysisQuery(ProblemQuery):
#     def execute(self):
#         if self.type == 'walker':
#         elif self.type == 'power':
#         elif self.type == 'launch vehicle':
#         return 0





