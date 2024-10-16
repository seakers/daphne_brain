import json
import math
import sys
import traceback

import numpy as np
from sqlalchemy.orm import sessionmaker

import EOSS.historian.models as models
import EOSS.data.problem_specific as problem_specific
from EOSS.analyst.helpers import get_feature_unsatisfied, get_feature_satisfied, \
    feature_expression_to_string
from EOSS.data.problem_helpers import assignation_problems, partition_problems
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture
from EOSS.models import EOSSContext
from EOSS.vassar.api import VASSARClient
from EOSS.data_mining.api import DataMiningClient
from daphne_context.models import UserInformation



def bool_list_to_string(bool_list_str, unpacked=False):
    if not unpacked:
        bool_list = json.loads(bool_list_str)
    else:
        bool_list = bool_list_str
    print("--> bool_list_to_string", bool_list)
    return_str = ''
    for bool_pos in bool_list:
        if bool_pos:
            return_str = return_str + '1'
        else:
            return_str = return_str + '0'
    return return_str

def boolean_string_to_boolean_array(boolean_string):
    return [b == "1" for b in boolean_string]



class Critic:

    def __init__(self, user_information: UserInformation, session_key):
        # Connect to the CEOS database
        self.engine = models.db_connect()
        self.session = sessionmaker(bind=self.engine)()
        self.user_information = user_information
        self.context = user_information.eosscontext
        self.instruments_dataset = problem_specific.get_instrument_dataset(self.context.problem_id)
        self.orbits_dataset = problem_specific.get_orbit_dataset(self.context.problem_id)
        self.session_key = session_key

    def get_missions_from_genome(self, problem_type, genome):
        missions = []
        if problem_type == 'assignation':
            missions = self.get_missions_from_bitstring(genome)
        elif problem_type == 'discrete':
            missions = self.get_missions_from_partition(genome)

        return missions

    def get_missions_from_bitstring(self, bitstring):
        missions = []
        num_instr = len(self.instruments_dataset)
        num_orbits = len(self.orbits_dataset)
        for orbit in range(num_orbits):
            mission = {"orbit": self.orbits_dataset[orbit]["name"], "instruments": []}

            for instr in range(num_instr):
                idx = orbit*num_instr + instr
                if bitstring[idx]:
                    mission["instruments"].append(self.instruments_dataset[instr])

            missions.append(mission)

        return missions

    def get_missions_from_partition(self, genome):
        missions = []
        # TODO: Retrieve all missions from genome

        return missions

    def orbits_similarity(self, mission_orbit, hist_mission):
        score = 0
        # Score orbit type
        if mission_orbit["type"] == hist_mission.orbit_type:
            score += 1
        # Score orbit altitude
        if hist_mission.orbit_altitude_num is not None and \
                                        int(mission_orbit["altitude"]) - 50 < hist_mission.orbit_altitude_num < int(mission_orbit["altitude"]) + 50:
            score += 1
        # Score orbit LST
        if mission_orbit["LST"] == hist_mission.orbit_LST:
            score += 1
        # Return orbit score
        return score

    def instruments_score(self, mission_instrument, hist_instrument):
        score = 0.0
        # Score instrument type
        for type2 in hist_instrument.types:
            if mission_instrument["type"] == type2.name:
                score += 1
                break
        # Score instrument technology
        if mission_instrument["technology"] == hist_instrument.technology:
            score += 1
        # Score instrument geometry
        for geometry2 in hist_instrument.geometries:
            if mission_instrument["geometry"] == geometry2.name:
                score += 1
                break
        # Score instrument wavebands
        for waveband1 in mission_instrument["wavebands"]:
            for waveband2 in hist_instrument.wavebands:
                if waveband1 == waveband2.name:
                    score += 1/len(mission_instrument["wavebands"])
                    break
        # Return instruments score
        return score

    def instruments_similarity(self, instruments1, instruments2):
        score = 0.0
        # Compute similarity matrix
        N = max(len(instruments1), len(instruments2))
        sim = np.zeros((N, N))
        for i1 in range(len(instruments1)):
            for i2 in range(len(instruments2)):
                sim[i1, i2] = self.instruments_score(instruments1[i1], instruments2[i2])
        # Find the best matches for i1xi2 (greedy)
        for k in range(len(instruments1)):
            i1i2 = np.argmax(sim)
            i1 = int(i1i2 / N)
            i2 = i1i2 % N
            score += sim[i1, i2]/len(instruments1)
            sim[i1, :] = 0
            sim[:, i2] = 0
        return score

    def missions_similarity(self, mission_orbit, mission_instruments, missions_database):
        max_score = -1
        max_mission = None
        # Iterate over all the missions in the database
        for hist_mission in missions_database:
            score = 0
            # Get orbits similarity
            score += self.orbits_similarity(mission_orbit, hist_mission)
            # If score bigger than a threshold
            if(score > 1):
                # Get instruments similarities
                score += self.instruments_similarity(mission_instruments, hist_mission.instruments)
            if score > max_score:
                max_score = score
                max_mission = hist_mission
        # Return result
        return [(max_score*10)/7, max_mission]

    def expert_critic(self, design):
        # Criticize architecture (based on rules)
        problem_id = self.context.problem_id
        client = VASSARClient(user_information=self.user_information)
        result_list = client.critique_architecture(problem_id, design)

        result = []
        for advice in result_list:
            advice = advice.strip()
            is_relevant = False
            is_cut = False
            if advice[0:2] == "E:":
                if self.user_information.is_domain_expert:
                    is_relevant = True
                    is_cut = True
            elif advice[0:2] == "N:":
                if not self.user_information.is_domain_expert:
                    is_relevant = True
                    is_cut = True
            else:
                is_relevant = True
            if is_relevant:
                if is_cut:
                    advice = advice[2:]
                result.append({
                    "type": "Expert",
                    "advice": advice
                })
        return result

    def explorer_critic(self, design):

        def get_advices_from_bit_string_diff(difference, has_expertise):
            out = []
            ninstr = len(self.instruments_dataset)

            for i in range(len(difference)):
                advice = []
                if not has_expertise:
                    if difference[i] == 1:
                        advice.append("Add")
                    elif difference[i] == -1:
                        advice.append("Remove")
                    else:
                        continue
                else:
                    advice.append("I found a similar but better design: By")
                    if difference[i] == 1:
                        advice.append("adding")
                    elif difference[i] == -1:
                        advice.append("removing")
                    else:
                        continue

                orbit_index = i // ninstr  # Floor division
                instr_index = i % ninstr  # Get the remainder
                advice.append("instrument {}".format(self.instruments_dataset[instr_index]['name']))

                if difference[i] == 1:
                    advice.append("to")
                elif difference[i] == -1:
                    advice.append("from")

                advice.append("orbit {}".format(self.orbits_dataset[orbit_index]['name']))

                advice = " ".join(advice)
                out.append(advice)

            print("--> get_advices_from_bit_string_diff", out, ninstr)
            if not out:
                return out
            out = ", and ".join(out)
            out = out[0].upper() + out[1:]
            return out

        original_outputs = design["outputs"]
        original_inputs = design["inputs"]
        problem_id = self.context.problem_id
        client = VASSARClient(user_information=self.user_information)

        archs = None
        advices = []
        problem_type = client.get_problem_type(problem_id)
        if problem_type == "assignation":
            archs = client.run_local_search(design["inputs"], problem_id, self.context.vassar_request_queue_url)

            for arch in archs:
                new_outputs = arch["outputs"]

                new_design_inputs = arch["inputs"]
                print("--> explorer_critic diff:", new_design_inputs, original_inputs)
                diff = [a - b for a, b in zip(new_design_inputs, original_inputs)]
                advice = [get_advices_from_bit_string_diff(diff, self.user_information.is_domain_expert)]
                costdiff = abs(round(new_outputs[0] - original_outputs[0], 3))
                sciencediff = abs(round(new_outputs[1] - original_outputs[0], 3))

                # TODO: Generalize the code for comparing each metric. Currently it assumes two metrics: science and cost
                if new_outputs[0] > original_outputs[0] and new_outputs[1] < original_outputs[1]:
                    # New solution dominates the original solution
                    if self.user_information.is_domain_expert:
                        advice.append("performance increases and cost decreases.")
                    else:
                        advice.append("to increase performance while also lowering the cost.")
                # elif new_outputs[0] > original_outputs[0]:
                #     advice.append(" to increase the science benefit by "+str(sciencediff)+", but the cost would go up by about $"+str(costdiff)+"M.")
                # elif new_outputs[1] < original_outputs[1]:
                #     advice.append(" to lower the cost by $"+str(costdiff)+"M but decrease science by "+str(sciencediff)+".")
                else:
                    continue

                advice = "".join(advice)
                advices.append(advice)
        elif problem_type == "discrete":
            archs = client.run_local_search(design["inputs"], problem_id, self.context.vassar_request_queue_url)
            # TODO: Add the delta code for discrete architectures
        
        result = []
        for advice in advices:
            result.append({
                "type": "Explorer",
                "advice": advice
            })
        return result

    def historian_critic(self, design):
        historian_feedback = []

        client = VASSARClient(user_information=self.user_information)
        problem_id = self.context.problem_id
        problem_type = client.get_problem_type(problem_id)

        # Convert architecture format
        missions = self.get_missions_from_genome(problem_type, design["inputs"])

        # Type 2: Mission by mission
        missions_database = self.session.query(models.Mission)
        for mission in missions:
            # Find the orbit information based in the name
            orbit_info = {}
            for orbit in self.orbits_dataset:
                if orbit["name"] == mission["orbit"]:
                    orbit_info = orbit
                    break
            # Find similar past missions from the information on the current mission, including orbit and instruments
            res = self.missions_similarity(orbit_info, mission["instruments"], missions_database)
            if len(mission["instruments"]) > 0:
                if res[0] < 6:
                    historian_feedback.append("""I noticed that nobody has ever flown a satellite with instruments of type: {} 
                    in the orbit: {}. This is great from an innovation standpoint, but be sure to check 
                    the Expert for some reasons this might not be a good idea!"""
                                              .format(", ".join([instr["type"] for instr in mission["instruments"]]),
                                                      mission["orbit"]))
                elif res[0] > 3:
                    historian_feedback.append("""I found a mission that is similar to your design in orbit {}: {}.
                    Would you like to see more information? Click <a target="_blank" href="http://database.eohandbook.com/database/missionsummary.aspx?missionID={}">here</a>"""
                                              .format(mission["orbit"], res[1].name, res[1].id))
                    # +
                    # '<br>'.join(["Instrument similar to %s (score: %.2f)" % \
                    #    (i[0], i[2]) for i in self.instruments_match_dataset(res[1].instruments)]) + '.')

        result = []
        for advice in historian_feedback:
            result.append({
                "type": "Historian",
                "advice": advice
            })
        return result

    def analyst_critic(self, this_design):
        result = []
        dm_client = DataMiningClient()

        vassar_client = VASSARClient(user_information=self.user_information)
        problem_id = self.context.problem_id
        problem_type = vassar_client.get_problem_type(problem_id)

        try:
            # Start connection with data_mining
            dm_client.startConnection()

            behavioral = []
            non_behavioral = []

            dataset = vassar_client.get_dataset_architectures(problem_id, self.context.dataset_id)

            if len(dataset) < 10:
                raise ValueError("Could not run data mining: the number of samples is less than 10")
            else:
                utopiaPoint = [1, 0]
                temp = []
                maxObjectives = [0, 0]
                # Find the maximum values of all objectives for normalization
                for design in dataset:
                    outputs = design["outputs"]
                    for index, output in enumerate(outputs):
                        maxObjectives[index] = max(maxObjectives[index], output)
                # Select the top N% archs based on the distance to the utopia point
                for design in dataset:
                    outputs = design["outputs"]
                    id = design["id"]
                    dist = math.sqrt(((outputs[0] - utopiaPoint[0])/(maxObjectives[0] - utopiaPoint[0])) ** 2 + ((outputs[1] - utopiaPoint[1])/(maxObjectives[1] - utopiaPoint[1])) ** 2)
                    temp.append((id, dist))

                # Sort the list based on the distance to the utopia point
                temp = sorted(temp, key=lambda x: x[1])
                for i in range(len(temp)):
                    if i <= len(temp) // 10:  # Label the top 10% architectures as behavioral
                        behavioral.append(temp[i][0])
                    else:
                        non_behavioral.append(temp[i][0])

            # Extract feature
            _archs = []
            if problem_type == "assignation":
                for arch in dataset:
                    _archs.append(BinaryInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
                _features = dm_client.client.getDrivingFeaturesEpsilonMOEABinary(self.session_key, problem_id, problem_type, 
                                                                                    behavioral, non_behavioral, _archs)

            elif problem_type == "discrete":
                for arch in dataset:
                    _archs.append(DiscreteInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
                _features = dm_client.client.getDrivingFeaturesEpsilonMOEADiscrete(self.session_key, problem_id, problem_type,
                                                                                    behavioral, non_behavioral, _archs)
            else:
                raise ValueError("Problem type not implemented")

            features = []
            for df in _features:
                features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})

            advices = []
            if not len(features) == 0:

                # Compare features to the current design
                unsatisfied = get_feature_unsatisfied(features[0]['name'], this_design, self.context)
                satisfied = get_feature_satisfied(features[0]['name'], this_design, self.context)

                if type(unsatisfied) is not list:
                    unsatisfied = [unsatisfied]

                if type(satisfied) is not list:
                    satisfied = [satisfied]

                for exp in unsatisfied:
                    if exp == "":
                        continue
                    if self.user_information.is_domain_expert:
                        advices.append(
                            "Based on my analysis of the best designs explored so far, I advise you to make the following changes: " +
                            feature_expression_to_string(exp, is_critique=True, context=self.context))
                    else:
                        advices.append(
                            "My analysis of the best designs explored so far revealed the following patterns: " +
                            feature_expression_to_string(exp, is_critique=False, context=self.context))

                for exp in satisfied:
                    if exp == "":
                        continue
                    if self.user_information.is_domain_expert:
                        advices.append(
                            "Based on my analysis of the best designs explored so far, I advise you to make the following changes: " +
                            feature_expression_to_string(exp, is_critique=True, context=self.context))
                    else:
                        advices.append(
                            "My analysis of the best designs explored so far revealed the following patterns: " +
                            feature_expression_to_string(exp, is_critique=False, context=self.context))

            # End the connection before return statement
            dm_client.endConnection()

            for i in range(len(advices)):  # Generate answers for the first 5 features
                advice = advices[i]
                result.append({
                    "type": "Analyst",
                    "advice": advice
                })
        except Exception as e:
            print("Exc in generating critic from data mining: " + str(e))
            traceback.print_exc(file=sys.stdout)
            dm_client.endConnection()

        return result
