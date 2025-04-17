import logging

from EOSS.data_mining.api import DataMiningClient
import json
from EOSS.analyst.helpers import get_feature_unsatisfied, get_feature_satisfied, feature_expression_to_string
import math
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture
from EOSS.models import EOSSContext


logger = logging.getLogger('EOSS.analyst')


def data_mining_run(designs, design_id, context, session_key, problem):
    print("in data mining run")
    client = DataMiningClient()
    try:
        # Start connection with data_mining
        print("designs", designs)
        print("design_id", design_id)
        designs_list = list(designs.values())
        print("designs_list", designs_list[0])
        this_design = designs.get(id=design_id)

        if this_design is None:
            raise ValueError("Design id {} not found in the database".format(design_id))
        print("context", context)
        client.startConnection()

        support_threshold = 0.002
        confidence_threshold = 0.2
        lift_threshold = 1

        behavioral = []
        non_behavioral = []

        print("designs", designs)
        print("this_design", this_design)

        eosscontext = EOSSContext.objects.get(id=context["screen"]["id"])

        #---------------------

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

        print("behavioral", behavioral)
        print("non_behavioral", non_behavioral)

        # Extract feature
        problem_type = "binary"
        _archs = []
        if problem_type == "binary":
            for arch in designs:
                _archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = client.client.getDrivingFeaturesEpsilonMOEABinary(session_key, problem, behavioral,
                                                                            non_behavioral, _archs)

        elif problem_type == "discrete":
            for arch in designs:
                _archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = client.client.getDrivingFeaturesEpsilonMOEADiscrete(session_key, problem, behavioral,
                                                                            non_behavioral, _archs)
        else:
            raise ValueError("Problem type not implemented")
        
        features = []
        for df in _features:
            features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})
        print("features", features)
        # advices = []
        # if not len(features) == 0:

        #     # Compare features to the current design
        #     unsatisfied = get_feature_unsatisfied(features[0]['name'], this_design, eosscontext)
        #     satisfied = get_feature_satisfied(features[0]['name'], this_design, eosscontext)

        #     if type(unsatisfied) is not list:
        #         unsatisfied = [unsatisfied]

        #     if type(satisfied) is not list:
        #         satisfied = [satisfied]

        #     for exp in unsatisfied:
        #         if exp == "":
        #             continue
        #         print("bad feature expressions")
        #         advices.append(
        #             "Based on the data mining result, I advise you to make the following change: " +
        #             feature_expression_to_string(exp, is_critique=True, context=eosscontext))

        #     for exp in satisfied:
        #         print("good features")
        #         if exp == "":
        #             continue
        #         advices.append(
        #             "Based on the data mining result, these are the good features. Consider keeping them: " +
        #             feature_expression_to_string(exp, is_critique=False, context=eosscontext))
                

        advices = []
        for feature in features[0:3]:
            advices.append(
                feature_expression_to_string(feature['name'], is_critique=False, context=eosscontext)
            )

        result = []
        for advice in advices:
            result.append({
                                "type": "Analyzer",
                                "advice": advice
                            })


        # End the connection before return statement
        client.endConnection()

        # for i in range(len(advices)):  # Generate answers for the first 5 features
        #     advice = advices[i]
        #     result.append({
        #         "type": "Analyst",
        #         "advice": advice
        #     })
        print("data mining result", result)
        return result
                                
    except Exception:
        logger.exception('Exception in running data mining')
        client.endConnection()
        return None
    #     if len(dataset) < 10:
    #         raise ValueError("Could not run data mining: the number of samples is less than 10")
    #     else:
    #         utopiaPoint = [1, 0]
    #         temp = []
    #         # Select the top N% archs based on the distance to the utopia point
    #         for design in dataset:
    #             outputs = design["outputs"]
    #             id = design["id"]
    #             dist = math.sqrt((outputs[0] - utopiaPoint[0]) ** 2 + (outputs[1] - utopiaPoint[1]) ** 2)
    #             temp.append((id, dist))

    #         # Sort the list based on the distance to the utopia point
    #         temp = sorted(temp, key=lambda x: x[1])
    #         for i in range(len(temp)):
    #             if i <= len(temp) // 10:  # Label the top 10% architectures as behavioral
    #                 behavioral.append(temp[i][0])
    #             else:
    #                 non_behavioral.append(temp[i][0])

    #     # Extract feature
    #     _archs = []
    #     if problem_type == "assignation":
    #         for arch in dataset:
    #             _archs.append(BinaryInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
    #         _features = dm_client.client.getDrivingFeaturesEpsilonMOEABinary(session.session_key, problem_id,
    #                                                                          problem_type,
    #                                                                          behavioral, non_behavioral,
    #                                                                          _archs)

    #     elif problem_type == "discrete":
    #         for arch in dataset:
    #             _archs.append(DiscreteInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
    #         _features = dm_client.client.getDrivingFeaturesEpsilonMOEADiscrete(session.session_key, problem_id,
    #                                                                            problem_type,
    #                                                                            behavioral, non_behavioral,
    #                                                                            _archs)
    #     else:
    #         raise ValueError("Problem type not implemented")

    #     features = []
    #     for df in _features:
    #         features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})
    #         print('--> FEATURE:', df)


    #     advices = []
    #     is_expert = user_information.is_domain_expert
    #     for feature in features[0:3]:
    #         advices.append(
    #             feature_expression_to_string(feature['name'], is_critique=not is_expert, context=context, user_info=user_information)
    #         )

    #     result = []
    #     for advice in advices:
    #         result.append({
    #                             "type": "Analyzer",
    #                             "advice": advice
    #                         })

    #     # -------
    #     print('--> EXTRACTED RESULTS')
    #     for f in result:
    #         print('--> ', f)

    #     return result

    # except Exception as e:
    #     logger.exception('Exception in running data mining')
    #     print('--> EXCEPTION', e)
    #     dm_client.endConnection()
    #     return None


        # features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
        # # features = client.runAutomatedLocalSearch(behavioral, non_behavioral, designs, support_threshold,
        # #                                           confidence_threshold, lift_threshold)

        # # End the connection before return statement
        # client.endConnection()

        # result = []
        # max_features = 3
        # if len(features) > 3:
        #     pass
        # else:
        #     max_features = len(features)

        # for i in range(max_features):  # Generate answers for the first 3 features
        #     advice = feature_expression_to_string(features[i]['name'], context)
        #     result.append({
        #         "type": "Analyzer",
        #         "advice": advice
        #     })
        # return result

    