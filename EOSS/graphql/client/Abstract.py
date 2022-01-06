import requests
import aiohttp
import asyncio
import json
from concurrent.futures import ProcessPoolExecutor

from EOSS.aws.utils import graphql_server_address

from gql import Client as GQLClient
from gql.transport.websockets import WebsocketsTransport
from gql.transport.aiohttp import AIOHTTPTransport
from asgiref.sync import async_to_sync, sync_to_async

from graphql import (build_ast_schema, parse)

class MissionCostWrapper:
    powerBudgetSlots = ["payload-peak-power#", "satellite-BOL-power#"]
    costBudgetSlots = ["payload-cost#", "bus-cost#", "launch-cost#", "program-cost#", "IAT-cost#", "operations-cost#"]
    massBudgetSlots = ["adapter-mass", "propulsion-mass#", "structure-mass#", "avionics-mass#", "ADCS-mass#",
                       "EPS-mass#", "propellant-mass-injection", "propellant-mass-ADCS", "thermal-mass#",
                       "payload-mass#"]

    def __init__(self, cost_info):
        information = []
        for info in cost_info:
            # payload
            payloads = []
            for inst in info['payloads']:
                if inst['Instrument'] != None:
                    payloads.append(inst['Instrument']['name'])

            # budgets
            mass_budget = {}
            power_budget = {}
            cost_budget = {}
            for budget in info['budgets']:
                budget_type = budget['Mission_Attribute']['name']
                if budget_type in self.powerBudgetSlots:
                    power_budget[budget_type] = budget['value']
                if budget_type in self.massBudgetSlots:
                    mass_budget[budget_type] = budget['value']
                if budget_type in self.costBudgetSlots:
                    cost_budget[budget_type] = budget['value']
            cost_info_obj = MissionCostInformation(info['mission_name'], payloads, info['launch_vehicle'], info['mass'],
                                                   info['power'], info['cost'], mass_budget, power_budget, cost_budget)
            information.append(cost_info_obj)
        self.information = information

    def get_info(self):
        return self.information

class MissionCostInformation:
    def __init__(self, orbit_name, payload, launch_vehicle, total_mass, total_power, total_cost, mass_budget, power_budget, cost_budget):
        self.orbit_name = orbit_name
        self.payload = payload
        self.launch_vehicle = launch_vehicle
        self.total_mass = total_mass
        self.total_power = total_power
        self.total_cost = total_cost

        self.mass_budget = mass_budget       # dict
        self.power_budget = power_budget     # dict
        self.cost_budget = cost_budget       # dict



class SubscoreWrapper:
    def __init__(self, panels):
        information = []
        for panel in panels:
            objective_info = []
            for obj in panel['objectives']:
                subobjective_info = []
                for subobj in obj['subobjectives']:
                    if len(subobj['satisfaction']) > 0:
                        subobjective_info.append(SubscoreInformation(subobj['code'], subobj['description'], subobj['satisfaction'][0]['value'], subobj['weight']))
                if len(obj['satisfaction']) > 0:
                    objective_info.append(SubscoreInformation(obj['code'], obj['description'], obj['satisfaction'][0]['value'], obj['weight'], subobjective_info))
            if len(panel['satisfaction']) > 0:
                information.append(SubscoreInformation(panel['code'], panel['description'], panel['satisfaction'][0]['value'], panel['weight'], objective_info))
        self.information = information

    def get_info(self):
        return self.information

class SubscoreInformation:
    def __init__(self, name, description, value, weight, subscores=None):
        self.name = name
        self.description = description
        self.value = value
        self.weight = weight
        self.subscores = subscores


class AbstractGraphqlClient:

    # --> Only the constructor is to touch the django ORM
    # --> All other methods are async
    def __init__(self, user_info):

        # --> 1. Save user information
        self.user_info = user_info
        self.group_id = user_info.eosscontext.group_id
        self.problem_id = user_info.eosscontext.problem_id
        self.dataset_id = user_info.eosscontext.dataset_id
        self.user_id = user_info.user.id

        # --> 2. Get client from schema file
        self.hasura_url = graphql_server_address()

    async def _schema(self):
        schema_content = ""
        with open('/app/daphne/daphne_brain/EOSS/graphql/schema.graphql') as f:
            schema_content = await sync_to_async(f.read)()
        schema_parsed = await sync_to_async(parse)(schema_content)
        return await sync_to_async(build_ast_schema)(schema_parsed)

    async def _execute2_gql(self, query):
        transport = AIOHTTPTransport(url='http://graphql:8080/v1/graphql')
        async with GQLClient(transport=transport, fetch_schema_from_transport=False, ) as session:
            return await session.execute(query)

    async def _execute(self, query):
        async with aiohttp.ClientSession() as session:
            async with session.post('http://graphql:8080/v1/graphql', json={'query': query}) as response:
                result = json.loads(await response.text())
                if 'data' not in result:
                    return dict()
                return result['data']

    def save_to_file(self, input, file_name):
        file_path = '/app/daphne/daphne_brain/EOSS/graphql/output/' + file_name
        f = open(file_path, "w+")
        f.write(input)
        f.close()





    @staticmethod
    async def _proc(func, *args):
        loop = asyncio.get_running_loop()
        result = None
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(pool, func, *args)
        return result

    @staticmethod
    async def _query(query):
        async with aiohttp.ClientSession() as session:
            async with session.post('http://graphql:8080/v1/graphql', json={'query': query}) as response:
                result = json.loads(await response.text())
                if 'data' not in result:
                    return dict()
                return result['data']


    @staticmethod
    async def query(query):
        async with aiohttp.ClientSession() as session:
            async with session.post('http://graphql:8080/v1/graphql', json={'query': query}) as response:
                result = json.loads(await response.text())
                if 'data' not in result:
                    return dict()
                return result['data']




    @staticmethod
    async def _subscribe(subscription, tries=5, sleep_time=2):
        async with aiohttp.ClientSession() as session:
            for attempt in range(tries):
                # --> 1. Check to see if the obj exists
                async with session.post(graphql_server_address(), json={'query': subscription}) as response:
                    result = json.loads(await response.text())
                    if 'data' not in result:
                        print('--> DATA FIELD NOT FOUND IN SUB REQUEST', result)
                        await asyncio.sleep(sleep_time)
                        continue
                    if 'item' not in result['data']:
                        print('--> INCORRECTLY FORMATTED SUBSCRIPTION (needs item on element)', subscription)
                        return None

                    # --> 2. Check to see if object has been inserted
                    count = int(result['data']['item']['aggregate']['count'])
                    if count > 0:

                        # --> 3. Check to see if nodes were requested, return if so
                        if 'nodes' in result['data']['item']:
                            return result['data']['item']['nodes']
                        return count
                    else:
                        await asyncio.sleep(sleep_time)
        print('--> ITEM NOT FOUND IN', tries * sleep_time, 'SECONDS')
        return None

    @staticmethod
    async def _table(table_name, where=None, get=None):

        query = """
            query abstract_query {



            }   
        """

    @staticmethod
    async def _where(where_dict):

        # --> 1. Build where string
        where_list = []
        for key, value in where_dict.items():
            # --> problem_id: {_eq: %d}
            temp_str = ''
            if value['type'] == 'string':
                temp_str = """%s: {%s: "%s"}""" % (str(key), str(value['logic']), str(value['value']))
            if value['type'] == 'int':
                temp_str = """%s: {%s: %d}""" % (str(key), str(value['logic']), int(value['value']))
            if value['type'] == 'float':
                temp_str = """%s: {%s: %f}""" % (str(key), str(value['logic']), float(value['value']))
            where_list.append(temp_str)
        where_str = ''
        if len(where_list) > 0:
            where_str = ', '.join(where_list)

        # --> 2. Build and return final statement
        statement = """
            (where: {%s})
        """ % where_str

        return statement

    @staticmethod
    async def _where(field, logic, value, value_type):
        if value_type == str:
            return """%s: {%s: "%s"}""" % (field, logic, value)
        elif value_type == int:
            return """%s: {%s: %d}""" % (field, logic, value)
        elif value_type == float:
            return """%s: {%s: %f}""" % (field, logic, value)
        elif value_type == list:
            value_str = ''
            if isinstance(value, list):
                value_str = '[' + ','.join(value) + ']'
                return """%s: {%s: %s}""" % (field, logic, value_str)
            return """%s: {%s: %s}""" % (field, logic, value)
        return ''

    @staticmethod
    async def _where_neighbor(neighbor, field, logic, value, value_type):
        return """
            %s: {%s}
        """ % (neighbor, await AbstractGraphqlClient._where(field, logic, value, value_type))

    @staticmethod
    async def _table_wrap(table, value):
        return """
                %s: {%s}
        """ % (table, value)

    @staticmethod
    async def _where_wrapper(statements, distinct=None):

        # --> 1. Distinct
        distinct_str = ''
        if distinct is not None:
            distinct_str = """distinct_on: %s """ % str(distinct)

        # --> 2. Where
        where_string = ''
        if isinstance(statements, str):
            where_string = """ where: {%s} """ % statements
        elif isinstance(statements, list):
            if len(statements) > 0:
                statement_str = ','.join(statements)
                where_string = """ where: {%s} """ % statement_str

        # --> 3. Build and return
        if distinct_str == '' and where_string == '':
            return ''
        where_statement = '(' + distinct_str + ' ' + where_string + ')'
        return where_statement



    @staticmethod
    async def _format_input(inputs):
        ### Inputs could be one of three forms --> convert as necessary
        # 1. List of bits
        # 2. List of booleans
        # 3. String of bits (required for eval)
        converted_inputs = ''
        if isinstance(inputs, list):
            if len(inputs) > 0:
                if isinstance(inputs[0], int):
                    for x in inputs:
                        if x == 0:
                            converted_inputs += '0'
                        elif x == 1:
                            converted_inputs += '1'
                elif isinstance(inputs[0], bool):
                    for x in inputs:
                        if x == False:
                            converted_inputs += '0'
                        elif x == True:
                            converted_inputs += '1'
            else:
                print('--> INPUT LIST EMPTY')
                return None
        else:
            converted_inputs = inputs
        return converted_inputs




    """
          _____                 _  __ _        _____                            _       
         / ____|               (_)/ _(_)      |  __ \                          | |      
        | (___  _ __   ___  ___ _| |_ _  ___  | |__) |___  __ _ _   _  ___  ___| |_ ___ 
         \___ \| '_ \ / _ \/ __| |  _| |/ __| |  _  // _ \/ _` | | | |/ _ \/ __| __/ __|
         ____) | |_) |  __/ (__| | | | | (__  | | \ \  __/ (_| | |_| |  __/\__ \ |_\__ \
        |_____/| .__/ \___|\___|_|_| |_|\___| |_|  \_\___|\__, |\__,_|\___||___/\__|___/
               | |                                           | |                        
               |_|                                           |_|                  
    """

    @staticmethod
    async def add_user_to_group(user_id, group_id):
        if group_id is None:
            group_id = 1
        
        mutation = """
            mutation insert_user_to_group {
                insert_Join__AuthUser_Group_one(
                    object: {user_id: %d, group_id: %d, admin: false}
                ) {
                    id
                    group_id
                    user_id
                }
            }
        """ % (int(user_id), int(group_id))
        result = await AbstractGraphqlClient.query(mutation)
        if 'insert_Join__AuthUser_Group_one' not in result:
            return None
        return result['insert_Join__AuthUser_Group_one']

    @staticmethod
    async def get_problems():
        query = """
            query abstract_query {
                Problem {
                    id 
                    name 
                    group_id
                }
            }
        """
        result = await AbstractGraphqlClient.query(query)
        if 'Problem' not in result:
            return None
        return result['Problem']

    @staticmethod
    async def get_orbits(problem_id=None, group_id=None, orbit_name=None, attributes=False):
        if group_id is None:
            group_id = 1

        # --> 1. Where statements
        statements = []
        if problem_id is not None:
            statements.append(await AbstractGraphqlClient._where_neighbor('Join__Problem_Orbits', 'problem_id', '_eq', int(problem_id), int))
        if problem_id is not None:
            statements.append(await AbstractGraphqlClient._where('group_id', '_eq', int(group_id), int))
        where_str = await AbstractGraphqlClient._where_wrapper(statements)

        # --> 2. Return statements
        return_str = """
            id
            name
        """
        if attributes is True:
            return_str += """
                attributes: Join__Orbit_Attributes {
                    value
                    Orbit_Attribute {
                        name
                    }
                }
            """

        # --> 3. Query
        query = """
            query abstract_query {
                Orbit%s {
                    %s
                }
            }
        """ % (where_str, return_str)
        result = await AbstractGraphqlClient.query(query)
        if 'Orbit' not in result:
            return None
        return result['Orbit']

    @staticmethod
    async def get_instruments(problem_id=None, group_id=None, instrument_name=None, attributes=False):
        if group_id is None:
            group_id = 1

        # --> 1. Where statements
        statements = []
        if problem_id is not None:
            statements.append(await AbstractGraphqlClient._where_neighbor('Join__Problem_Instruments', 'problem_id', '_eq', int(problem_id), int))
        if problem_id is not None:
            statements.append(await AbstractGraphqlClient._where('group_id', '_eq', int(group_id), int))
        where_str = await AbstractGraphqlClient._where_wrapper(statements)

        # --> 2. Return statements
        return_str = """
                    id
                    name
                """
        if attributes is True:
            temp_where_str = ''
            if problem_id is not None:
                temp_where_str = await AbstractGraphqlClient._where_wrapper([await AbstractGraphqlClient._where('problem_id', '_eq', int(group_id), int)])
            return_str += """
                attributes: Join__Instrument_Characteristics%s {
                    value
                    Instrument_Attribute {
                        name
                    }
                }
            """ % temp_where_str

        # --> 3. Query
        query = """
                query abstract_query {
                    Instrument%s {
                        %s
                    }
                }
            """ % (where_str, return_str)
        result = await AbstractGraphqlClient.query(query)
        if 'Instrument' not in result:
            return None
        return result['Instrument']

    @staticmethod
    async def get_instrument_attributes(group_id=None, attribute_name=None):
        if group_id is None:
            group_id = 1

        # --> 1. Where statements
        statements = []
        if group_id is not None:
            statements.append(await AbstractGraphqlClient._where('group_id', '_eq', int(group_id), int))
        if attribute_name is not None:
            statements.append(await AbstractGraphqlClient._where('name', '_eq', str(attribute_name), str))
        where_str = await AbstractGraphqlClient._where_wrapper(statements)

        # --> 2. Return statements
        return_str = """
            id
            name
        """

        # --> 3. Query
        query = """
            query abstract_query {
                attributes: Instrument_Attribute%s {
                    %s
                }
            }
        """ % (where_str, return_str)
        result = await AbstractGraphqlClient.query(query)
        if 'attributes' not in result:
            return None
        return result['attributes']

    @staticmethod
    async def get_measurements(problem_id=None):

        # --> 1. Where statements
        statements = []
        if problem_id is not None:
            statements.append(await AbstractGraphqlClient._where('problem_id', '_eq', int(problem_id), int))
        where_str = await AbstractGraphqlClient._where_wrapper(statements, distinct='[measurement_id]')

        # --> 2. Return statements
        return_str = """
            Measurement {
                name
                id
            }
        """

        # --> 3. Query
        query = """
            query abstract_query {
                measurements: Requirement_Rule_Attribute%s {
                    %s
                }
            }
        """ % (where_str, return_str)
        result = await AbstractGraphqlClient.query(query)
        if 'measurements' not in result:
            return None
        return result['measurements']

    @staticmethod
    async def get_stakeholders(problem_id, panel=False, objective=False, subobjective=False):

        panel_str = ''
        if panel is True:
            panel_str = """
                        panel :Stakeholder_Needs_Panel(
                            where: {problem_id: {_eq: %d}}
                        ) {
                            id
                            name
                        }
                    """ % problem_id

        objective_str = ''
        if objective is True:
            objective_str = """
                        objective :Stakeholder_Needs_Objective(
                            where: {problem_id: {_eq: %d}}
                        ) {
                            id
                            name
                        }
                    """ % problem_id

        subobjective_str = ''
        if subobjective is True:
            subobjective_str = """
                        subobjective :Stakeholder_Needs_Subobjective(
                            where: {problem_id: {_eq: %d}}
                        ) {
                            id
                            name
                        }
                    """ % problem_id

        query = """        
            query get_stakeholder_info {
                %s
                %s
                %s
            }
        """ % (panel_str, objective_str, subobjective_str)
        return await AbstractGraphqlClient.query(query)

    @staticmethod
    async def get_arch_science_info(problem_id, arch_id):

        # --> 1. Query
        query = """
            query abstract_query {
                panels: Stakeholder_Needs_Panel(where: {problem_id: {_eq: %d}}) {
                    code: index_id
                    description
                    name
                    weight
                    satisfaction: ArchitectureScoreExplanations(where: {architecture_id: {_eq: %d}}) {
                        value: satisfaction
                    }
                    objectives: Stakeholder_Needs_Objectives {
                        code: name
                        description
                        weight
                        satisfaction: PanelScoreExplanations(where: {architecture_id: {_eq: %d}} {
                            value: satisfaction
                        }
                        subobjectives: Stakeholder_Needs_Subobjectives {
                            code: name
                            description
                            weight
                            satisfaction: ObjectiveScoreExplanations {
                                value: satisfaction
                            }
                        }
                    }
                }
            }
        """ % (int(problem_id), int(arch_id), int(arch_id))
        results = await AbstractGraphqlClient.query(query)
        panels = results['panels']
        information = SubscoreWrapper(panels).get_info()
        print("\n---> all stakeholder info", information)
        return information

    @staticmethod
    async def get_arch_cost_info(arch_id):
        # --> 1. Query
        query = """
            query abstract_query {
                cost_info: ArchitectureCostInformation(where: {architecture_id: {_eq: %d}}) {
                    mission_name
                    launch_vehicle
                    mass
                    power
                    cost
                    others
                    payloads: ArchitecturePayloads {
                        Instrument {
                            name
                        }
                    }
                    budgets: ArchitectureBudgets {
                        value
                        Mission_Attribute {
                            name
                        }
                    }
                }
            }
        """ % int(arch_id)
        results = await AbstractGraphqlClient.query(query)
        cost_info = results['cost_info']
        information = MissionCostWrapper(cost_info).get_info()
        return information

    @staticmethod
    async def insert_architecture(problem_id, dataset_id, user_id, inputs, science, cost):
        mutation = """
            mutation insert_architecture {
                architecture: insert_Architecture_one(object: {problem_id: %d, dataset_id: %d, user_id: %d, input: "%s", science: %f, cost: %f, ga: false, eval_status: false, improve_hv: false}) {
                    id
                }
            }
        """ % (int(problem_id), int(dataset_id), int(user_id), str(inputs), float(science), float(cost))
        return await AbstractGraphqlClient.query(mutation)









