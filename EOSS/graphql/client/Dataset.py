import timeit

from EOSS.graphql.client.Abstract import AbstractGraphqlClient as Client
from EOSS.graphql.generation.CloneGenerator import CloneGenerator
from daphne_context.models import UserInformation
from gql import gql
from asgiref.sync import async_to_sync, sync_to_async
from concurrent.futures import ProcessPoolExecutor
import asyncio

class DatasetGraphqlClient(Client):

    # --> Only the constructor is to touch the django ORM
    # --> All other methods are async
    def __init__(self, user_info: UserInformation):
        super().__init__(user_info)

        # --> Query strings
        self.info_base = """
            id
            user_id
            science
            problem_id
            input
            improve_hv
            ga
            eval_status
            dataset_id
            critique
            cost
        """
        self.info_costs = """
            ArchitectureCostInformations {
              power
              others
              mission_name
              mass
              launch_vehicle
              id
              cost
              architecture_id
              ArchitectureBudgets {
                value
                mission_attribute_id
                id
                arch_cost_id
              }
              ArchitecturePayloads {
                instrument_id
                id
                arch_cost_id
              }
            }
        """
        self.info_scores = """
            ArchitectureScoreExplanations {
                satisfaction
                panel_id
                id
                architecture_id
                Stakeholder_Needs_Panel {
                    id
                    name
                    index_id
                    weight
                    problem_id
                }
            }
            PanelScoreExplanations {
                satisfaction
                objective_id
                id
                architecture_id
                Stakeholder_Needs_Objective { 
                    name 
                    weight 
                }
            }
            ObjectiveScoreExplanations {
                subobjective_id
                satisfaction
                id
                architecture_id
                Stakeholder_Needs_Subobjective { 
                    name 
                    weight 
                }
            }
            SubobjectiveScoreExplanations {
              taken_by
              subobjective_id
              score
              attribute_values: measurement_attribute_values
              justifications
              id
              architecture_id
            }
        """
        self.into_experiment = """
            data_continuity
            fairness
            programmatic_risk
            eval_idx
        """

        # --> Initialization (handles case: dataset_id == -1)
        # async_to_sync(self.initialize)()

    def set_dataset(self, dataset_id):
        self.user_info.eosscontext.dataset_id = dataset_id
        self.user_info.eosscontext.save()
        self.user_info.save()

    async def initialize(self):
        if self.dataset_id == -1:

            # --> 1. Get default user dataset id (get)
            default_user_dataset = await self.get_default_user_dataset()
            if default_user_dataset is not None:
                await sync_to_async(self.set_dataset)(default_user_dataset['id'])
                return

            # --> 2. Get problem default dataset id (get or create)
            default_dataset = await self.get_default_dataset()
            if default_dataset is None:
                default_dataset = await self.new_default_dataset(save=False)
            default_dataset_id = default_dataset['id']

            # --> 3. Get default user dataset id (create)
            default_user_dataset = await self.new_user_default_dataset(save=True)
            default_user_dataset_id = default_user_dataset['id']

            # --> 4. Copy architectures to new default user dataset
            await self.clone_architectures(default_dataset_id, default_user_dataset_id, costs=True, scores=True)

    async def wrap_query(self, query):
        return query

    """
      _____        _                 _   
     |  __ \      | |               | |  
     | |  | | __ _| |_ __ _ ___  ___| |_ 
     | |  | |/ _` | __/ _` / __|/ _ \ __|
     | |__| | (_| | || (_| \__ \  __/ |_ 
     |_____/ \__,_|\__\__,_|___/\___|\__|   
    """

    async def _dataset_id(self, dataset_id=None):
        if dataset_id:
            return dataset_id
        return self.dataset_id

    ###########
    ### GET ###
    ###########

    async def get_dataset(self, dataset_id=None):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        query = await self.wrap_query(
            """
            query dataset_id {
                Dataset(
                    where: {id: {_eq: %d}}
                ) {
                    group_id
                    id
                    name
                    problem_id
                    user_id
                }
            }
            """ % (used_dataset_id)
        )
        result = await self._query(query)
        if 'Dataset' not in result:
            return None
        if len(result['Dataset']) == 0:
            return None
        return result['Dataset'][0]

    async def get_default_dataset(self, problem_id=None):
        if problem_id is None:
            problem_id = self.problem_id

        query = await self.wrap_query(
            """
            query dataset_id {
                Dataset(
                    where: {name: {_eq: "default"}, problem_id: {_eq: %d}, user_id: {_is_null: true}, group_id: {_is_null: true}}
                ) {
                    id
                }
            }
            """ % (problem_id)
        )
        result = await self._query(query)
        if 'Dataset' not in result:
            return None
        if len(result['Dataset']) == 0:
            return None
        return result['Dataset'][0]

    async def get_default_dataset_count(self):
        # --> 1. Create and run query
        query = await self.wrap_query(
            """
            query dataset_count {
                Dataset_aggregate(
                    where: {name: {_eq: "default"}, problem_id: {_eq: %d}, user_id: {_is_null: true}, group_id: {_is_null: true}}
                ) {
                    aggregate {
                      count
                    }
                }
            }
            """ % (self.problem_id)
        )
        result = await self._query(query)
        if 'Dataset_aggregate' not in result:
            return None
        return int(result['Dataset_aggregate']['aggregate']['count'])

    async def get_default_user_dataset(self):
        query = await self.wrap_query(
            """
            query dataset_id {
                Dataset(
                    where: {name: {_eq: "default"}, problem_id: {_eq: %d}, user_id: {_eq: %d}}
                ) {
                    id
                }
            }
            """ % (self.problem_id, self.user_id)
        )
        result = await self._query(query)
        if 'Dataset' not in result:
            return None
        if len(result['Dataset']) == 0:
            return None
        return result['Dataset'][0]

    async def get_default_user_dataset_count(self):
        # --> 1. Create and run query
        query = await self.wrap_query(
            """
            query dataset_count {
                Dataset_aggregate(
                    where: {name: {_eq: "default"}, problem_id: {_eq: %d}, user_id: {_eq: %d}}
                ) {
                    aggregate {
                      count
                    }
                }
            }
            """ % (self.problem_id, self.user_id)
        )
        result = await self._query(query)
        if 'Dataset_aggregate' not in result:
            return None
        return int(result['Dataset_aggregate']['aggregate']['count'])

    ###########
    ### NEW ###
    ###########

    async def new_user_dataset(self, name, save=True):
        query = await self.wrap_query(
            """
            mutation new_dataset {
                insert_Dataset_one(
                    object: {group_id: %d, problem_id: %d, user_id: %d, name: %s}
                ) {
                    id
                }
            }
            """ % (self.group_id, self.problem_id, self.user_id, name)
        )
        result = await self._query(query)
        if 'insert_Dataset_one' not in result:
            return None
        if save is True:
            id = result['insert_Dataset_one']['id']
            await sync_to_async(self.set_dataset)(id)
        return result['insert_Dataset_one']

    async def new_user_default_dataset(self, save=True):
        return await self.new_user_dataset("default", save=save)

    async def new_default_dataset(self, save=True):
        query = await self.wrap_query(
            """
            mutation new_dataset {
                insert_Dataset_one(
                    object: {name: "default", problem_id: %d, group_id: null,  user_id: null}
                ) {
                    id
                }
            }
            """ % (self.problem_id)
        )
        result = await self._query(query)
        if 'insert_Dataset_one' not in result:
            return None
        if save is True:
            id = result['insert_Dataset_one']['id']
            await sync_to_async(self.set_dataset)(id)
        return result['insert_Dataset_one']

    #############
    ### CLONE ###
    #############

    async def clone_dataset(self, source_id, name, save=True, costs=False, scores=False):

        # --> 1. Create new dataset
        new_dataset = await self.new_user_dataset(name, save=save)
        if new_dataset is None or 'id' not in new_dataset:
            return None
        target_id = new_dataset['id']

        # --> 2. Get architectures from source dataset
        architectures = await self.get_architectures(dataset_id=source_id, costs=costs, scores=scores)

        # --> 3. Open new process to clone archs
        arch_strings = await CloneGenerator(self.user_info).architectures(architectures, target_id, costs, scores)

        # --> 4. Build mutation
        mutation = """
            mutation insert_architectures {
                insert_Architecture(
                    objects: %s
                ) {
                    returning {
                        id
                    }
                }
            }
        """ % arch_strings
        # await sync_to_async(self._save)(mutation_string, 'mutation.json')

        # --> 5. Execute mutation and return new dataset id
        await self._query(mutation)


        return target_id

    #############
    ### CHECK ###
    #############

    async def check_dataset_read_only(self, dataset_id=None):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Create and run query
        dataset = await self.get_dataset(dataset_id=used_dataset_id)
        return (dataset['user_id'] is None) and (dataset['group_id'] is None)


    """
                        _     _ _            _                  
         /\            | |   (_) |          | |                 
        /  \   _ __ ___| |__  _| |_ ___  ___| |_ _   _ _ __ ___ 
       / /\ \ | '__/ __| '_ \| | __/ _ \/ __| __| | | | '__/ _ \
      / ____ \| | | (__| | | | | ||  __/ (__| |_| |_| | | |  __/
     /_/    \_\_|  \___|_| |_|_|\__\___|\___|\__|\__,_|_|  \___|           
    """

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

    ###########
    ### GET ###
    ###########

    async def get_architecture_critique(self, arch_id):
        architecture = await self.get_architecture_pk(arch_id)
        if architecture is None or architecture['critique'] is None:
            return []
        critique = architecture['critique']
        critiques = critique.split('|')
        return critiques[:-1]

    async def get_architecture_pk(self, arch_id, costs=False, scores=False):

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        query = """
            query get_architecture_pk {
                architecture: Architecture_by_pk(id: %d) {
                    %s
                }
            }
        """ % (int(arch_id), info_list)

        result = await self._query(query)
        if 'architecture' not in result:
            return None
        return result['architecture']

    async def get_architectures(self, dataset_id=None, problem_id=None, costs=True, scores=True):
        print('--> GETTING ARCHITECTURES')

        # --> 1. Determine dataset_id
        if dataset_id is None:
            dataset_id = self.dataset_id
        if problem_id is None:
            problem_id = self.problem_id

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        # --> 3. Build query
        query = """
            query get_architectures {
                Architecture(order_by: { id: asc }, where: {problem_id: {_eq: %s}, dataset_id: {_eq: %s}, _or: [{ga: {_eq: false}}, {ga: {_eq: true}, improve_hv: {_eq: true}}]}) {
                    %s
                }
            }
        """ % (int(problem_id), int(dataset_id), info_list)


        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_architectures_false(self, dataset_id=None):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Determine requested info
        info_list = self.info_base

        # --> 3. Build query
        query_start = """
                            query get_architectures {
                                Architecture(
                                    where: {dataset_id: {_eq: %d}, eval_status: {_eq: false}}
                                ) { 
                        """ % (used_dataset_id)
        query_end = """
                                }
                            } 
                        """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_architectures_ga(self, dataset_id=None, costs=True, scores=True):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        # --> 3. Build query
        query_start = """
            query get_architectures {
                Architecture(
                    where: {dataset_id: {_eq: %d}, ga: {_eq: true}, improve_hv: {_eq: true}, eval_status: {_eq: true}}
                ) { 
        """ % (used_dataset_id)
        query_end = """
                }
            } 
        """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_architectures_ga_all(self, dataset_id=None, costs=True, scores=True):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        # --> 3. Build query
        query_start = """
            query get_architectures {
                Architecture(
                    where: {dataset_id: {_eq: %d}, ga: {_eq: true}, eval_status: {_eq: true}}
                ) { 
        """ % (used_dataset_id)
        query_end = """
                }
            } 
        """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_architectures_user(self, dataset_id=None, costs=True, scores=True):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        # --> 3. Build query
        query_start = """
            query get_architectures {
                Architecture(
                    where: {dataset_id: {_eq: %d}, user_id: {_eq: %d}, eval_status: {_eq: true}}
                ) { 
        """ % (used_dataset_id, self.user_id)
        query_end = """
                }
            } 
        """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_architectures_user_all(self, dataset_id=None, costs=True, scores=True):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Determine requested info
        info_list = self.info_base
        if costs is True:
            info_list += self.info_costs
        if scores is True:
            info_list += self.info_scores

        # --> 3. Build query
        query_start = """
            query get_architectures {
                Architecture(
                    where: {dataset_id: {_eq: %d}, ga: {_eq: false}, eval_status: {_eq: true}}
                ) { 
        """ % (used_dataset_id)
        query_end = """
                }
            } 
        """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']

    async def get_subobjective_score_explanation(self, arch_id, subobjective):
        query = '''query MyQuery($arch_id: Int!, $subobjective_name: String!) {
            SubobjectiveScoreExplanation(where: { architecture_id: {_eq: $arch_id}, Stakeholder_Needs_Subobjective: {name: {_eq: $subobjective_name}}}) {
                measurement_attribute_values
                score
                taken_by
                justifications
            }
        }'''
        result = await self._query(query, {"arch_id": arch_id, "subobjective_name": subobjective})
        return result

    ###########
    ### SET ###
    ###########

    async def set_architecture_invalid(self, arch_id):

        # --> 1. Create mutation
        mutation = """
            mutation invalidate_architecture {
                item: update_Architecture(where: {id: {_eq: %d}}, _set: {eval_status: false}) {
                    affected_rows
                }
            }
        """ % int(arch_id)

        # --> 2. Execute mutation
        result = await self._query(mutation)
        if 'item' not in result:
            return False
        return int(result['item']['affected_rows']) > 0

    #############
    ### CHECK ###
    #############

    async def check_existing_architecture(self, input, dataset_id=None):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

        # --> 2. Create and run query
        query = await self.wrap_query(
            """
            query architecture_count {
                Architecture(
                    where: {dataset_id: {_eq: %d}, input: {_eq: "%s"}}
                ) 
                {
                    id
                }
            }
            """ % (used_dataset_id, str(input))
        )
        result = await self._query(query)
        if 'Architecture' not in result:
            return None
        if len(result['Architecture']) == 0:
            return None
        return result['Architecture'][0]

    async def check_existing_architecture_2(self, input, dataset_id=None, problem_id=None):

        # --> 1. Get parameter values
        if dataset_id is None:
            dataset_id = self.dataset_id
        if problem_id is None:
            problem_id = self.problem_id

        # --> 2. Create query
        query = """
            query check_existing_architecture2 {
                items: Architecture_aggregate(where: {problem_id: {_eq: %d}, dataset_id: {_eq: %d}, input: {_eq: "%s"}}) {
                    aggregate {
                        count
                    }
                    nodes {
                        id
                    }
                }
            }
        """ % (int(problem_id), int(dataset_id), await self._format_input(input))
        result = await self._query(query)
        if result is None or 'items' not in result:
            return False, None
        if int(result['items']['aggregate']['count']) > 0:
            arch_id = result["items"]["nodes"][0]["id"]
            return True, arch_id
        return False, None

    #################
    ### SUBSCRIBE ###
    #################

    async def subscribe_to_architecture(self, input, dataset_id=None, problem_id=None):
        # --> 1. Determine variables
        if dataset_id is None:
            dataset_id = self.dataset_id
        if problem_id is None:
            problem_id = self.problem_id

        # --> 2. Create and run subscription
        subscription = await self.wrap_query(
            """
            query dataset_count {
                item: Architecture_aggregate(
                    where: {dataset_id: {_eq: %d}, problem_id: {_eq: %d}, input: {_eq: "%s"}, eval_status: {_eq: true}}
                ) {
                    aggregate {
                      count
                    }
                    nodes {
                        %s
                    }
                }
            }
            """ % (dataset_id, problem_id, input, self.info_base)
        )
        return await Client._subscribe(subscription, tries=30, sleep_time=2)

    async def subscribe_to_critique(self, arch_id):
        for idx in range(5):
            query = await self.get_architecture_pk(arch_id)
            if query['critique'] is not None:
                critiques = query['critique'].split('|')
                return critiques[:-1]
            await asyncio.sleep(2)
        return []
