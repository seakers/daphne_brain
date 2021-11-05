

import requests
import json
import time
from auth_API.helpers import get_or_create_user_information
from EOSS.aws.utils import graphql_server_address, pprint



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

    def __init__(self, hasura_url=None, request=None, problem_id=None, user_info=None):
        if hasura_url is not None:
            self.hasura_url = hasura_url
        else:
            self.hasura_url = graphql_server_address()

        if user_info is not None:
            self.problem_id = user_info.eosscontext.problem_id
            self.dataset_id = user_info.eosscontext.dataset_id
        elif problem_id is not None:
            self.problem_id = str(problem_id)
        elif request is not None:
            user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)
            self.problem_id = str(user_info.eosscontext.problem_id)
        else:
            self.problem_id = str(5)

    def boolean_string_to_boolean_array(self, boolean_string):
        return [b == "1" for b in boolean_string]

    def get_architectures(self, problem_id=6, dataset_id=-1):
        query = f'query get_architectures {{ Architecture(order_by: {{id: asc}}, where: {{problem_id: {{_eq: {problem_id} }}, dataset_id: {{_eq: {dataset_id} }} }}) {{ id input cost science eval_status }} }} '
        return self.execute_query(query)

    def get_architectures_ai4se(self, problem_id=6, dataset_id=-1):
        query = f'query get_architectures {{ Architecture(order_by: {{id: asc}}, where: {{problem_id: {{_eq: {problem_id} }}, dataset_id: {{_eq: {dataset_id} }} }}) {{ id input cost science eval_status programmatic_risk fairness data_continuity ArchitectureScoreExplanations {{ panel_id satisfaction }} }} }} '
        return self.execute_query(query)

    def get_architectures_ai4se_form(self, problem_id=6, dataset_id=-1):
        query = f'query get_architectures {{ Architecture(order_by: {{id: asc}}, where: {{problem_id: {{_eq: {self.problem_id} }}, dataset_id: {{_eq: {self.dataset_id} }} }}) {{ id input cost science eval_status programmatic_risk fairness data_continuity ArchitectureScoreExplanations {{ panel_id satisfaction }} }} }} '
        results = self.execute_query(query)
        archs = []
        for arch in results['data']['Architecture']:
            if not arch['eval_status']:
                continue
            outputs = [float(arch['cost']), float(arch['data_continuity']), float(arch['fairness']),
                       float(arch['programmatic_risk'])]
            for x in arch['ArchitectureScoreExplanations']:
                outputs.append(float(x['satisfaction']))  # There will be three stakeholder panel satisfactions
            curr_arch = {
                'inputs': self.boolean_string_to_boolean_array(arch['input']),
                'outputs': outputs
            }
            archs.append(curr_arch)
        return archs






    def check_for_existing_arch(self, problem_id, dataset_id, input):
        query = f'''
        query ArchitectureCount($problem_id: Int!, $dataset_id: Int!, $input: String!) {{
            items: Architecture_aggregate(where: {{problem_id: {{_eq: $problem_id}}, dataset_id: {{_eq: $dataset_id}}, input: {{_eq: $input}} }}) 
            {{
                aggregate {{
                    count
                }}
                nodes {{
                    id
                }}
            }}
        }}
        '''
        variables = {
            "problem_id": problem_id,
            "dataset_id": dataset_id,
            "input": input
        }
        query_result = self.execute_query(query, variables)
        count = query_result["data"]["items"]["aggregate"]["count"]
        arch_id = None
        if count > 0:
            arch_id = query_result["data"]["items"]["nodes"][0]["id"]
        return count > 0, arch_id

    def check_dataset_read_only(self, dataset_id):
        query = f'''
        query current_dataset($dataset_id: Int!) {{
            current_dataset: Dataset(where: {{id: {{_eq: $dataset_id}}}}) {{
                id
                name
                user_id
                Problem {{
                    id
                    name
                }}
                Group {{
                    id
                    name
                }}
            }}
            }}
        '''
        variables = {
            "dataset_id": dataset_id
        }
        query_result = self.execute_query(query, variables)
        current_dataset = query_result["data"]["current_dataset"][0]
        
        return current_dataset["user_id"] == None and current_dataset["Group"] == None

    def get_orbit_list(self, problem_id):
        # query = ' query get_orbit_list { Join__Orbit_Attribute(where: {problem_id: {_eq: ' + problem_id + '}}, distinct_on: orbit_id) { Orbit { id name } } } '
        query = f'query get_orbit_list {{ Join__Problem_Orbit(where: {{problem_id: {{_eq: {problem_id} }}}}) {{ Orbit {{ id name }} }} }}'
        return self.execute_query(query)

    def get_orbits_and_attributes(self, problem_id):
        query = f'''
            query MyQuery {{
                items: Join__Problem_Orbit(where: {{problem_id: {{_eq: {problem_id}}}}}) {{
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

    def get_architectures_like(self, dataset_id, arch_input_list):
        query = f'''
            query MyQuery {{
              Architecture(where: {{dataset_id: {{_eq: {dataset_id}}}, input: {{_in: {json.dumps(arch_input_list)}}}}}, order_by: {{eval_idx: asc}}) {{
                cost
                programmatic_risk
                fairness
                data_continuity
                eval_idx
                ArchitectureScoreExplanations {{
                  satisfaction
                  Stakeholder_Needs_Panel {{
                    name
                  }}
                }}
              }}
            }}
        '''
        return self.execute_query(query)

    def get_architectures_all(self, dataset_id):
        query = f'''
            query MyQuery {{
              Architecture(where: {{dataset_id: {{_eq: {dataset_id}}}}}, order_by: {{eval_idx: asc}}) {{
                cost
                input
                programmatic_risk
                fairness
                data_continuity
                eval_idx
                ArchitectureScoreExplanations {{
                  satisfaction
                  Stakeholder_Needs_Panel {{
                    name
                  }}
                }}
              }}
            }}
        '''
        return self.execute_query(query)

    def get_architectures_like_aggregate(self, dataset_id, arch_input_list):
        query = f'''
                    query MyQuery {{
                      Architecture_aggregate(where: {{dataset_id: {{_eq: {dataset_id}}}, input: {{_in: {json.dumps(arch_input_list)}}}}}) {{
                        aggregate {{
                            count
                        }}
                      }}
                    }}
                '''
        return self.execute_query(query)

    def get_architectures_aggregate(self, dataset_id):
        query = f'''
                    query MyQuery {{
                      Architecture_aggregate(where: {{dataset_id: {{_eq: {dataset_id}}}}}) {{
                        aggregate {{
                            count
                        }}
                      }}
                    }}
                '''
        return self.execute_query(query)

    def get_instrument_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_instrument_list { Join__Problem_Instrument(where: {problem_id: {_eq: ' + self.problem_id + '}}) { Instrument { id name } } } '
        return self.execute_query(query)

    def get_instrument_list_ai4se(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_instrument_list { Join__Problem_Instrument(where: {problem_id: {_eq: ' + problem_id + '}}) { Instrument { id name } } } '
        return self.execute_query(query)

    def get_instruments_and_attributes(self, problem_id):
        query = f'''
            query MyQuery {{
                items: Join__Problem_Instrument(where: {{problem_id: {{_eq: {problem_id}}}}}) {{
                    instrument: Instrument {{
                      name
                      attributes: Join__Instrument_Characteristics(where: {{problem_id: {{_eq: {problem_id}}}}}) {{
                        value
                        Instrument_Attribute {{
                          name
                        }}
                      }}
                    }}
                }}
            }}
        '''
        instrument_info = self.execute_query(query)['data']['items']
        return instrument_info

    def get_instrument_attributes(self, group_id):
        query = '''
        query get_instrument_attributes($group_id: Int!) {
          attributes: Instrument_Attribute(where: {group_id: {_eq: $group_id}}) {
            id
            name
          }
        }'''
        variables = {
            "group_id": group_id
        }
        instrument_attributes = self.execute_query(query, variables)['data']['attributes']
        return instrument_attributes

    def get_instrument_attribute_value(self, problem_id, instrument, attribute):
        query = '''
        query get_instrument_attribute_value($instrument_name: String = "", $attribute_name: String = "", $problem_id: Int = 10) {
            attribute_value: Join__Instrument_Characteristic(where: { Instrument_Attribute: {name: {_eq: $attribute_name}}, Instrument: {name: {_eq: $instrument_name}}, problem_id: {_eq: $problem_id}}) {
                value
                Instrument {
                    name
                }
                problem_id
                Instrument_Attribute {
                    name
                }
            }
        }'''
        variables = {
            "problem_id": problem_id,
            "instrument_name": instrument,
            "attribute_name": attribute
        }
        attribute_value = self.execute_query(query, variables)['data']['attribute_value']
        return attribute_value

    def get_instrument_capability_values(self, group_id, instrument, attribute, measurement=None):
        query_wo_measurement = '''
        query get_instrument_capability_value($instrument_name: String = "", $attribute_name: String = "", $group_id: Int = 10) {
            capability_value: Join__Instrument_Capability(where: {Measurement_Attribute: {name: {_eq: $attribute_name}}, Instrument: {name: {_eq: $instrument_name}}, group_id: {_eq: $group_id}}) {
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
        }'''

        query_measurement = '''
        query get_instrument_capability_value($instrument_name: String = "", $attribute_name: String = "", $group_id: Int = 10, $measurement_name: String = "") {
            capability_value: Join__Instrument_Capability(where: {Measurement_Attribute: {name: {_eq: $attribute_name}}, Instrument: {name: {_eq: $instrument_name}}, group_id: {_eq: $group_id}, Measurement: {name: {_eq: $measurement_name}}}) {
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
        }'''

        variables = {
            "group_id": group_id,
            "instrument_name": instrument,
            "attribute_name": attribute
        }

        if measurement is None:
            capability_value = self.execute_query(query_wo_measurement, variables)['data']['capability_value']
        else:
            variables["measurement_name"] = measurement
            capability_value = self.execute_query(query_measurement, variables)['data']['capability_value']
        
        return capability_value

    def get_measurement_requirements(self, problem_id, measurement_name, measurement_attribute, subobjective=None):
        query_no_stakeholder = '''
        query MyQuery($measurement_name: String = "", $measurement_attribute: String = "", $problem_id: Int = 10) {
            requirements: Requirement_Rule_Attribute(where: {Measurement: {name: {_eq: $measurement_name}}, Measurement_Attribute: {name: {_eq: $measurement_attribute}}, problem_id: {_eq: $problem_id}}) {
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
        }'''

        query_stakeholder = '''
        query MyQuery($measurement_name: String = "", $measurement_attribute: String = "", $problem_id: Int = 10, $subobjective: String = "") {
            requirements: Requirement_Rule_Attribute(where: {Measurement: {name: {_eq: $measurement_name}}, Measurement_Attribute: {name: {_eq: $measurement_attribute}}, problem_id: {_eq: $problem_id}, Stakeholder_Needs_Subobjective: {name: {_eq: $subobjective}}}) {
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
        '''

        variables = {
            "problem_id": problem_id,
            "measurement_name": measurement_name,
            "measurement_attribute": measurement_attribute
        }

        if subobjective is None:
            capability_value = self.execute_query(query_no_stakeholder, variables)['data']['requirements']
        else:
            variables["subobjective"] = subobjective
            capability_value = self.execute_query(query_stakeholder, variables)['data']['requirements']
        
        return capability_value

    def get_problem_measurements(self, problem_id):
        query = '''
        query get_problem_measurements($problem_id: Int!) {
          measurements: Requirement_Rule_Attribute(distinct_on: [measurement_id] where: {problem_id: {_eq: $problem_id}}) {
            Measurement {
              name
            }
          }
        }
        '''
        variables = {
            "problem_id": problem_id
        }
        problem_measurements = self.execute_query(query, variables)['data']['measurements']
        return problem_measurements

    def get_measurement_for_subobjective(self, problem_id, subobjective):
        query = '''
        query MyQuery($subobjective: String = "", $problem_id: Int = 1) {
            measurements: Requirement_Rule_Attribute(distinct_on: [measurement_id], where: {Stakeholder_Needs_Subobjective: {name: {_eq: $subobjective}}, problem_id: {_eq: $problem_id}}) {
                Measurement {
                    name
                }
            }
        }
        '''
        variables = {
            "problem_id": problem_id,
            "subobjective": subobjective
        }
        problem_measurements = self.execute_query(query, variables)['data']['measurements'][0]['Measurement']['name']
        return problem_measurements

    def get_stakeholders_list(self, problem_id):
        query = '''
        query get_stakeholders_list($problem_id: Int!) {
          stakeholders: Stakeholder_Needs_Panel(where: {problem_id: {_eq: $problem_id}}) {
            id
            name
          }
        }
        '''
        variables = {
            "problem_id": problem_id
        }
        stakeholders = self.execute_query(query, variables)['data']['stakeholders']
        return stakeholders

    def get_objectives_list(self, problem_id):
        query = '''
        query get_objectives_list($problem_id: Int!) {
          objectives: Stakeholder_Needs_Objective(where: {problem_id: {_eq: $problem_id}}) {
            name
          }
        }
        '''
        variables = {
            "problem_id": problem_id
        }
        objectives = self.execute_query(query, variables)['data']['objectives']
        return objectives

    def get_subobjectives_list(self, problem_id):
        query = '''
        query get_subobjectives_list($problem_id: Int!) {
          subobjectives: Stakeholder_Needs_Subobjective(where: {problem_id: {_eq: $problem_id}}) {
            name
          }
        }
        '''
        variables = {
            "problem_id": problem_id
        }
        subobjectives = self.execute_query(query, variables)['data']['subobjectives']
        return subobjectives

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

    def get_false_architectures(self, dataset_id):
        dataset_id = str(dataset_id)
        query = ' query MyQuery { Architecture(order_by: {{id: asc}}, where: {dataset_id: {_eq: ' + dataset_id + '}, eval_status: {_eq: false}}) { id ga eval_status input problem_id user_id } } '
        return self.execute_query(query)

    def get_instrument_from_objective(self, problem_id, objective):
        query = ' query MyQuery { Instrument(where: {Join__Instrument_Measurements: {problem_id: {_eq: ' + str(problem_id) + '}, Measurement: {Requirement_Rule_Attributes: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + str(problem_id) + '}, name: {_eq: ' + str(objective) + '}}}}}}}) { id name } } '
        return self.execute_query(query)

    def get_instrument_from_panel(self, problem_id, panel):
        query = ' query MyQuery { Instrument(where: {Join__Instrument_Measurements: {problem_id: {_eq: ' + str(problem_id) + '}, Measurement: {Requirement_Rule_Attributes: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Panel: {problem_id: {_eq: ' + str(problem_id) + '}, name: {_eq: ' + str(panel) + '}}}}}}}}) { id name } }'
        return self.execute_query(query)

    def get_architecture_score_explanation(self, problem_id, arch_id):
        query = ' query MyQuery { ArchitectureScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Panel: {problem_id: {_eq: ' + str(problem_id) + '}}}) { satisfaction Stakeholder_Needs_Panel { weight index_id } } }' 
        return self.execute_query(query)

    def get_panel_score_explanation_by_id(self, problem_id, arch_id, panel_id):
        query = 'query myquery { PanelScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Panel: {index_id: {_eq: "' + panel_id + '"}}}}) { satisfaction Stakeholder_Needs_Objective { name weight } }  } '
        return self.execute_query(query)

    def get_panel_score_explanation(self, problem_id, arch_id, panel):
        query = 'query myquery { PanelScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Objective: {problem_id: {_eq: ' + str(problem_id) + '}, Stakeholder_Needs_Panel: {name: {_eq: "' + panel + '"}}}}) { satisfaction Stakeholder_Needs_Objective { name weight } }  } '
        return self.execute_query(query)

    def get_objective_score_explanation(self, problem_id, arch_id, objective):
        query = 'query myquery { ObjectiveScoreExplanation(where: {architecture_id: {_eq: ' + str(arch_id) + '}, Stakeholder_Needs_Subobjective: {problem_id: {_eq: ' + str(problem_id) + '}, , Stakeholder_Needs_Objective: {name: {_eq: "' + objective + '"}}}}) { satisfaction Stakeholder_Needs_Subobjective { name weight } }  }'
        return self.execute_query(query)

    def get_subobjective_score_explanation(self, arch_id, subobjective):
        query = '''query MyQuery($arch_id: Int!, $subobjective_name: String!) {
            SubobjectiveScoreExplanation(where: { architecture_id: {_eq: $arch_id}, Stakeholder_Needs_Subobjective: {name: {_eq: $subobjective_name}}}) {
                measurement_attribute_values
                score
                taken_by
                justifications
            }
        }'''
        return self.execute_query(query, {"arch_id": arch_id, "subobjective_name": subobjective})
    
    def get_arch_science_information(self, problem_id, arch_id):
        query = f'''
        query myquery {{
            panels: Stakeholder_Needs_Panel(where: {{problem_id: {{_eq: {problem_id}}}}}) {{
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

    def get_arch_cost_information(self, problem_id, arch_id):
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
        query = 'query get_problems { Problem { id name group_id } }'
        return self.execute_query(query)['data']['Problem']


    def get_default_dataset_id(self, dataset_name, problem_id):
        query = f'query get_default_dataset_id {{ Dataset(where: {{problem_id: {{_eq: {problem_id} }}, name: {{_eq: "{dataset_name}" }}, user_id: {{_is_null: true }}, group_id: {{_is_null: true }} }}) {{ id name }} }}'
        return self.execute_query(query)['data']['Dataset'][0]['id']

    def clone_dataset(self, src_dataset_id, user_id, dst_dataset_name):
        get_src_dataset_query = f'query default_dataset {{ Dataset(where: {{id: {{_eq: {src_dataset_id} }} }}) {{ id name problem_id }} Architecture(order_by: {{id: asc}}, where: {{dataset_id: {{_eq: {src_dataset_id} }} }}) {{ cost science problem_id eval_status ga improve_hv critique input }}  }}'
        original_dataset = self.execute_query(get_src_dataset_query)['data']
        add_new_dataset_query = f'mutation insert_new_dataset {{ insert_Dataset_one(object: {{name: "{dst_dataset_name}", problem_id: {original_dataset["Dataset"][0]["problem_id"]}, user_id: {user_id} }}) {{ id }} }}'
        new_dataset_id = self.execute_query(add_new_dataset_query)['data']['insert_Dataset_one']['id']
        for arch in original_dataset["Architecture"]:
            arch["dataset_id"] = new_dataset_id
            arch["user_id"] = user_id
        clone_data_query = f'mutation insert_new_archs($archs: [Architecture_insert_input!]!) {{ insert_Architecture(objects: $archs) {{ affected_rows returning {{ id }} }} }}'
        self.execute_query(clone_data_query, {"archs": original_dataset["Architecture"]})
        return new_dataset_id

    def clone_default_dataset(self, origin_dataset_id, user_id):
        return self.clone_dataset(origin_dataset_id, user_id, "default")

    def new_dataset(self, user_id, problem_id, dataset_name, group_id=1):
        mutation = f'mutation {{insert_Dataset_one(object: {{group_id: {group_id}, problem_id: {problem_id}, user_id: {user_id}, name: "{dataset_name}" }}) {{id}} }}'
        return self.execute_query(mutation)



    def insert_user_into_group(self, user_id, group_id=1):
        mutation = 'mutation { insert_Join__AuthUser_Group(objects: {group_id: '+str(group_id)+', user_id: ' + str(user_id) + ', admin: true}) { returning { group_id user_id id }}}'
        return self.execute_query(mutation)

    def execute_query(self, query, variables=None):
        json_body = {'query': query }
        if variables is not None:
            json_body['variables'] = variables
        r = requests.post(self.hasura_url, json=json_body)
        result = json.loads(r.text)
        # print('\n-------- Query Result --------')
        # print('----> URL:', self.hasura_url)
        # print('--> QUERY:', query)
        # pprint(result)
        # print('-------------------------\n')
        return result

    # Return architecture details after vassar evaluates
    def subscribe_to_architecture(self, input, problem_id, dataset_id, timeout=1000):
        query = f'query subscribe_to_architecture {{ Architecture_aggregate(where: {{problem_id: {{_eq: {problem_id} }}, dataset_id: {{_eq: {dataset_id} }}, input: {{_eq: "{input}"}}, eval_status: {{_eq: true }} }})  {{ aggregate {{ count }} }} }}'

        # Check for an entry every second
        counter = 0
        while int(self.execute_query(query)['data']['Architecture_aggregate']['aggregate']['count']) == 0:
            print('---> waiting for architecture: ' + str(counter))
            time.sleep(3)
            counter = counter + 1
            if counter >= timeout:
                return False
        
        query = f'query get_architecture {{ Architecture(where: {{problem_id: {{_eq: {problem_id} }}, dataset_id: {{_eq: {dataset_id} }}, input: {{_eq: "{input}"}} }})  {{ id input science cost }} }}'
        return self.execute_query(query)

    def get_architecture(self, arch_id: int):
        query = f'query get_architecture {{ Architecture(where: {{id: {{_eq: {arch_id} }} }}) {{ id input science cost ga }} }}'
        return self.execute_query(query)["data"]["Architecture"][0]

    def unevaluate_architecture(self, arch_id: int):
        query = f'''
        mutation unevaluate_architecture {{
            result: update_Architecture(where: {{id: {{_eq: {arch_id} }} }}, _set: {{eval_status: false}}) {{
                affected_rows
            }}
        }}'''
        return self.execute_query(query)["data"]["result"]["affected_rows"] > 0