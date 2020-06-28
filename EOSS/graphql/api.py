

import requests
import json
import time





class GraphqlClient:

    def __init__(self, hasura_url='http://graphql:8080/v1/graphql'):
        self.hasura_url = hasura_url



    def get_architectures(self, problem_id=5):
        problem_id = str(problem_id)
        query = ' query get_architectures { Architecture(where: {problem_id: {_eq: ' + problem_id + '}}) { id input cost science } } '
        return self.execute_query(query)


    def get_orbit_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_orbit_list { Orbit(where: {group_id: {_eq: ' + group_id + '}}) { id name } } '
        return self.execute_query(query)

    def get_instrument_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_instrument_list { Instrument(where: {Join__Problem_Instruments: {problem_id: {_eq: ' + problem_id + '}}})  { id name } } '
        return self.execute_query(query)

    def get_objective_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_objective_list { Stakeholder_Needs_Objective(where: {Problem: {id: {_eq: ' + problem_id + '}}})  { id name description panel_id problem_id weight} } '
        return self.execute_query(query)

    def get_subobjective_list(self, group_id, problem_id):
        group_id = str(group_id)
        problem_id = str(problem_id)
        query = ' query get_subobjective_list { Stakeholder_Needs_Subobjective(where: {Problem: {id: {_eq: ' + problem_id + '}}})  { id name description problem_id weight} } '
        return self.execute_query(query)

    def execute_query(self, query):
        r = requests.post(self.hasura_url, json={'query': query })
        result = json.loads(r.text)
        print('\n\n-------- Query Result --------')
        print(result)
        print('-------------------------\n\n')

        return result

    # Return architecture details after vassar evaluates
    def subscribe_to_architecture(self, input, problem_id, timeout=1000):
        query = ' query subscribe_to_architecture { Architecture_aggregate(where: {problem_id: {_eq: ' + str(problem_id) + '}, input: {_eq: "' + str(input) + '"}})  {aggregate { count }} } '

        # Check for an entry every second
        counter = 0
        while int(self.execute_query(query)['data']['Architecture_aggregate']['aggregate']['count']) == 0:
            print('---> waiting for architecture: ' + str(counter))
            time.sleep(3)
            counter = counter + 1
            if counter >= timeout:
                return False
        
        query = ' query get_architecture { Architecture(where: {problem_id: {_eq: ' + str(problem_id) + '}, input: {_eq: "' + str(input) + '"}})  { id input science cost } } '
        return self.execute_query(query)







