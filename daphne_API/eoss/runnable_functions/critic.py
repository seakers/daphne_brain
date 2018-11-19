import json
import logging
import math
import sys
import traceback

from VASSAR_API.api import VASSARClient
from daphne_API import problem_specific
from daphne_API.critic.critic import CRITIC
from daphne_API.eoss.runnable_functions.helpers import get_feature_unsatisfied, get_feature_satisfied, \
    feature_expression_to_string
from daphne_API.models import UserInformation
from data_mining_API.api import DataMiningClient

logger = logging.getLogger('VASSAR')


def general_call(design_id, designs, context: UserInformation):
    port = context.eosscontext.vassar_port
    client = VASSARClient(port)
    critic = CRITIC(context.eosscontext.problem)

    try:
        this_design = None
        num_design_id = int(design_id)

        for design in designs:
            if num_design_id == design.id:
                this_design = design
                break

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))
        else:
            pass

        # Start connection with VASSAR
        client.startConnection()

        assignation_problems = ['SMAP', 'ClimateCentric']
        partition_problems = ['Decadal2017Aerosols']

        problem = context.eosscontext.problem
        if problem in assignation_problems:
            problem_type = 'binary'
        elif problem in partition_problems:
            problem_type = 'discrete'
        else:
            problem_type = 'unknown'

        # Criticize architecture (based on rules)

        result1 = None
        if problem in assignation_problems:
            result1 = client.client.getCritiqueBinaryInputArch(problem, json.loads(this_design.inputs))
        elif problem in partition_problems:
            result1 = client.client.getCritiqueDiscreteInputArch(problem, json.loads(this_design.inputs))

        result = []
        for advice in result1:
            result.append({
                "type": "Expert",
                "advice": advice
            })

        orbit_dataset = problem_specific.get_orbit_dataset(context.eosscontext.problem)
        instrument_dataset = problem_specific.get_instrument_dataset(context.eosscontext.problem)

        # Criticize architecture (based on explorer)
        def get_advices_from_bit_string_diff(diff):
            out = []
            ninstr = len(instrument_dataset)

            for i in range(len(diff)):
                advice = []
                if diff[i] == 1:
                    advice.append("add")
                elif diff[i] == -1:
                    advice.append("remove")
                else:
                    continue

                orbit_index = i // ninstr  # Floor division
                instr_index = i % ninstr  # Get the remainder
                advice.append("instrument {}".format(instrument_dataset[instr_index]['name']))

                if diff[i] == 1:
                    advice.append("to")
                elif diff[i] == -1:
                    advice.append("from")

                advice.append("orbit {}".format(orbit_dataset[orbit_index]['name']))

                advice = " ".join(advice)
                out.append(advice)

            out = ", and ".join(out)
            out = out[0].upper() + out[1:]
            return out

        original_outputs = json.loads(this_design.outputs)
        original_inputs = json.loads(this_design.inputs)

        archs = None
        advices = []
        if problem in assignation_problems:
            archs = client.client.runLocalSearchBinaryInput(problem, json.loads(this_design.inputs))

            for arch in archs:
                new_outputs = arch.outputs

                new_design_inputs = arch.inputs
                diff = [a - b for a, b in zip(new_design_inputs, original_inputs)]
                advice = [get_advices_from_bit_string_diff(diff)]

                # TODO: Generalize the code for comparing each metric. Currently it assumes two metrics: science and cost
                if new_outputs[0] > original_outputs[0] and new_outputs[1] < original_outputs[1]:
                    # New solution dominates the original solution
                    advice.append(" to increase the science benefit and lower the cost.")
                elif new_outputs[0] > original_outputs[0]:
                    advice.append(" to increase the science benefit (but cost may increase!).")
                elif new_outputs[1] < original_outputs[1]:
                    advice.append(" to lower the cost (but science may decrease too!).")
                else:
                    continue

                advice = "".join(advice)
                advices.append(advice)
        elif problem in partition_problems:
            archs = client.client.runLocalSearchDiscreteInput(problem, json.loads(this_design.inputs))

            # TODO: Add the delta code for discrete architectures

        client.endConnection()
        result2 = []
        for advice in advices:
            result2.append({
                "type": "Explorer",
                "advice": advice
            })
        result.extend(result2)

        # Criticize architecture (based on database)
        result3 = critic.criticize_arch(problem_type, json.loads(this_design.inputs))
        result.extend(result3)

        # Criticize architecture (based on data mining)
        result4 = []
        client = DataMiningClient()
        try:
            # Start connection with data_mining
            client.startConnection()

            support_threshold = 0.02
            confidence_threshold = 0.2
            lift_threshold = 1

            behavioral = []
            non_behavioral = []

            if len(designs) < 10:
                raise ValueError("Could not run data mining: the number of samples is less than 10")
            else:

                utopiaPoint = [0.26, 0]
                temp = []
                # Select the top N% archs based on the distance to the utopia point
                for design in designs:
                    outputs = json.loads(this_design.outputs)
                    id = design.id
                    dist = math.sqrt((outputs[0] - utopiaPoint[0]) ** 2 + (outputs[1] - utopiaPoint[1]) ** 2)
                    temp.append((id, dist))

                # Sort the list based on the distance to the utopia point
                temp = sorted(temp, key=lambda x: x[1])
                for i in range(len(temp)):
                    if i <= len(temp) // 10:  # Label the top 10% architectures as behavioral
                        behavioral.append(temp[i][0])
                    else:
                        non_behavioral.append(temp[i][0])

            # Extract feature
            # features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
            features = client.runAutomatedLocalSearch(problem, problem_type, behavioral, non_behavioral, designs,
                                                      support_threshold, confidence_threshold, lift_threshold)

            advices = []
            if not len(features) == 0:

                # Compare features to the current design
                unsatisfied = get_feature_unsatisfied(features[0]['name'], this_design, context)
                satisfied = get_feature_satisfied(features[0]['name'], this_design, context)

                if type(unsatisfied) is not list:
                    unsatisfied = [unsatisfied]

                if type(satisfied) is not list:
                    satisfied = [satisfied]

                for exp in unsatisfied:
                    if exp == "":
                        continue
                    advices.append(
                        "Based on the data mining result, I advise you to make the following change: " + feature_expression_to_string(
                            exp, is_critique=True, context=context))

                for exp in satisfied:
                    if exp == "":
                        continue
                    advices.append(
                        "Based on the data mining result, these are the good features. Consider keeping them: " + feature_expression_to_string(
                            exp, is_critique=False, context=context))

            # End the connection before return statement
            client.endConnection()

            for i in range(len(advices)):  # Generate answers for the first 5 features
                advice = advices[i]
                result4.append({
                    "type": "Analyst",
                    "advice": advice
                })

        except Exception as e:
            print("Exc in generating critic from data mining: " + str(e))
            traceback.print_exc(file=sys.stdout)
            client.endConnection()
            result4 = []

        result.extend(result4)

        # Send response
        return result

    except Exception:
        logger.exception('Exception in criticizing the architecture')
        client.endConnection()
        return None


def specific_call(design_id, agent, designs, context: UserInformation):
    critic = CRITIC(context.eosscontext.problem)
    client = VASSARClient()
    try:
        result = []
        result_arr = []
        num_design_id = int(design_id[1:])
        if agent == 'expert':
            # Start connection with VASSAR
            client.startConnection()
            # Criticize architecture (based on rules)
            result_arr = client.client.getCritique(json.loads(designs[num_design_id].inputs))
            client.endConnection()
        elif agent == 'historian':
            # Criticize architecture (based on database)
            result_arr = critic.historian_critic(json.loads(designs[num_design_id].inputs))
        elif agent == 'analyst':
            # Criticize architecture (based on database)
            result_arr = critic.analyst_critic(json.loads(designs[num_design_id].inputs))
        elif agent == 'explorer':
            # Criticize architecture (based on database)
            result_arr = critic.explorer_critic(json.loads(designs[num_design_id].inputs))
        # Send response
        for res in result_arr:
            result.append({'advice': res})
        return result

    except Exception:
        logger.exception('Exception in using a single agent to criticize the architecture')
        client.endConnection()
        return None
