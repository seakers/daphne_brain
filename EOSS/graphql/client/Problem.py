import timeit

from EOSS.graphql.client.Abstract import AbstractGraphqlClient as GQLClient
from daphne_context.models import UserInformation
from EOSS.graphql.generation.WhereGenerator import WhereGenerator
from asgiref.sync import async_to_sync, sync_to_async
from concurrent.futures import ProcessPoolExecutor
import asyncio





class ProblemGraphqlClient(GQLClient):

    def __init__(self, user_info: UserInformation):
        super().__init__(user_info)


    async def _problem_id(self, problem_id=None):
        if problem_id is None:
            return self.problem_id
        return problem_id

    ###########
    ### GET ###
    ###########

    async def get_orbits(self, problem_id=None, attributes=False):
        problem_id = await self._problem_id(problem_id)

        # --> 1. Return
        return_str = ''
        if attributes is True:
            return_str = """
                attributes: Join__Orbit_Attributes {
                    value
                    Orbit_Attribute {
                        name
                    }
                }
            """

        # --> 2. Query
        query = """        
            query get_orbit_list {
                Orbit(where: {Join__Problem_Orbits: {problem_id: {_eq: %d}}}){
                    id
                    name
                    %s
                }
            }
        """ % (int(problem_id), return_str)

        result = await self._query(query)
        if 'Orbit' not in result:
            return None
        return result['Orbit']

    async def get_instruments(self, problem_id=None, attributes=False, measurements=False, capabilities=False):
        problem_id = await self._problem_id(problem_id)

        capa_str = ''
        if capabilities is True:
            capa_str = """
                capabilities: Join__Instrument_Capability {
                    value
                    Measurement {
                        id
                        name
                    }
                    Measurement_Attribute {
                        id
                        name
                    }
                }
            """

        meas_str = ''
        if measurements is True:
            meas_str = """
                measurements: Join__Instrument_Measurement {
                    value
                    Measurement {
                        id
                        name
                    }
                }
            """

        attr_str = ''
        if attributes is True:
            attr_str = """
                attributes: Join__Instrument_Characteristics(where: {problem_id: {_eq: %d}}) {
                    value
                    Instrument_Attribute {
                        name
                    }
                }
            """ % int(problem_id)

        query = """        
            query get_instrument_list {
                Instrument(where: {Join__Problem_Instruments: {problem_id: {_eq: %d}}}) {
                    id
                    name
                    %s
                    %s
                    %s
                }
            }
        """ % (int(problem_id), attr_str, meas_str, capa_str)

        result = await self._query(query)
        if 'Instrument' not in result:
            return None
        return result['Instrument']

    async def get_instrument_attributes(self, group_id=None):
        if group_id is None:
            group_id = self.group_id

        query = """
            query get_instrument_attributes {
                attributes: Instrument_Attribute(where: {group_id: {_eq: %d}}) {
                    id
                    name
                }
            }
        """ % int(group_id)

        result = await self._query(query)
        if 'attributes' not in result:
            return None
        return result['attributes']

    async def get_instrument_attribute_value(self, problem_id=None, instrument=None, attribute=None):
        if problem_id is None:
            problem_id = self.problem_id

        # --> 1. Where
        statements = {}
        statements['problem_id'] = {'type': int, 'logic': '_eq', 'value': problem_id}
        if attribute is not None:
            nested = {
                'name': {'type': str, 'logic': '_eq', 'value': attribute},
            }
            statements['Instrument_Attribute'] = {'statements': nested}
        if instrument is not None:
            nested = {
                'name': {'type': str, 'logic': '_eq', 'value': instrument},
            }
            statements['Instrument'] = {'statements': nested}
        where_str = await WhereGenerator.from_dict(statements)

        # --> 2. Query
        query = """
            query get_instrument_attribute_value {
                attribute_value: Join__Instrument_Characteristic%s {
                    value
                    Instrument {
                        name
                    }
                    problem_id
                    Instrument_Attribute {
                        name
                    }
                }
            }
        """ % where_str

        # --> 3. Result
        result = await self._query(query)
        if 'attribute_value' not in result:
            return None
        return result['attribute_value']

    async def get_instrument_capability_values(self, group_id=None, instrument=None, attribute=None, measurement=None):
        if group_id is None:
            group_id = self.group_id

        # --> 1. Where
        statements = {}
        if attribute is not None:
            statements['Measurement_Attribute'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': attribute},
            }}
        if instrument is not None:
            statements['Instrument'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': instrument},
            }}
        if measurement is not None:
            statements['Measurement'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': measurement},
            }}
        statements['group_id'] = {'type': int, 'logic': '_eq', 'value': group_id}
        where_str = await WhereGenerator.from_dict(statements)

        # --> 2. Query
        query = """
            query get_instrument_attribute_value {
                capability_value: Join__Instrument_Capability%s {
                    value
                    Instrument {
                        name
                    }
                    group_id
                    Measurement_Attribute {
                        name
                    }
                    Measurement {
                        name
                    }
                }
            }
        """ % where_str

        # --> 3. Result
        result = await self._query(query)
        if 'capability_value' not in result:
            return None
        return result['capability_value']

    async def get_measurement_attributes(self, group_id=None):
        if group_id is None:
            group_id = self.group_id

        query = """
            query get_measurement_attributes {
                attributes: Measurement_Attribute(order_by: {name: asc}, where: {group_id: {_eq: %d}}) {
                    id
                    name
                }
            }
        """ % int(group_id)

        result = await self._query(query)
        if 'attributes' not in result:
            return None
        return result['attributes']

    async def get_measurement_requirements(self, problem_id=None, measurement_name=None, measurement_attribute=None, subobjective=None, distinct=None):
        if problem_id is None:
            problem_id = self.problem_id

        # --> 1. Where
        statements = {}
        if measurement_attribute is not None:
            statements['Measurement_Attribute'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': measurement_attribute},
            }}
        if subobjective is not None:
            statements['Stakeholder_Needs_Subobjective'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': subobjective},
            }}
        if measurement_name is not None:
            statements['Measurement'] = {'statements': {
                'name': {'type': str, 'logic': '_eq', 'value': measurement_name},
            }}
        statements['problem_id'] = {'type': int, 'logic': '_eq', 'value': problem_id}
        where_str = await WhereGenerator.from_dict(statements)







        # --> 2. Query
        query = """
            query get_measurement_requirements {
                requirements: Requirement_Rule_Attribute%s {
                    Measurement_Attribute {
                        name
                    }
                    Measurement {
                        name
                    }
                    scores
                    thresholds
                    Stakeholder_Needs_Subobjective {
                        name
                    }
                }
            }
        """ % where_str

        # --> 3. Result
        result = await self._query(query)
        if 'requirements' not in result:
            return None
        return result['requirements']

    async def get_requirement_rule_attribute(self, problem_id=None, measurement_name=None, measurement_attribute=None, subobjective=None):
        problem_id = await self._problem_id(problem_id)

        where_list = []
        if measurement_name is not None:
            measurement_name_query = """Measurement: {name: {_eq: "%s"}}""" % str(measurement_name)
            where_list.append(measurement_name_query)
        if measurement_attribute is not None:
            measurement_attribute_query = """Measurement_Attribute: {name: {_eq: "%s"}}""" % str(measurement_attribute)
            where_list.append(measurement_attribute_query)
        if subobjective is not None:
            subobjective_query = """Stakeholder_Needs_Subobjective: {name: {_eq: "%s"}}""" % str(subobjective)
            where_list.append(subobjective_query)

        params = ''
        if len(where_list) > 0:
            joined_str = ', '.join(where_list)
            params += (', ' + joined_str)

        where_statement = """ where: {problem_id: {_eq: %d}%s}""" % (problem_id, params)

        query = """        
                    query requirement_rule_attribute {
                        requirements: Requirement_Rule_Attribute(
                            %s                      
                        ) {
                            Measurement_Attribute {
                                name
                            }
                            Measurement {
                                name
                            }
                            scores
                            thresholds
                            Stakeholder_Needs_Subobjective {
                                name
                            }
                        }
                    }
                """ % where_statement

        result = await self._query(query)
        if 'requirements' not in result:
            return None
        return result['requirements']

    async def get_stakeholders(self, problem_id=None, panel=False, objective=False, subobjective=False):
        problem_id = await self._problem_id(problem_id)

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

        return await self._query(query)


    ############
    ### SPEC ###
    ############

    async def get_instrument_from_objective(self, objective, problem_id=None):
        if problem_id is None:
            problem_id = self.problem_id

        # --> 1. Where
        statements = {}
        statements['Join__Instrument_Measurements'] = {'statements': {
            'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
            'Measurement': {'statements': {
                'Requirement_Rule_Attributes': {'statements': {
                    'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                    'Stakeholder_Needs_Subobjective': {'statements': {
                        'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                        'Stakeholder_Needs_Objective': {'statements': {
                            'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                            'name': {'type': str, 'logic': '_eq', 'value': objective},
                        }}
                    }}
                }}
            }}
        }}
        where_str = await WhereGenerator.from_dict(statements)




        # --> 2. Query
        query = """
            query get_instrument_from_objective {
                Instrument%s {
                    id
                    name
                }
            }
        """ % where_str

        # --> 3. Result
        result = await self._query(query)
        if 'Instrument' not in result:
            return None
        return result['Instrument']

    async def get_instrument_from_panel(self, panel, problem_id=None):
        if problem_id is None:
            problem_id = self.problem_id

        # --> 1. Where
        statements = {}
        statements['Join__Instrument_Measurements'] = {'statements': {
            'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
            'Measurement': {'statements': {
                'Requirement_Rule_Attributes': {'statements': {
                    'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                    'Stakeholder_Needs_Subobjective': {'statements': {
                        'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                        'Stakeholder_Needs_Objective': {'statements': {
                            'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                            'Stakeholder_Needs_Panel': {'statements': {
                                'problem_id': {'type': int, 'logic': '_eq', 'value': problem_id},
                                'name': {'type': str, 'logic': '_eq', 'value': panel},
                            }}
                        }}
                    }}
                }}
            }}
        }}
        where_str = await WhereGenerator.from_dict(statements)








        # --> 2. Query
        query = """
            query get_instrument_from_panel {
                Instrument%s {
                    id
                    name
                }
            }
        """ % where_str

        # --> 3. Result
        result = await self._query(query)
        if 'Instrument' not in result:
            return None
        return result['Instrument']