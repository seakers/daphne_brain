from EOSS.graphql.utils import _proc







class CloneGenerator:

    def __init__(self, user_info=None):
        self.init = 0
        self.user_info = user_info

        #####################
        ### EXAMPLE USAGE ###
        #####################

    ####################
    ### ARCHITECTURE ###
    ####################

    async def architectures(self, architectures, dataset_id, costs=False, scores=False):
        return await _proc(self._clone_architecture_strings, architectures, dataset_id, costs, scores)

    def _clone_architecture_strings(self, architectures, dataset_id, costs=False, scores=False):
        arch_list = []
        for idx, arch in enumerate(architectures):
            arch_list.append(self._clone_architecture(arch, dataset_id, costs=costs, scores=scores))
        return '[' + ','.join(arch_list) + ']'

    def _clone_architecture(self, architecture, dataset_id, costs=False, scores=False):

        def convert_bool(input):
            if bool(input) is True:
                return "true"
            else:
                return "false"

        # --> 1. Build cost string
        cost_string = """"""
        if costs is True:
            cost_info = self._clone_architecture_cost_info(architecture)
            cost_string = """ArchitectureCostInformations: {data: %s},""" % cost_info

        # --> 2. Build score string
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

        # --> 3. Ensure correct if user id is None
        user_id = architecture['user_id']
        if user_id is None:
            if self.user_info is not None:
                user_id = self.user_info.user.id
        else:
            user_id = int(user_id)

        # --> 4. Set eval status to false when cloning an arch without cost or score info
        eval_status = convert_bool(architecture['eval_status'])
        # if costs is False or scores is False:
        #     eval_status = False

        # --> 5. Compose final string
        clone = """{
              %s 
              %s 
              cost: %f, 
              critique: "%s", 
              dataset_id: %d, 
              eval_status: %s, 
              ga: %s, 
              improve_hv: %s, 
              input: "%s", 
              problem_id: %d, 
              science: %f, 
              user_id: %d
            }
            """ % (
            cost_string,
            score_string,
            float(architecture['cost']),
            architecture['critique'],
            # architecture['data_continuity'],
            int(dataset_id),
            # architecture['eval_idx'],
            eval_status,
            # float(architecture['fairness']),
            convert_bool(architecture['ga']),
            convert_bool(architecture['improve_hv']),
            architecture['input'],
            architecture['problem_id'],
            # float(architecture['programmatic_risk']),
            float(architecture['science']),
            user_id
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

    ###############
    ### PROBLEM ###
    ###############






