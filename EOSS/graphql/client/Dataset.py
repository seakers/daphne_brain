import timeit

from EOSS.graphql.client.Abstract import AbstractGraphqlClient as Client
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
            }
            PanelScoreExplanations {
              satisfaction
              objective_id
              id
              architecture_id
            }
            ObjectiveScoreExplanations {
              subobjective_id
              satisfaction
              id
              architecture_id
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
        result = await self._execute(query)
        if 'Dataset' not in result:
            return None
        if len(result['Dataset']) == 0:
            return None
        return result['Dataset'][0]

    async def get_default_dataset(self):
        query = await self.wrap_query(
            """
            query dataset_id {
                Dataset(
                    where: {name: {_eq: "default"}, problem_id: {_eq: %d}, user_id: {_is_null: true}, group_id: {_is_null: true}}
                ) {
                    id
                }
            }
            """ % (self.problem_id)
        )
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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

        # --> 2. Clone architectures
        await self.clone_architectures(source_id, target_id, costs=costs, scores=scores)
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

    ###########
    ### GET ###
    ###########

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

        result = await self._execute(query)
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
        query_start = """
                    query get_architectures {
                        Architecture(
                            where: {dataset_id: {_eq: %d}, problem_id: {_eq: %d}}
                        ) { 
                """ % (dataset_id, problem_id)
        query_end = """
                        }
                    } 
                """
        query = await self.wrap_query(query_start + info_list + query_end)

        # --> 4. Run query
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
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
        result = await self._execute(query)
        if 'Architecture' not in result:
            return None
        return result['Architecture']


    #############
    ### CLONE ###
    #############

    async def clone_architectures(self, source_id, target_id, costs=False, scores=False):

        # --> 1. Get architectures from source dataset
        architectures = await self.get_architectures(dataset_id=source_id, costs=costs, scores=scores)

        # --> 2. Open new process to clone archs
        arch_strings = await self._proc(self._proc_clone_architecture_strings, architectures, target_id, costs, scores)

        # --> 3. Build mutation
        mutation_string = """
                mutation insert_architectures {
                    insert_Architecture(
                        objects: %s
                    ) {
                        returning {
                            id
                        }
                    }
                }
            """ % (arch_strings)
        # await sync_to_async(self.save_to_file)(mutation_string, 'mutation.json')
        mutation = await self.wrap_query(mutation_string)

        # --> 4. Execute mutation
        result = await self._execute(mutation)

    # ---------------------------------------------- SYNC -----------------------------------------------
    def _proc_clone_architecture_strings(self, architectures, database_id, costs=False, scores=False):
        arch_list = []
        for idx, arch in enumerate(architectures):
            arch_list.append(self._clone_architecture(arch, database_id, costs=costs, scores=scores))

        result = '[' + ','.join(arch_list) + ']'
        return result

    def _clone_architecture(self, architecture, dataset_id, costs=False, scores=False):

        def convert_bool(input):
            if bool(input) is True:
                return "true"
            else:
                return "false"

        cost_string = """"""
        if costs is True:
            cost_info = self._clone_architecture_cost_info(architecture)
            cost_string = """ArchitectureCostInformations: {data: %s},""" % cost_info

        score_string = """"""
        if scores is True:
            score_info = self._clone_architecture_score_info(architecture)
            score_string = """
                ArchitectureScoreExplanations: {data: %s}, 
                PanelScoreExplanations: {data: %s},
                ObjectiveScoreExplanations: {data: %s},  
                SubobjectiveScoreExplanations: {data: %s},
            """ % (
                score_info['architecture'],
                score_info['panel'],
                score_info['objective'],
                score_info['subobjective']
            )

        eval_status = True
        if costs is False or scores is False:
            eval_status = False

        clone = """{
              %s 
              %s 
              cost: %f, 
              critique: "%s", 
              data_continuity: %f, 
              dataset_id: %d, 
              eval_idx: %d, 
              eval_status: %s, 
              fairness: %f, 
              ga: %s, 
              improve_hv: %s, 
              input: "%s", 
              problem_id: %d, 
              programmatic_risk: %f, 
              science: %f, 
              user_id: %d
            }
            """ % (
            cost_string,
            score_string,
            float(architecture['cost']),
            architecture['critique'],
            architecture['data_continuity'],
            int(dataset_id),
            architecture['eval_idx'],
            convert_bool(eval_status),
            float(architecture['fairness']),
            convert_bool(architecture['ga']),
            convert_bool(architecture['improve_hv']),
            architecture['input'],
            architecture['problem_id'],
            float(architecture['programmatic_risk']),
            float(architecture['science']),
            architecture['user_id']
        )

        return clone

    def _clone_architecture_score_info(self, architecture):

        # --> 1. Create score info
        score_info = {
            'architecture': '[',
            'panel': '[',
            'objective': '[',
            'subobjective': '['
        }

        # --> 2. Clone architecture score info
        for idx, info in enumerate(architecture['ArchitectureScoreExplanations']):
            object = """
                {panel_id: %d, satisfaction: %f}
            """ % (int(info['panel_id']), float(info['satisfaction']))
            score_info['architecture'] += object
            if (idx + 1) != len(architecture['ArchitectureScoreExplanations']):
                score_info['architecture'] += ', '
        score_info['architecture'] += ']'

        # --> 3. Clone panel score info
        for idx, info in enumerate(architecture['PanelScoreExplanations']):
            object = """
                {objective_id: %d, satisfaction: %f}
            """ % (int(info['objective_id']), float(info['satisfaction']))
            score_info['panel'] += object
            if (idx + 1) != len(architecture['PanelScoreExplanations']):
                score_info['panel'] += ', '
        score_info['panel'] += ']'

        # --> 4. Clone objective score info
        for idx, info in enumerate(architecture['ObjectiveScoreExplanations']):
            object = """
                {subobjective_id: %d, satisfaction: %f}
            """ % (int(info['subobjective_id']), float(info['satisfaction']))
            score_info['objective'] += object
            if (idx + 1) != len(architecture['ObjectiveScoreExplanations']):
                score_info['objective'] += ', '
        score_info['objective'] += ']'

        # --> 5. Clone subobjective score info
        for idx, info in enumerate(architecture['SubobjectiveScoreExplanations']):
            object = """
                {taken_by: "%s", subobjective_id: %d, score: %f}
            """ % (str(info['taken_by']), int(info['subobjective_id']), float(info['score']))
            score_info['subobjective'] += object
            if (idx + 1) != len(architecture['SubobjectiveScoreExplanations']):
                score_info['subobjective'] += ', '
        score_info['subobjective'] += ']'

        # architecture_score = '{data: {panel_id: 10, satisfaction: ""}}'
        # panel_score = '{data: {satisfaction: "", objective_id: 10}}'
        # objective_score = '{data: {subobjective_id: 10, satisfaction: ""}}'
        # subobjective_score = '{data: {taken_by: "", subobjective_id: 10, score: "", measurement_attribute_values: "", justifications: ""}}'

        return score_info

    def _clone_architecture_cost_info(self, architecture):
        all_cost_info = '['

        for idx, info in enumerate(architecture['ArchitectureCostInformations']):
            budget_info = self._clone_architecture_budget_info(info)
            payload_info = self._clone_architecture_payload_info(info)
            cost_info = """
                {
                    ArchitectureBudgets: {data: %s}, 
                    ArchitecturePayloads: {data: %s}, 
                    power: %f, 
                    others: %f, 
                    mission_name: "%s", 
                    mass: %f, 
                    launch_vehicle: "%s", 
                    cost: %f
                }
            """ % (
                budget_info,
                payload_info,
                float(info['power']),
                float(info['others']),
                str(info['mission_name']),
                float(info['mass']),
                info['launch_vehicle'],
                float(info['cost'])
            )
            all_cost_info += cost_info
            if (idx + 1) != len(architecture['ArchitectureCostInformations']):
                all_cost_info += ', '
        all_cost_info += ']'

        return all_cost_info

    def _clone_architecture_budget_info(self, cost_info):
        all_budget_info = '['

        for idx, budget in enumerate(cost_info['ArchitectureBudgets']):
            budget_info = """
                {mission_attribute_id: %d, value: %f}
            """ % (int(budget['mission_attribute_id']), float(budget['value']))
            all_budget_info += budget_info
            if (idx + 1) != len(cost_info['ArchitectureBudgets']):
                all_budget_info += ', '
        all_budget_info += ']'

        return all_budget_info

    def _clone_architecture_payload_info(self, cost_info):
        all_payload_info = '['

        for idx, budget in enumerate(cost_info['ArchitecturePayloads']):
            payload_info = """
                {instrument_id: %d}
            """ % (int(budget['instrument_id']))
            all_payload_info += payload_info
            if (idx + 1) != len(cost_info['ArchitecturePayloads']):
                all_payload_info += ', '
        all_payload_info += ']'

        return all_payload_info
    # ---------------------------------------------------------------------------------------------------

    # ---------------------------------------------- ASYNC ----------------------------------------------
    async def clone_architectures_slow(self, source_id, target_id, costs=False, scores=False):

        # --> 1. Get architectures from source dataset
        architectures = await self.get_architectures(dataset_id=source_id, costs=costs, scores=scores)

        # --> 2. Clone architectures
        arch_strings = ''
        for idx, arch in enumerate(architectures):
            cloned_arch = await self.clone_architecture(arch, target_id, costs=costs, scores=scores)
            # if idx == 0:
            #     await sync_to_async(self.save_to_file)(cloned_arch, 'arch.json')
            arch_strings += cloned_arch
            if (idx + 1) != len(architectures):
                arch_strings += ', '

        # --> 3. Build mutation
        mutation_string = """
            mutation insert_architectures {
                insert_Architecture(
                    objects: [%s]
                ) {
                    returning {
                        id
                    }
                }
            }
        """ % (arch_strings)
        # await sync_to_async(self.save_to_file)(mutation_string, 'mutation.json')
        mutation = await self.wrap_query(mutation_string)

        # --> 4. Execute mutation
        result = await self._execute(mutation)

    async def clone_architecture(self, architecture, dataset_id, costs=False, scores=False):

        async def convert_bool(input):
            if bool(input) is True:
                return "true"
            else:
                return "false"

        cost_string = """"""
        if costs is True:
            cost_info = await self.clone_architecture_cost_info(architecture)
            cost_string = """ArchitectureCostInformations: {data: %s},""" % cost_info

        score_string = """"""
        if scores is True:
            score_info = await self.clone_architecture_score_info(architecture)
            score_string = """
                ArchitectureScoreExplanations: {data: %s}, 
                PanelScoreExplanations: {data: %s},
                ObjectiveScoreExplanations: {data: %s},  
                SubobjectiveScoreExplanations: {data: %s},
            """ % (
                score_info['architecture'],
                score_info['panel'],
                score_info['objective'],
                score_info['subobjective']
            )

        eval_status = True
        if costs is False or scores is False:
            eval_status = False

        clone = """{
              %s 
              %s 
              cost: %f, 
              critique: "%s", 
              data_continuity: %f, 
              dataset_id: %d, 
              eval_idx: %d, 
              eval_status: %s, 
              fairness: %f, 
              ga: %s, 
              improve_hv: %s, 
              input: "%s", 
              problem_id: %d, 
              programmatic_risk: %f, 
              science: %f, 
              user_id: %d
            }
            """ % (
            cost_string,
            score_string,
            float(architecture['cost']),
            architecture['critique'],
            architecture['data_continuity'],
            int(dataset_id),
            architecture['eval_idx'],
            await convert_bool(eval_status),
            float(architecture['fairness']),
            await convert_bool(architecture['ga']),
            await convert_bool(architecture['improve_hv']),
            architecture['input'],
            architecture['problem_id'],
            float(architecture['programmatic_risk']),
            float(architecture['science']),
            architecture['user_id']
        )

        return clone

    async def clone_architecture_score_info(self, architecture):

        # --> 1. Create score info
        score_info = {
            'architecture': '[',
            'panel': '[',
            'objective': '[',
            'subobjective': '['
        }

        # --> 2. Clone architecture score info
        for idx, info in enumerate(architecture['ArchitectureScoreExplanations']):
            object = """
                {panel_id: %d, satisfaction: %f}
            """ % (int(info['panel_id']), float(info['satisfaction']))
            score_info['architecture'] += object
            if (idx + 1) != len(architecture['ArchitectureScoreExplanations']):
                score_info['architecture'] += ', '
        score_info['architecture'] += ']'

        # --> 3. Clone panel score info
        for idx, info in enumerate(architecture['PanelScoreExplanations']):
            object = """
                {objective_id: %d, satisfaction: %f}
            """ % (int(info['objective_id']), float(info['satisfaction']))
            score_info['panel'] += object
            if (idx + 1) != len(architecture['PanelScoreExplanations']):
                score_info['panel'] += ', '
        score_info['panel'] += ']'

        # --> 4. Clone objective score info
        for idx, info in enumerate(architecture['ObjectiveScoreExplanations']):
            object = """
                {subobjective_id: %d, satisfaction: %f}
            """ % (int(info['subobjective_id']), float(info['satisfaction']))
            score_info['objective'] += object
            if (idx + 1) != len(architecture['ObjectiveScoreExplanations']):
                score_info['objective'] += ', '
        score_info['objective'] += ']'

        # --> 5. Clone subobjective score info
        for idx, info in enumerate(architecture['SubobjectiveScoreExplanations']):
            object = """
                {taken_by: "%s", subobjective_id: %d, score: %f}
            """ % (str(info['taken_by']), int(info['subobjective_id']), float(info['score']))
            score_info['subobjective'] += object
            if (idx + 1) != len(architecture['SubobjectiveScoreExplanations']):
                score_info['subobjective'] += ', '
        score_info['subobjective'] += ']'

        # architecture_score = '{data: {panel_id: 10, satisfaction: ""}}'
        # panel_score = '{data: {satisfaction: "", objective_id: 10}}'
        # objective_score = '{data: {subobjective_id: 10, satisfaction: ""}}'
        # subobjective_score = '{data: {taken_by: "", subobjective_id: 10, score: "", measurement_attribute_values: "", justifications: ""}}'

        return score_info

    async def clone_architecture_cost_info(self, architecture):
        all_cost_info = '['

        for idx, info in enumerate(architecture['ArchitectureCostInformations']):
            budget_info = await self.clone_architecture_budget_info(info)
            payload_info = await self.clone_architecture_payload_info(info)
            cost_info = """
                {
                    ArchitectureBudgets: {data: %s}, 
                    ArchitecturePayloads: {data: %s}, 
                    power: %f, 
                    others: %f, 
                    mission_name: "%s", 
                    mass: %f, 
                    launch_vehicle: "%s", 
                    cost: %f
                }
            """ % (
                budget_info,
                payload_info,
                float(info['power']),
                float(info['others']),
                str(info['mission_name']),
                float(info['mass']),
                info['launch_vehicle'],
                float(info['cost'])
            )
            all_cost_info += cost_info
            if (idx + 1) != len(architecture['ArchitectureCostInformations']):
                all_cost_info += ', '
        all_cost_info += ']'

        return all_cost_info

    async def clone_architecture_budget_info(self, cost_info):
        all_budget_info = '['

        for idx, budget in enumerate(cost_info['ArchitectureBudgets']):
            budget_info = """
                {mission_attribute_id: %d, value: %f}
            """ % (int(budget['mission_attribute_id']), float(budget['value']))
            all_budget_info += budget_info
            if (idx + 1) != len(cost_info['ArchitectureBudgets']):
                all_budget_info += ', '
        all_budget_info += ']'

        return all_budget_info

    async def clone_architecture_payload_info(self, cost_info):
        all_payload_info = '['

        for idx, budget in enumerate(cost_info['ArchitecturePayloads']):
            payload_info = """
                {instrument_id: %d}
            """ % (int(budget['instrument_id']))
            all_payload_info += payload_info
            if (idx + 1) != len(cost_info['ArchitecturePayloads']):
                all_payload_info += ', '
        all_payload_info += ']'

        return all_payload_info
    # ---------------------------------------------------------------------------------------------------

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
        result = await self._execute(query)
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
        result = await self._execute(query)
        if 'items' not in result:
            return False, None
        count = result['items']['aggregate']['count']
        arch_id = None
        if count > 0:
            arch_id = result["items"]["nodes"][0]["id"]

    #################
    ### SUBSCRIBE ###
    #################

    async def subscribe_to_architecture(self, input, dataset_id=None):
        # --> 1. Determine dataset_id
        used_dataset_id = await self._dataset_id(dataset_id)

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
                }
            }
            """ % (used_dataset_id, self.problem_id, input)
        )
        return await Client._subscribe(subscription)





