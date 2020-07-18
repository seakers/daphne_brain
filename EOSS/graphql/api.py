

import requests
import json
import time




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



class GraphqlClient:

    def __init__(self, hasura_url='http://graphql:8080/v1/graphql'):
        self.hasura_url = hasura_url
        self.problem_id = str(5)



    def get_architectures(self, problem_id=5):
        problem_id = str(problem_id)
        query = ' query get_architectures { Architecture(where: {problem_id: {_eq: ' + self.problem_id + '}}) { id input cost science eval_status } } '
        return self.execute_query(query)

    def get_orbit_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        # query = ' query get_orbit_list { Join__Orbit_Attribute(where: {problem_id: {_eq: ' + problem_id + '}}, distinct_on: orbit_id) { Orbit { id name } } } '
        query = ' query get_orbit_list { Join__Problem_Orbit(where: {problem_id: {_eq: ' + self.problem_id + '}}){ Orbit { id name } } } '
        return self.execute_query(query)

    def get_instrument_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_instrument_list { Join__Problem_Instrument(where: {problem_id: {_eq: ' + self.problem_id + '}}) { Instrument { id name } } } '
        return self.execute_query(query)

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
    
    
    
    
    
    def get_arch_id(self, arch_object):
        id = arch_object.id
        inputs = bool_list_to_string(arch_object.inputs)
        outputs = arch_object.outputs
        print("--> Finding django arch:", self.problem_id, inputs)
        query = 'query myquery { Architecture(where: {problem_id: {_eq: ' + self.problem_id + '}, input: {_eq: "' + inputs + '"}}) { id } }'
        return self.execute_query(query)['data']['Architecture'][0]['id']
        







    def execute_query(self, query):
        r = requests.post(self.hasura_url, json={'query': query })
        result = json.loads(r.text)
        print('\n-------- Query Result --------')
        print(result)
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







