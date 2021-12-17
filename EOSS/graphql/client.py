import requests
import aiohttp
import asyncio
import json

from EOSS.aws.utils import graphql_server_address

from gql import Client as GQLClient
from gql.transport.websockets import WebsocketsTransport
from gql.transport.aiohttp import AIOHTTPTransport
from asgiref.sync import async_to_sync, sync_to_async

from graphql import (build_ast_schema, parse)

class Client:

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
        async with GQLClient(transport=transport, fetch_schema_from_transport=False,) as session:
            return await session.execute(query)

    async def _execute(self, query):
        async with aiohttp.ClientSession() as session:
            async with session.post('http://graphql:8080/v1/graphql', json={'query': query }) as response:
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
    async def _query(query):
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
                async with session.post('http://graphql:8080/v1/graphql', json={'query': subscription}) as response:
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
        """ % (neighbor, await Client._where(field, logic, value, value_type))

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
