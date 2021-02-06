

import requests
import json
import time
from auth_API.helpers import get_or_create_user_information
from EOSS.aws.utils import pprint



powerBudgetSlots    = [ "payload-peak-power#", "satellite-BOL-power#" ]
costBudgetSlots     = [ "payload-cost#", "bus-cost#", "launch-cost#", "program-cost#", "IAT-cost#", "operations-cost#" ]
massBudgetSlots     = [ "adapter-mass", "propulsion-mass#", "structure-mass#", "avionics-mass#", "ADCS-mass#", "EPS-mass#", "propellant-mass-injection", "propellant-mass-ADCS", "thermal-mass#", "payload-mass#" ]


def bool_list_to_string(bool_list_str):
    bool_list = json.loads(bool_list_str)
    print("--> bool_list_to_string", bool_list)
    return_str = ''
    for bool_pos in bool_list:
        if bool_pos:
            return_str = return_str + '1'
        else:
            return_str = return_str + '0'
    return return_str

def boolean_string_to_boolean_array(self, boolean_string):
        return [b == "1" for b in boolean_string]


class SubscoreInformation:
    def __init__(self, name, description, value, weight, subscores=None):
        self.name = name
        self.description = description
        self.value = value
        self.weight = weight
        self.subscores = subscores


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




class GraphqlClient:

    def __init__(self, hasura_url='http://graphql:8080/v1/graphql', request=None, problem_id=None, user_info=None):
        self.hasura_url = hasura_url
        if user_info is not None:
            self.problem_id = user_info.eosscontext.problem_id
        elif problem_id is not None:
            self.problem_id = str(problem_id)
        elif request is not None:
            user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)
            self.problem_id = str(user_info.eosscontext.problem_id)
        else:
            self.problem_id = str(4)


    def get_architectures(self, problem_id=5):
        problem_id = str(problem_id)
        query = ' query get_architectures { Architecture(where: {problem_id: {_eq: ' + self.problem_id + '}}) { id input cost science eval_status } } '
        return self.execute_query(query)

    def get_orbit_list(self, group_id, problem_id):
        # query = ' query get_orbit_list { Join__Orbit_Attribute(where: {problem_id: {_eq: ' + problem_id + '}}, distinct_on: orbit_id) { Orbit { id name } } } '
        query = ' query get_orbit_list { Join__Problem_Orbit(where: {problem_id: {_eq: ' + self.problem_id + '}}){ Orbit { id name } } } '
        return self.execute_query(query)

    def get_orbits_and_attributes(self):
        query = f'''
            query MyQuery {{
                items: Join__Problem_Orbit(where: {{problem_id: {{_eq: {self.problem_id}}}}}) {{
                    orbit: Orbit {{
                      name
                      attributes: Join__Orbit_Attributes {{
                        value
                        Orbit_Attribute {{
                          name
                        }}
                      }}
                    }}
                }}
            }}
        '''
        orbit_info = self.execute_query(query)['data']['items']
        return orbit_info

    def get_instrument_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_instrument_list { Join__Problem_Instrument(where: {problem_id: {_eq: ' + self.problem_id + '}}) { Instrument { id name } } } '
        return self.execute_query(query)

    def get_instruments_and_attributes(self):
        query = f'''
            query MyQuery {{
                items: Join__Problem_Instrument(where: {{problem_id: {{_eq: {self.problem_id}}}}}) {{
                    instrument: Instrument {{
                      name
                      attributes: Join__Instrument_Characteristics(where: {{problem_id: {{_eq: {self.problem_id}}}}}) {{
                        value
                        Orbit_Attribute {{
                          name
                        }}
                      }}
                    }}
                }}
            }}
        '''
        instrument_info = self.execute_query(query)['data']['items']
        return instrument_info



    def get_objective_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_objective_list { Stakeholder_Needs_Objective(where: {Problem: {id: {_eq: ' + self.problem_id + '}}})  { id name description panel_id problem_id weight} } '
        return self.execute_query(query)

    def get_subobjective_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_subobjective_list { Stakeholder_Needs_Subobjective(where: {Problem: {id: {_eq: ' + self.problem_id + '}}})  { id name description problem_id weight} } '
        return self.execute_query(query)

    def get_false_architectures(self, problem_id):
        problem_id = str(problem_id)
        query = ' query MyQuery { Architecture(where: {problem_id: {_eq: ' + self.problem_id + '}, eval_status: {_eq: false}}) { id ga eval_status input problem_id user_id } } '
        return self.execute_query(query)

    def get_instrument_from_objective(self, objective):
        query = ' query MyQuery { Instrument(where: {Join__Instrument_Measurements: {problem_id: {_eq: ' + self.problem_id + '}, Measurement: {Requirement_Rule_Attributes: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + self.problem_id + '}, name: {_eq: ' + str(objective) + '}}}}}}}) { id name } } '
        return self.execute_query(query)

    def get_instrument_from_panel(self, panel):
        query = ' query MyQuery { Instrument(where: {Join__Instrument_Measurements: {problem_id: {_eq: ' + self.problem_id + '}, Measurement: {Requirement_Rule_Attributes: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Panel: {problem_id: {_eq: ' + self.problem_id + '}, index_id: {_eq: ' + str(panel) + '}}}}}}}}) { id name } }'
        return self.execute_query(query)

    def get_architecture_score_explanation(self, arch_id):
        query = ' query MyQuery { ArchitectureScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Panel: {problem_id: {_eq: ' + self.problem_id + '}}}) { satisfaction Stakeholder_Needs_Panel { weight index_id } } }' 
        return self.execute_query(query)

    def get_panel_score_explanation(self, arch_id, panel):
        query = 'query myquery { PanelScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + self.problem_id + '}, Stakeholder_Needs_Panel: {index_id: {_eq: "' + panel + '"}}}}) { satisfaction Stakeholder_Needs_Objective { name weight } }  } '
        return self.execute_query(query)

    def get_objective_score_explanation(self, arch_id, objective):
        query = 'query myquery { ObjectiveScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + self.problem_id + '}, , Stakeholder_Needs_Objective: {name: {_eq: "' + objective + '"}}}}) { satisfaction Stakeholder_Needs_Subobjective { name weight } }  }'
        return self.execute_query(query)
    
    def get_arch_science_information(self, arch_id):
        query = f''' query myquery {{
            panels: Stakeholder_Needs_Panel(where: {{problem_id: {{_eq: {self.problem_id}}}}}) {{
                code: index_id
                description
                name
                weight
                satisfaction: ArchitectureScoreExplanations(where: {{architecture_id: {{_eq: {arch_id}}}}}) {{
                value: satisfaction
                }}
                objectives: Stakeholder_Needs_Objectives {{
                    code: name
                    description
                    weight
                    satisfaction: PanelScoreExplanations(where: {{architecture_id: {{_eq: {arch_id}}}}}) {{
                        value: satisfaction
                    }}
                    subobjectives: Stakeholder_Needs_Subobjectives {{
                        code: name
                        description
                        weight
                        satisfaction: ObjectiveScoreExplanations {{
                        value: satisfaction
                        }}
                    }}
                }}
            }}

        }}
        '''
        panels = self.execute_query(query)['data']['panels']
        information = []
        for panel in panels:
            objective_info = []
            for obj in panel['objectives']:
                subobjective_info = []
                for subobj in obj['subobjectives']:
                    subobjective_info.append(SubscoreInformation(subobj['code'], subobj['description'], subobj['satisfaction'][0]['value'], subobj['weight']))
                objective_info.append(SubscoreInformation(obj['code'], obj['description'], obj['satisfaction'][0]['value'], obj['weight'], subobjective_info))
            information.append(SubscoreInformation(panel['code'], panel['description'], panel['satisfaction'][0]['value'], panel['weight'], objective_info))
        print("\n---> all stakeholder info", information)
        return information

    def get_arch_cost_information(self, arch_id):
        query = f''' query myquery {{
            cost_info: ArchitectureCostInformation(where: {{architecture_id: {{_eq: {arch_id}}}}}) {{
                mission_name
                launch_vehicle
                mass
                power
                cost
                others
                payloads: ArchitecturePayloads {{
                    Instrument {{
                        name
                    }}
                }}
                budgets: ArchitectureBudgets {{
                    value
                    Mission_Attribute {{
                        name
                    }}
                }}
            }}

        }}
        '''
        cost_info = self.execute_query(query)['data']['cost_info']
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
                if budget_type in powerBudgetSlots:
                    power_budget[budget_type] = budget['value']
                if budget_type in massBudgetSlots:
                    mass_budget[budget_type] = budget['value']
                if budget_type in costBudgetSlots:
                    cost_budget[budget_type] = budget['value']
            cost_info_obj = MissionCostInformation(info['mission_name'], payloads, info['launch_vehicle'], info['mass'], info['power'], info['cost'], mass_budget, power_budget, cost_budget)
            information.append(cost_info_obj)
        return information


    def wait_for_critique(self, arch_id, timeout=20):
        results = self.get_arch_critique(arch_id)
        for x in range(0, timeout):
            results = self.get_arch_critique(arch_id)
            if results:
                return results
            time.sleep(1)
        return results


    def get_arch_critique(self, arch_id):
        query = f''' query myquery {{
            Architecture_by_pk(id: {arch_id}) {{
                id
                critique
            }}
        }}
        '''
        critique = self.execute_query(query)['data']['Architecture_by_pk']['critique']
        if critique == None:
            return []
        critiques = critique.split('|')
        return critiques[:-1]



    
    def get_arch_id(self, arch_object):
        id = arch_object.id
        inputs = bool_list_to_string(arch_object.inputs)
        outputs = arch_object.outputs
        print("--> Finding django arch:", self.problem_id, inputs)
        query = 'query myquery { Architecture(where: {problem_id: {_eq: ' + self.problem_id + '}, input: {_eq: "' + inputs + '"}}) { id } }'
        return self.execute_query(query)['data']['Architecture'][0]['id']
        

    def get_problems(self):
        query = 'query MyQuery { Problem { id name group_id } }'
        return self.execute_query(query)['data']['Problem']


    def insert_user_into_group(self, user_id, group_id=1):
        mutation = 'mutation { insert_Join__AuthUser_Group(objects: {group_id: '+str(group_id)+', user_id: ' + str(user_id) + ', admin: true}) { returning { group_id user_id id }}}'
        return self.execute_query(mutation)

    def execute_query(self, query):
        r = requests.post(self.hasura_url, json={'query': query })
        result = json.loads(r.text)
        print('\n-------- Query Result --------')
        print('----> URL:', self.hasura_url)
        print('--> QUERY:', query)
        pprint(result)
        print('-------------------------\n')
        return result

    # Return architecture details after vassar evaluates
    def subscribe_to_architecture(self, input, problem_id, timeout=1000):
        query = ' query subscribe_to_architecture { Architecture_aggregate(where: {problem_id: {_eq: ' + str(self.problem_id) + '}, input: {_eq: "' + str(input) + '"}})  {aggregate { count }} } '

        # Check for an entry every second
        counter = 0
        while int(self.execute_query(query)['data']['Architecture_aggregate']['aggregate']['count']) == 0:
            print('---> waiting for architecture: ' + str(counter))
            time.sleep(3)
            counter = counter + 1
            if counter >= timeout:
                return False
        
        query = ' query get_architecture { Architecture(where: {problem_id: {_eq: ' + str(self.problem_id) + '}, input: {_eq: "' + str(input) + '"}})  { id input science cost } } '
        return self.execute_query(query)







