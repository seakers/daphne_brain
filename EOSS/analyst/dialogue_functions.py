import logging
import math
from EOSS.analyst.helpers import feature_expression_to_string
from EOSS.data_mining.api import DataMiningClient
from EOSS.vassar.api import VASSARClient
from EOSS.data_mining.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture


logger = logging.getLogger('EOSS.analyst')

# purpose: call data-mining to search for features around the pareto front
def data_mining_run(context, user_information, session):
    dm_client = DataMiningClient()
    vassar_client = VASSARClient(user_information=user_information)

    problem_id = user_information.eosscontext.problem_id
    dataset_id = user_information.eosscontext.dataset_id
    problem_type = vassar_client.get_problem_type(problem_id)

    print('--> DATA MINING RUN:', problem_id, dataset_id, problem_type)

    try:
        # Start connection with data_mining
        dm_client.startConnection()

        behavioral = []
        non_behavioral = []

        dataset = vassar_client.get_dataset_architectures(problem_id, dataset_id)

        if len(dataset) < 10:
            raise ValueError("Could not run data mining: the number of samples is less than 10")
        else:
            utopiaPoint = [1, 0]
            temp = []
            # Select the top N% archs based on the distance to the utopia point
            for design in dataset:
                outputs = design["outputs"]
                id = design["id"]
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
        _archs = []
        if problem_type == "assignation":
            for arch in dataset:
                _archs.append(BinaryInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
            _features = dm_client.client.getDrivingFeaturesEpsilonMOEABinary(session.session_key, problem_id,
                                                                             problem_type,
                                                                             behavioral, non_behavioral,
                                                                             _archs)

        elif problem_type == "discrete":
            for arch in dataset:
                _archs.append(DiscreteInputArchitecture(arch["id"], arch["inputs"], arch["outputs"]))
            _features = dm_client.client.getDrivingFeaturesEpsilonMOEADiscrete(session.session_key, problem_id,
                                                                               problem_type,
                                                                               behavioral, non_behavioral,
                                                                               _archs)
        else:
            raise ValueError("Problem type not implemented")

        features = []
        for df in _features:
            features.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics})
            print('--> FEATURE:', df)


        advices = []
        is_expert = user_information.is_domain_expert
        for feature in features[0:3]:
            advices.append(
                feature_expression_to_string(feature['name'], is_critique=not is_expert, context=context, user_info=user_information)
            )

        result = []
        for advice in advices:
            result.append({
                                "type": "Analyzer",
                                "advice": advice
                            })

        # -------
        print('--> EXTRACTED RESULTS')
        for f in result:
            print('--> ', f)

        return result

    except Exception as e:
        logger.exception('Exception in running data mining')
        print('--> EXCEPTION', e)
        dm_client.endConnection()
        return None











# ---------------------------------------------------------------------------------------------------
#         support_threshold = 0.002
#         confidence_threshold = 0.2
#         lift_threshold = 1
#
#         # features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
#         features = client.runAutomatedLocalSearch(behavioral, non_behavioral, designs, support_threshold,
#                                                   confidence_threshold, lift_threshold)
#
#         # End the connection before return statement
#         client.endConnection()
#
#         result = []
#         max_features = 3
#         if len(features) > 3:
#             pass
#         else:
#             max_features = len(features)
#
#         for i in range(max_features):  # Generate answers for the first 3 features
#             advice = feature_expression_to_string(features[i]['name'], context)
#             result.append({
#                 "type": "Analyzer",
#                 "advice": advice
#             })
#         return result
#
#     except Exception:
#         logger.exception('Exception in running data mining')
#         client.endConnection()
#         return None