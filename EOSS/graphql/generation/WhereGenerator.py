import os




class WhereGenerator:

    def __init__(self):
        self.init = 0

        #####################
        ### EXAMPLE USAGE ###
        #####################

        statements = {}

        statements['field'] = {'type': None, 'logic': None, 'value': None}

        # 1 -------------------------
        statements['t1'] = {'statements': {
            'field': {'type': None, 'logic': None, 'value': None},
        }}

        # 2 -------------------------
        statements['t2'] = {'statements': {
            # 'field': {'type': None, 'logic': None, 'value': None},
            'table': {'statements': {
                'field': {'type': None, 'logic': None, 'value': None},
            }}
        }}

        # 3 -------------------------
        statements['t3'] = {'statements': {
            # 'field': {'type': None, 'logic': None, 'value': None},
            'table': {'statements': {
                # 'field': {'type': None, 'logic': None, 'value': None},
                'table': {'statements': {
                    'field': {'type': None, 'logic': None, 'value': None},
                }}
            }}
        }}

        # 4 -------------------------
        statements['t4'] = {'statements': {
            # 'field': {'type': None, 'logic': None, 'value': None},
            'table': {'statements': {
                # 'field': {'type': None, 'logic': None, 'value': None},
                'table': {'statements': {
                    # 'field': {'type': None, 'logic': None, 'value': None},
                    'table': {'statements': {
                        'field': {'type': None, 'logic': None, 'value': None},
                    }}
                }}
            }}
        }}


    @staticmethod
    async def from_dict(where_dict):
        return await WhereGenerator.where_wrapper(where_dict)

    @staticmethod
    async def where_wrapper(where_dict):
        # --> 1. Get statement list
        statements_str = await WhereGenerator.parse_dict(where_dict)

        # --> 2. Compile into final where string
        return """(where: {%s})""" % statements_str

    @staticmethod
    async def parse_dict(where_dict):
        # ----- key (str): field name | table name
        # ---- type (str): int, float, str, bool | table
        # -- value (dict):

        statements = []
        for key, value_dict in where_dict.items():

            # --> 1. If this is a nested where statement
            if 'statements' in value_dict:
                table_str = await WhereGenerator.parse_dict(value_dict['statements'])
                temp_str = """%s: {%s}""" % (key, table_str)
                statements.append(temp_str)
                continue

            # --> 2. If not a nested where statement
            statements.append(await WhereGenerator.base_statement(key, value_dict))

        # --> 3. Return polished string
        statement_str = ''
        if len(statements) > 0:
            statement_str = ', '.join(statements)
        return statement_str

    @staticmethod
    async def base_statement(key, value_dict):
        # --> 1. Extract values
        type = value_dict['type']
        value = value_dict['value']
        logic = value_dict['logic']

        # --> 2. Build base statement
        base_str = ''
        if type == str:
            base_str = """%s: {%s: "%s"}""" % (str(key), str(logic), str(value))
        elif type == int:
            base_str = """%s: {%s: %d}""" % (str(key), str(logic), int(value))
        elif type == float:
            base_str = """%s: {%s: %f}""" % (str(key), str(logic), float(value))
        elif type == bool:
            base_str = """%s: {%s: %s}""" % (str(key), str(logic), str(bool(value)))
        else:
            print('--> ERROR, WRONG TYPE FOR BASE STATEMENT')
            raise Exception()
        return base_str



