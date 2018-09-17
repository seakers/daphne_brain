import logging
from VASSAR_API.api import VASSARClient
from data_mining_API.api import DataMiningClient
from daphne_API.critic.critic import CRITIC
import daphne_API.problem_specific as problem_specific
import pandas
import pickle

import traceback
import math
import sys

import numpy as np
import sys, os
import scipy.io
import pandas as pd
import xlrd
# from Naked.toolshed.shell import execute_rb, muterun_rb, run_rb
# from beautifultable import BeautifulTable
import json
from daphne_API import GetScorecardObjects
from daphne_API.MatEngine_object import eng1



logger = logging.getLogger('VASSAR')


def data_mining_run(designs, behavioral, non_behavioral, context):
    
    client = DataMiningClient()
    try:
        # Start connection with data_mining
        client.startConnection()
        
        support_threshold = 0.002
        confidence_threshold = 0.2
        lift_threshold = 1
        
        # features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
        features = client.runAutomatedLocalSearch(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
        
        # End the connection before return statement
        client.endConnection()
        
        result = []
        max_features = 3
        if len(features) > 3:
            pass
        else:
            max_features = len(features)

        for i in range(max_features): # Generate answers for the first 3 features
            advice = feature_expression_to_string(features[i]['name'], context)
            result.append({
                "type": "Analyzer",
                "advice": advice
            })
        return result
    
    except Exception:
        logger.exception('Exception in running data mining')
        client.endConnection()
        return None


def VASSAR_get_architecture_scores(design_id, designs, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id)
        list = client.client.getArchitectureScoreExplanation(designs[num_design_id]['inputs'])

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in loading architecture score information')
        client.endConnection()
        return None


def VASSAR_get_panel_scores(design_id, designs, panel, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id)
        stakeholders_to_excel = {
            "atmospheric": "ATM",
            "oceanic": "OCE",
            "terrestrial": "TER",
            "weather": "WEA",
            "climate": "CLI",
            "land and ecosystems": "ECO",
            "water": "WAT",
            "human health": "HEA"
        }

        panel_code = stakeholders_to_excel[panel]
        list = client.client.getPanelScoreExplanation(designs[num_design_id]['inputs'], panel_code)

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in loading panel score information')
        client.endConnection()
        return None


def VASSAR_get_objective_scores(design_id, designs, objective, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id)
        objective_list = client.client.getObjectiveScoreExplanation(designs[num_design_id]['inputs'], objective)

        # End the connection before return statement
        client.endConnection()
        return objective_list

    except Exception:
        logger.exception('Exception in loading objective score information')
        client.endConnection()
        return None


def VASSAR_get_instruments_for_objective(objective, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.startConnection()
        list = client.client.getInstrumentsForObjective(objective)

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in loading related instruments to an objective')
        client.endConnection()
        return None


def VASSAR_get_instruments_for_stakeholder(stakeholder, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)

    try:
        # Start connection with VASSAR
        client.startConnection()
        stakeholders_to_excel = {
            "atmospheric": "ATM",
            "oceanic": "OCE",
            "terrestrial": "TER",
            "weather": "WEA",
            "climate": "CLI",
            "land and ecosystems": "ECO",
            "water": "WAT",
            "human health": "HEA"
        }
        panel_code = stakeholders_to_excel[stakeholder]
        list = client.client.getInstrumentsForPanel(panel_code)

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in loading related instruments to a panel')
        client.endConnection()
        return None



def VASSAR_get_instrument_parameter(vassar_instrument, instrument_parameter, context):
    context["vassar_instrument"] = vassar_instrument
    context["instrument_parameter"] = instrument_parameter
    capabilities_sheet = problem_specific.get_capabilities_sheet(context["problem"])
    capability_found = False
    capability_value = None
    for row in capabilities_sheet.itertuples(name='Instrument'):
        if row[1].split()[1] == vassar_instrument:
            for i in range(2, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_found = True
                    capability_value = row[i].split()[1]

    if capability_found:
        return 'The ' + instrument_parameter + ' for ' + vassar_instrument + ' is ' + capability_value
    else:
        instrument_sheet = problem_specific.get_instrument_sheet(context["problem"], vassar_instrument)

        for i in range(2, len(instrument_sheet.columns)):
            if instrument_sheet[i][0].split()[0] == instrument_parameter:
                capability_found = True
        if capability_found:
            return 'I have found different values for this parameter depending on the measurement. ' \
                   'Please tell me for which measurement you want this parameter: ' \
                   + ', '.join([measurement[11:-1] for measurement in instrument_sheet[1]])
        else:
            return 'I have not found any information for this measurement.'


def VASSAR_get_instrument_parameter_followup(vassar_instrument, instrument_parameter, instrument_measurement, context):
    instrument_sheet = problem_specific.get_instrument_sheet(context["problem"], vassar_instrument)

    capability_value = None
    for row in instrument_sheet.itertuples(index=True, name='Measurement'):
        if row[2][11:-1] == instrument_measurement:
            for i in range(3, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_value = row[i].split()[1]

    return 'The ' + instrument_parameter + ' for instrument ' + vassar_instrument + ' and measurement ' + instrument_measurement + ' is ' + capability_value


def VASSAR_get_measurement_requirement(vassar_measurement, instrument_parameter, context):
    context["vassar_measurement"] = vassar_measurement
    context["instrument_parameter"] = instrument_parameter
    requirements_sheet = problem_specific.get_requirements_sheet(context["problem"])
    requirement_found = False
    requirements = []
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement_found = True
            requirements.append({"stakeholder": row[1], "type": row[4], "thresholds": row[5]})

    if requirement_found:
        if len(requirements) > 1:
            stakeholders_to_human = {
                "ATM": "Atmospheric",
                "OCE": "Oceanic",
                "TER": "Terrestrial",
                "WEA": "weather",
                "CLI": "climate",
                "ECO": "land and ecosystems",
                "WAT": "water",
                "HEA": "human health"
            }
            return 'I have found different values for this requirement depending on the stakeholder. ' \
                   'Please tell me for which stakeholder you want this requirement: ' \
                   + ', '.join([stakeholders_to_human[requirement["stakeholder"][0:3]] for requirement in requirements])
        else:
            threshold = requirements[0]["thresholds"][1:-1].split(',')[-1]
            target_value = requirements[0]["thresholds"][1:-1].split(',')[0]
            return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' (subojective ' + \
                   requirements[0]["stakeholder"] + ') is ' + threshold + ' and its target value is ' + \
                   target_value + '.'
    else:
        return 'I have not found any information for this requirement.'


def VASSAR_get_measurement_requirement_followup(vassar_measurement, instrument_parameter, stakeholder, context):
    requirements_sheet = problem_specific.get_requirements_sheet(context["problem"])
    stakeholders_to_excel = {
        "atmospheric": "ATM",
        "oceanic": "OCE",
        "terrestrial": "TER",
        "weather": "WEA",
        "climate": "CLI",
        "land and ecosystems": "ECO",
        "water": "WAT",
        "human health": "HEA"
    }
    requirement = None
    for row in requirements_sheet.itertuples(name='Requirement'):
        if row[1][0:3] == stakeholders_to_excel[stakeholder] and row[2][1:-1] == vassar_measurement and row[3] == instrument_parameter:
            requirement = {"stakeholder": row[1], "type": row[4], "thresholds": row[5]}

    threshold = requirement["thresholds"][1:-1].split(',')[-1]
    target_value = requirement["thresholds"][1:-1].split(',')[0]
    return 'The threshold for ' + instrument_parameter + ' for ' + vassar_measurement + ' for panel ' + requirement["stakeholder"] + ' is ' \
           + threshold + ' and its target value is ' + target_value + '.'


def Critic_general_call(design_id, designs, context):
    port = context['vassar_port'] if 'vassar_port' in context else 9090
    client = VASSARClient(port)
    critic = CRITIC(context["problem"])

    try:
        this_design = None
        num_design_id = int(design_id)
                
        for design in designs:
            if num_design_id == design['id']:
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
        
        # Criticize architecture (based on rules)
        problem = context['problem']
        result1 = None
        if problem in assignation_problems:
            result1 = client.client.getCritiqueBinaryInputArch(problem, this_design['inputs'])
        elif problem in partition_problems:
            result1 = client.client.getCritiqueDiscreteInputArch(problem, this_design['inputs'])

        result = []
        for advice in result1:
            result.append({
                "type": "Expert",
                "advice": advice
            })

        orbit_dataset = problem_specific.get_orbit_dataset(context["problem"])
        instrument_dataset = problem_specific.get_instrument_dataset(context["problem"])
            
        # Criticize architecture (based on explorer)
        def getAdvicesFromBitStringDiff(diff):
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
                    
                orbitIndex = i // ninstr # Floor division
                instrIndex = i % ninstr # Get the remainder                
                advice.append("instrument {}".format(instrument_dataset[instrIndex]['name']))

                if diff[i] == 1:
                    advice.append("to")
                elif diff[i] == -1:
                    advice.append("from")

                advice.append("orbit {}".format(orbit_dataset[orbitIndex]['name']))
                    
                advice = " ".join(advice)
                out.append(advice)
            
            out = ", and ".join(out)
            out = out[0].upper() + out[1:]
            return out
                
        original_outputs = this_design['outputs']
        original_inputs = this_design['inputs']

        archs = None
        if problem in assignation_problems:
            archs = client.client.runLocalSearchBinaryInput(problem, this_design['inputs'])
        elif problem in partition_problems:
            archs = client.client.runLocalSearchDiscreteInput(problem, this_design['inputs'])
        advices = []
        for arch in archs:
            new_outputs = arch['outputs']
            
            new_design_inputs = arch['inputs']
            diff = [a-b for a,b in zip(new_design_inputs,original_inputs)]  
            advice = [getAdvicesFromBitStringDiff(diff)]
            
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
                
        client.endConnection()
        result2 = []
        for advice in advices:
            result2.append({
                "type": "Explorer",
                "advice": advice
            }) 
        result.extend(result2)
            
            
        # Criticize architecture (based on database)
        result3 = critic.criticize_arch(this_design['inputs'])
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
                
                utopiaPoint = [0.26,0]
                temp = []
                # Select the top N% archs based on the distance to the utopia point
                for design in designs:
                    outputs = design['outputs']
                    id = design['id']
                    dist =  math.sqrt((outputs[0] - utopiaPoint[0])**2 + (outputs[1] - utopiaPoint[1])**2)
                    temp.append((id,dist))
                
                # Sort the list based on the distance to the utopia point
                temp = sorted(temp, key=lambda x : x[1])
                for i in range(len(temp)):
                    if i <= len(temp)//10: # Label the top 10% architectures as behavioral
                        behavioral.append(temp[i][0])
                    else:
                        non_behavioral.append(temp[i][0])
                        
            # Extract feature
            #features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)   
            features = client.runAutomatedLocalSearch(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
            
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
                    advices.append("Based on the data mining result, I advise you to make the following change: " + feature_expression_to_string(exp, isCritique=True, context=context))
                
                for exp in satisfied:
                    if exp == "":
                        continue
                    advices.append("Based on the data mining result, these are the good features. Consider keeping them: " + feature_expression_to_string(exp, isCritique=False, context=context))
            
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


def Critic_specific_call(design_id, agent, designs, context):
    critic = CRITIC(context["problem"])
    client = VASSARClient()
    try:
        result = []
        result_arr = []
        num_design_id = int(design_id[1:])
        if agent == 'expert':
            # Start connection with VASSAR
            client.startConnection()
            # Criticize architecture (based on rules)
            result_arr = client.client.getCritique(designs[num_design_id]['inputs'])
            client.endConnection()
        elif agent == 'historian':
            # Criticize architecture (based on database)
            result_arr = critic.historian_critic(designs[num_design_id]['inputs'])
        elif agent == 'analyst':
            # Criticize architecture (based on database)
            result_arr = critic.analyst_critic(designs[num_design_id]['inputs'])
        elif agent == 'explorer':
            # Criticize architecture (based on database)
            result_arr = critic.explorer_critic(designs[num_design_id]['inputs'])
        # Send response
        for res in result_arr:
            result.append({'advice': res})
        return result

    except Exception:
        logger.exception('Exception in using a single agent to criticize the architecture')
        client.endConnection()
        return None
    

def base_feature_expression_to_string(feature_expression, isCritique = False, context=None):
    
    try:
        e = feature_expression[1:-1]
        out = None

        feature_type = e.split("[")[0]
        arguments = e.split("[")[1][:-1]

        arg_split = arguments.split(";")

        orbit_indices = arg_split[0]
        instrument_indices = arg_split[1]
        numbers = arg_split[2]

        orbit_dataset = problem_specific.get_orbit_dataset(context["problem"])
        instrument_dataset = problem_specific.get_instrument_dataset(context["problem"])

        orbit_names = []
        if orbit_indices:
            orbit_names = [orbit_dataset[int(i)]['name'] for i in orbit_indices.split(",")]
        instrument_names = []
        if instrument_indices:
            instrument_names = [instrument_dataset[int(i)]['name'] for i in instrument_indices.split(",")]
        if numbers:
            numbers = [int(n) for n in numbers.split(",")]  
        
        if feature_type == "present":
            if isCritique:
                out = "add {}".format(instrument_names[0])
            else:
                out = "{} is used".format(instrument_names[0])
        elif feature_type == "absent":
            if isCritique:
                out = "remove {}".format(instrument_names[0])
            else:            
                out = "{} is not used in any orbit".format(instrument_names[0])
        elif feature_type == "inOrbit":
            if isCritique:
                out = ["assign instruments", ", ".join(instrument_names), "to orbit", orbit_names[0]]
            else:               
                out = ["instruments", ", ".join(instrument_names), "are assigned to orbit", orbit_names[0]]
            out = " ".join(out)
            
        elif feature_type == "notInOrbit":
            if isCritique:
                out = ["remove instruments", ", ".join(instrument_names),"in orbit",orbit_names[0]]
            else:               
                out = ["instruments", ", ".join(instrument_names),"are not assigned to orbit",orbit_names[0]]
            out = " ".join(out)
        elif feature_type == "together":
            if isCritique:
                out = "assign instruments {} to the same orbit".format(", ".join(instrument_names))
            else:    
                out = "instruments {} are assigned to the same orbit".format(", ".join(instrument_names))
        elif feature_type == "separate":
            if isCritique:
                out = "do not assign instruments {} to the same orbit".format(", ".join(instrument_names))
            else:    
                out = "instruments {} are never assigned to the same orbit".format(", ".join(instrument_names))
        elif feature_type == "emptyOrbit":
            if isCritique:
                out = "no spacecraft should fly in orbit {}".format(orbit_names[0])
            else:              
                out = "no spacecraft flies in orbit {}".format(orbit_names[0])
        else:
            raise ValueError('Unrecognized feature name: {}'.format(feature_type))
        return out
    
    except Exception as e:
        msg = "Error in parsing feature expression: {}".format(feature_expression) 
        print(msg)
        traceback.print_exc(file=sys.stdout)
        logger.error(msg)  
        
    
def feature_expression_to_string(feature_expression, isCritique = False, context = None):
    out = []
    # TODO: Generalize the feature expression parsing. 
    # Currently assumes that the feature only contains conjunctions but no disjunction
    if "&&" in feature_expression:
        individual_features = feature_expression.split("&&")
        for feat in individual_features:
            if feat == "":
                continue
            out.append(base_feature_expression_to_string(feat, isCritique, context))
    elif "||" in feature_expression:
        pass
    else:
        if not feature_expression == "":
            out.append(base_feature_expression_to_string(feature_expression, isCritique, context))
    
    out = " AND ".join(out)
    out = out[0].upper() + out[1:]
    
    return out


def get_feature_satisfied(expression, design, context):
    
    out = []
    
    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp, design, context))
        return out
    
    else:
        # TODO: Generalize the feature expression parsing. 
        # Currently assumes that the feature only contains conjunctions but no disjunction        
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]
            
        for feat in individual_features:  
            satisfied = apply_base_filter(feat, design, context)
            if satisfied:
                out.append(feat)        
        return "&&".join(out)


def get_feature_unsatisfied(expression, design, context):
    
    out = []
    
    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp, design, context))
        return out
    
    else:
        # TODO: Generalize the feature expression parsing. 
        # Currently assumes that the feature only contains conjunctions but no disjunction        
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]
            
        for feat in individual_features:  
            satisfied = apply_base_filter(feat, design, context)
            if not satisfied:
                out.append(feat)
        return "&&".join(out)
    
        
def apply_base_filter(filter_expression, design, context):

    expression = filter_expression
    
    # Preset filter: {presetName[orbits;instruments;numbers]} 
    if expression[0] == "{" and expression[-1] == "}":
        expression = expression[1:-1]

    orbit_dataset = problem_specific.get_orbit_dataset(context["problem"])
    instrument_dataset = problem_specific.get_instrument_dataset(context["problem"])
    norb = len(orbit_dataset)
    ninstr = len(instrument_dataset)
    featureType = expression.split("[")[0]
    arguments = expression.split("[")[1]
    arguments = arguments[:-1]
    
    inputs = design['inputs']

    argSplit = arguments.split(";")
    orbit = argSplit[0]
    instr = argSplit[1]
    numb = argSplit[2]
    
    try:
        out = None
        if featureType == "present":
            if len(instr) == 0:
                return False
            out = False
            instr = int(instr)
            for i in range(norb):
                if inputs[ninstr*i + instr]:
                    out=True
                    break

        elif featureType == "absent":
            if len(instr) == 0:
                return False
            out = True
            instr = int(instr)
            for i in range(norb):
                if inputs[ninstr*i + instr]:
                    out=False
                    break     
                    
        elif featureType == "inOrbit":
            orbit = int(orbit)
            
            if "," in instr:
                # Multiple instruments
                out = True
                instruments = instr.split(",")
                for instrument in instruments:
                    temp = int(instrument)
                    if inputs[orbit*ninstr + temp] is False:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = False
                if inputs[orbit*ninstr + instrument]:
                    out = True

        elif featureType == "notInOrbit":
            orbit = int(orbit)
            
            if "," in instr:
                # Multiple instruments
                out = True
                instruments = instr.split(",")
                for instrument in instruments:
                    temp = int(instrument)
                    if inputs[orbit*ninstr + temp] is True:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = True
                if inputs[orbit*ninstr + instrument]:
                    out = False            

        elif featureType == "together":
            out = False
            instruments = instr.split(",")
            for i in range(norb):
                found = True
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i*ninstr + temp] is False:
                        found=False
                
                if found:
                    out = True
                    break
                    
        elif featureType == "separate":
            out = True
            instruments = instr.split(",")
            for i in range(norb):
                found = False
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i*ninstr+temp] is True:
                        if found:
                            out = False
                            break
                        else:
                            found = True
                if out is False:
                    break
            
        elif featureType == "emptyOrbit":
            out = True
            orbit = int(orbit)
            
            for i in range(ninstr):
                if inputs[orbit*ninstr + i]:
                    out = False
                    break
            
        elif featureType == "numOrbits":
            count = 0
            out = False
            numb = int(numb)
            
            for i in range(norb):
                for j in range(ninstr):
                    if inputs[i*ninstr+j]:
                        count += 1
                        break
            
            if numb==count:
                out = True
                
        else:
            raise ValueError("Feature type not recognized: {}".format(featureType))
                    
    except Exception as e:
        raise ValueError("Exe in applying the base filter: " + str(e))
        
    return out

def EDL_load_mat_files(mission_name, mat_file, context):
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)
    context["current_mat_file"] = file_path
    context["current_mat_file_for_print"] = mat_file
    ''' ---------------For MATLAB Engine ------------------'''
    eng1.addpath(os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name), nargout = 0)

    mat_file_engine = eng1.load(mat_file)
    # TODO: ADD VARIABLE OF INTEREST TO ENGINE, NOT WHOLE MATFILE
    # eng1.workspace['dataset'] = mat_file_engine

    # eng1.disp('esto', nargout = 0)
    print('The current mat_file is:')
    print(mat_file)
    return 'file loaded'

def EDL_mat_file_list(mission_name,context):
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name)
    mat_files = os.listdir(file_path)
    result = []
    for mat_file in mat_files:
        result.append(
            {
                'command_result':mat_file
            }
        )
    return result


def EDL_compute_stat(mission_name,mat_file, param_name, context):
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

    for i in range(len(dict_NL)):
        key = param_name
        if key in dict_NL:
            param_name = dict_NL[param_name][0] # this returns the value of the key

        else:
            param_name = param_name
    file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)
    mat_dict = scipy.io.loadmat(file_path)
    '''Get list of keys in mat dict'''
    list_keys = list(mat_dict.keys())
    param_array = mat_dict[param_name]
    max = np.amax(param_array)
    min = np.amin(param_array)
    mean = np.mean(param_array)
    variance = np.var(param_array)
    std_dev = np.std(param_array)
    plus_three_sig = np.mean(param_array) + 3 * np.std(param_array)
    minus_three_sig = np.mean(param_array) - 3 * np.std(param_array)
    percentile013 = np.percentile(param_array, 0.13)
    percentile1 = np.percentile(param_array, 1)
    percentile10 = np.percentile(param_array, 10)
    percentile50 = np.percentile(param_array, 50)
    percentile99 = np.percentile(param_array, 99)
    percentile99_87 = np.percentile(param_array, 99.87)
    high99_87_minus_median = np.percentile(param_array, 99.87) - np.median(param_array)
    high99_87_minus_mean = np.percentile(param_array, 99.87) - np.median(param_array)
    median_minus_low_99_87 = np.median(param_array) - np.percentile(param_array, 0.13)
    mean_minus_low_99_87 = np.mean(param_array) - np.percentile(param_array, 0.13)

    name_of_stat = ["max", "min", "mean", "variance", "std", "3s", "mean", "-3s", "0.13%", "1.00%", "10.00%", "50.00%",
                    "90.00%",
                    "99.87", "high 99.89 - median", "high 99.87 - mean", "median - low 99.87",
                    "mean - low 99.87"]

    value_of_stat = [max, min, mean, variance, std_dev, plus_three_sig, mean, minus_three_sig, percentile013,
                     percentile1,
                     percentile10, percentile50, percentile99, percentile99_87, high99_87_minus_median,
                     high99_87_minus_mean,
                     median_minus_low_99_87, mean_minus_low_99_87]
    '''Now we want to create a  list as the one in the list sim data query'''
    # from daphne_API.MatEngine_object import eng1
    # eng1.eval('2+2')
    # eng1.load(eval(file_path))
    # eng1.eval('disp(esto)')

    stat = []
    for name, value in zip(name_of_stat, value_of_stat):
        stat.append(
            {
                'command_result': " = ".join([name, value.astype(str)])
            }
        )

    ''' Save parameter into csv file for plotting'''
    filename = str(param_name)+'.csv'
    np.savetxt(filename, param_array, delimiter=',', header=param_name, comments="")
    return stat

def load_scorecard(mission_name, mat_file, context):

    ''' Set Paths:
     1. mat file path;
     2. the scorecard template path''
     '''
    mat_file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', mission_name, mat_file)
    scorecard_template_path = '"/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardTemplate.xlsx"'


    ''' Connect to the local computer and generate scorecard'''
    os.system('echo $SHELL')
    os.system('setenv DYLD_FALLBACK_LIBRARY_PATH $LD_LIBRARY_PATH')
    # The scorecard ruby location is: /Volumes/Encrypted/Mars2020/mars2020/bin/scorecard.rb'''
    # The Scorecard template is: /Users/ssantini/Code/ExtractDataMatlab/ScoreCardTemplate.xlsx '''
    os.system('~/scorecard.rb --help')
    os.system('pushd "~/Users/ssantini/Desktop/Code Daphne/daphne_brain/"')
    os.system('pwd')
    os.environ['MATLAB_PATH']= "/Volumes/Encrypted/Mars2020/mars2020/MATLAB/"
    print(os.environ['MATLAB_PATH'])
    os.system(('~/scorecard.rb --yaml --template="/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardTemplate.xlsx"') + ' ' + mat_file_path)

    ''' Rename the Scorecard to the mat file'''
    scorecard_temp_path = mat_file.replace(".mat", "")
    scorecard_name = os.path.basename(scorecard_temp_path)+'.yml'
    scorecard_path = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', scorecard_name)
    if os.path.isfile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/scorecard.yml'):
        os.rename('/Users/ssantini/Desktop/Code Daphne/daphne_brain/scorecard.yml', scorecard_path)

    context["current_scorecard"] = scorecard_path
    return 'Score Card Loaded and Populated'


def get_scorecard_post_results(edl_scorecard,scorecard_post_param, context):
    path_scorecard = '/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx'
    scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

    [summary_outofspec, decision_meeting, edl_metric, trn, bud_metrics, entry, parachute_descent, powered_flight,
     edltimeline, comms, telecom, efc, summary, failure, detailed,
     list_of_metrics] = GetScorecardObjects.get_scorecard_objects_and_metrics(scorecard, path_scorecard)

    df = pd.read_excel(
        '/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get data from sheet
    list_of_metrics = list(df[0])

    '''Here we want to get the call values to convert to a dictionary using the NL language descriptions'''
    '''This dictionary is to get the POST results with the units'''
    keys_dict_summoutofspec = []
    keys_dict_summoutofspec_post = []
    keys_dict_summoutofspec_units = []
    keys_dict_summoutofspec_gless = []
    keys_dict_summoutofspec_flag = []
    keys_dict_summoutofspec_outofspec = []
    keys_dict_summoutofspec_description = []

    keys_dict_decision_meeting = []
    keys_dict_decision_meeting_post = []
    keys_dict_decision_meeting_units = []
    keys_dict_decision_meeting_gless = []
    keys_dict_decision_meeting_flag = []
    keys_dict_decision_meeting_outofspec = []
    keys_dict_decision_meeting_description = []

    keys_dict_edlmetrics = []
    keys_dict_edlmetrics_post = []
    keys_dict_edlmetrics_units = []
    keys_dict_edlmetrics_gless = []
    keys_dict_edlmetrics_flag = []
    keys_dict_edlmetrics_outofspec = []
    keys_dict_edlmetrics_description = []

    keys_dict_trn = []
    keys_dict_trn_post = []
    keys_dict_trn_units = []
    keys_dict_trn_gless = []
    keys_dict_trn_flag = []
    keys_dict_trn_outofspec = []
    keys_dict_trn_description = []

    keys_dict_bud = []
    keys_dict_bud_post = []
    keys_dict_bud_units = []
    keys_dict_bud_gless = []
    keys_dict_bud_flag = []
    keys_dict_bud_outofspec = []
    keys_dict_bud_description = []

    keys_dict_entry = []
    keys_dict_entry_post = []
    keys_dict_entry_units = []
    keys_dict_entry_gless = []
    keys_dict_entry_flag = []
    keys_dict_entry_outofspec = []
    keys_dict_entry_description = []

    keys_dict_parachute = []
    keys_dict_parachute_post = []
    keys_dict_parachute_units = []
    keys_dict_parachute_gless = []
    keys_dict_parachute_flag = []
    keys_dict_parachute_outofspec = []
    keys_dict_parachute_description = []

    keys_dict_poweredflight = []
    keys_dict_poweredflight_post = []
    keys_dict_poweredflight_units = []
    keys_dict_poweredflight_gless = []
    keys_dict_poweredflight_flag = []
    keys_dict_poweredflight_outofpec = []
    keys_dict_poweredflight_description = []

    keys_dict_timeline = []
    keys_dict_timeline_post = []
    keys_dict_timeline_units = []
    keys_dict_timeline_gless = []
    keys_dict_timeline_flag = []
    keys_dict_timeline_outofspec = []
    keys_dict_timeline_description = []

    keys_dict_edlcom = []
    keys_dict_edlcom_post = []
    keys_dict_edlcom_units = []
    keys_dict_edlcom_gless = []
    keys_dict_edlcom_flag = []
    keys_dict_edlcom_outofspec = []
    keys_dict_edlcom_description = []

    keys_dict_telecom = []
    keys_dict_telecom_post = []
    keys_dict_telecom_units = []
    keys_dict_telecom_gless = []
    keys_dict_telecom_flag = []
    keys_dict_telecom_outofspec = []
    keys_dict_telecom_description = []

    keys_dict_efc = []
    keys_dict_efc_post = []
    keys_dict_efc_units = []
    keys_dict_efc_gless = []
    keys_dict_efc_flag = []
    keys_dict_efc_outofspec = []
    keys_dict_efc_description = []

    keys_dict_summary = []
    keys_dict_summary_post = []
    keys_dict_summary_units = []
    keys_dict_summary_gless = []
    keys_dict_summary_flag = []
    keys_dict_summary_outofspec = []
    keys_dict_summary_description = []

    keys_dict_failures = []
    keys_dict_failures_post = []
    keys_dict_failures_units = []
    keys_dict_failures_gless = []
    keys_dict_failures_flag = []
    keys_dict_failures_outofspec = []
    keys_dict_failures_description = []

    keys_dict_detailed = []
    keys_dict_detailed_post = []
    keys_dict_detailed_units = []
    keys_dict_detailed_gless = []
    keys_dict_detailed_flag = []
    keys_dict_detailed_outofspec = []
    keys_dict_detailed_description = []

    for i in range(len(summary_outofspec.entries)):
        keys_dict_summoutofspec.append('summary_outofspec.entries[' + str(i) + '].name')
        keys_dict_summoutofspec_post.append('summary_outofspec.entries[' + str(i) + '].POST_results')
        keys_dict_summoutofspec_units.append('summary_outofspec.entries[' + str(i) + '].units')
        keys_dict_summoutofspec_flag.append('summary_outofspec.entries[' + str(i) + '].Flag')
        keys_dict_summoutofspec_gless.append('summary_outofspec.entries[' + str(i) + '].GreatOrLess')
        keys_dict_summoutofspec_outofspec.append('summary_outofspec.entries[' + str(i) + '].OutOfSpec')
        keys_dict_summoutofspec_description.append('summary_outofspec.entries[' + str(i) + '].Description')
    for i in range(len(decision_meeting.entries)):
        keys_dict_decision_meeting.append('decision_meeting.entries[' + str(i) + '].name')
        keys_dict_decision_meeting_post.append('decision_meeting.entries[' + str(i) + '].POST_results')
        keys_dict_decision_meeting_units.append('decision_meeting.entries[' + str(i) + '].units')
        keys_dict_decision_meeting_flag.append('decision_meeting.entries[' + str(i) + '].Flag')
        keys_dict_decision_meeting_gless.append('decision_meeting.entries[' + str(i) + '].GreatOrLess')
        keys_dict_decision_meeting_outofspec.append('decision_meeting.entries[' + str(i) + '].OutOfSpec')
        keys_dict_decision_meeting_description.append('decision_meeting.entries[' + str(i) + '].Description')
    for i in range(len(edl_metric.entries)):
        keys_dict_edlmetrics.append('edl_metric.entries[' + str(i) + '].name')
        keys_dict_edlmetrics_post.append('edl_metric.entries[' + str(i) + '].POST_results')
        keys_dict_edlmetrics_units.append('edl_metric.entries[' + str(i) + '].units')
        keys_dict_edlmetrics_flag.append('edl_metric.entries[' + str(i) + '].Flag')
        keys_dict_edlmetrics_gless.append('edl_metric.entries[' + str(i) + '].GreatOrLess')
        keys_dict_edlmetrics_outofspec.append('edl_metric.entries[' + str(i) + '].OutOfSpec')
        keys_dict_edlmetrics_description.append('edl_metric.entries[' + str(i) + '].Description')
    for i in range(len(trn.entries)):
        keys_dict_trn.append('trn.entries[' + str(i) + '].name')
        keys_dict_trn_post.append('trn.entries[' + str(i) + '].POST_results')
        keys_dict_trn_units.append('trn.entries[' + str(i) + '].units')
        keys_dict_trn_flag.append('trn.entries[' + str(i) + '].Flag')
        keys_dict_trn_gless.append('trn.entries[' + str(i) + '].GreatOrLess')
        keys_dict_trn_outofspec.append('trn.entries[' + str(i) + '].OutOfSpec')
        keys_dict_trn_description.append('trn.entries[' + str(i) + '].Description')
    for i in range(len(bud_metrics.entries)):
        keys_dict_bud.append('bud_metrics.entries[' + str(i) + '].name')
        keys_dict_bud_post.append('bud_metrics.entries[' + str(i) + '].POST_results')
        keys_dict_bud_units.append('bud_metrics.entries[' + str(i) + '].units')
        keys_dict_bud_flag.append('bud_metrics.entries[' + str(i) + '].Flag')
        keys_dict_bud_gless.append('bud_metrics.entries[' + str(i) + '].GreatOrLess')
        keys_dict_bud_outofspec.append('bud_metrics.entries[' + str(i) + '].OutOfSpec')
        keys_dict_bud_description.append('bud_metrics.entries[' + str(i) + '].Description')
    for i in range(len(entry.entries)):
        keys_dict_entry.append('entry.entries[' + str(i) + '].name')
        keys_dict_entry_post.append('entry.entries[' + str(i) + '].POST_results')
        keys_dict_entry_units.append('entry.entries[' + str(i) + '].units')
        keys_dict_entry_flag.append('entry.entries[' + str(i) + '].Flag')
        keys_dict_entry_gless.append('entry.entries[' + str(i) + '].GreatOrLess')
        keys_dict_entry_outofspec.append('entry.entries[' + str(i) + '].OutOfSpec')
        keys_dict_entry_description.append('entry.entries[' + str(i) + '].Description')
    for i in range(len(parachute_descent.entries)):
        keys_dict_parachute.append('parachute_descent.entries[' + str(i) + '].name')
        keys_dict_parachute_post.append('parachute_descent.entries[' + str(i) + '].POST_results')
        keys_dict_parachute_units.append('parachute_descent.entries[' + str(i) + '].units')
        keys_dict_parachute_flag.append('parachute_descent.entries[' + str(i) + '].Flag')
        keys_dict_parachute_gless.append('parachute_descent.entries[' + str(i) + '].GreatOrLess')
        keys_dict_parachute_outofspec.append('parachute_descent.entries[' + str(i) + '].OutOfSpec')
        keys_dict_parachute_description.append('parachute_descent.entries[' + str(i) + '].Description')
    for i in range(len(powered_flight.entries)):
        keys_dict_poweredflight.append('powered_flight.entries[' + str(i) + '].name')
        keys_dict_poweredflight_post.append('powered_flight.entries[' + str(i) + '].POST_results')
        keys_dict_poweredflight_units.append('powered_flight.entries[' + str(i) + '].units')
        keys_dict_poweredflight_flag.append('powered_flight.entries[' + str(i) + '].Flag')
        keys_dict_poweredflight_gless.append('powered_flight.entries[' + str(i) + '].GreatOrLess')
        keys_dict_poweredflight_outofpec.append('powered_flight.entries[' + str(i) + '].OutOfSpec')
        keys_dict_poweredflight_description.append('powered_flight.entries[' + str(i) + '].Description')
    for i in range(len(edltimeline.entries)):
        keys_dict_timeline.append('edltimeline.entries[' + str(i) + '].name')
        keys_dict_timeline_post.append('edltimeline.entries[' + str(i) + '].POST_results')
        keys_dict_timeline_units.append('edltimeline.entries[' + str(i) + '].units')
        keys_dict_timeline_flag.append('edltimeline.entries[' + str(i) + '].Flag')
        keys_dict_timeline_gless.append('edltimeline.entries[' + str(i) + '].GreatOrLess')
        keys_dict_timeline_outofspec.append('edltimeline.entries[' + str(i) + '].OutOfSpec')
        keys_dict_timeline_description.append('edltimeline.entries[' + str(i) + '].Description')
    for i in range(len(comms.entries)):
        keys_dict_edlcom.append('comms.entries[' + str(i) + '].name')
        keys_dict_edlcom_post.append('comms.entries[' + str(i) + '].POST_results')
        keys_dict_edlcom_units.append('comms.entries[' + str(i) + '].units')
        keys_dict_edlcom_flag.append('comms.entries[' + str(i) + '].Flag')
        keys_dict_edlcom_gless.append('comms.entries[' + str(i) + '].GreatOrLess')
        keys_dict_edlcom_outofspec.append('comms.entries[' + str(i) + '].OutOfSpec')
        keys_dict_edlcom_description.append('comms.entries[' + str(i) + '].Description')
    for i in range(len(telecom.entries)):
        keys_dict_telecom.append('telecom.entries[' + str(i) + '].name')
        keys_dict_telecom_post.append('telecom.entries[' + str(i) + '].POST_results')
        keys_dict_telecom_units.append('telecom.entries[' + str(i) + '].units')
        keys_dict_telecom_flag.append('telecom.entries[' + str(i) + '].Flag')
        keys_dict_telecom_gless.append('telecom.entries[' + str(i) + '].GreatOrLess')
        keys_dict_telecom_outofspec.append('telecom.entries[' + str(i) + '].OutOfSpec')
        keys_dict_telecom_description.append('telecom.entries[' + str(i) + '].Description')
    for i in range(len(efc.entries)):
        keys_dict_efc.append('efc.entries[' + str(i) + '].name')
        keys_dict_efc_post.append('efc.entries[' + str(i) + '].POST_results')
        keys_dict_efc_units.append('efc.entries[' + str(i) + '].units')
        keys_dict_efc_flag.append('efc.entries[' + str(i) + '].Flag')
        keys_dict_efc_gless.append('efc.entries[' + str(i) + '].GreatOrLess')
        keys_dict_efc_outofspec.append('efc.entries[' + str(i) + '].OutOfSpec')
        keys_dict_efc_description.append('efc.entries[' + str(i) + '].Description')
    for i in range(len(summary.entries)):
        keys_dict_summary.append('summary.entries[' + str(i) + '].name')
        keys_dict_summary_post.append('summary.entries[' + str(i) + '].POST_results')
        keys_dict_summary_units.append('summary.entries[' + str(i) + '].units')
        keys_dict_summary_flag.append('summary.entries[' + str(i) + '].Flag')
        keys_dict_summary_gless.append('summary.entries[' + str(i) + '].GreatOrLess')
        keys_dict_summary_outofspec.append('summary.entries[' + str(i) + '].OutOfSpec')
        keys_dict_summary_description.append('summary.entries[' + str(i) + '].Description')
    for i in range(len(failure.entries)):
        keys_dict_failures.append('failure.entries[' + str(i) + '].name')
        keys_dict_failures_post.append('failure.entries[' + str(i) + '].POST_results')
        keys_dict_failures_units.append('failure.entries[' + str(i) + '].units')
        keys_dict_failures_flag.append('failure.entries[' + str(i) + '].Flag')
        keys_dict_failures_gless.append('failure.entries[' + str(i) + '].GreatOrLess')
        keys_dict_failures_outofspec.append('failure.entries[' + str(i) + '].OutOfSpec')
        keys_dict_failures_description.append('failure.entries[' + str(i) + '].Description')
    for i in range(len(detailed.entries)):
        keys_dict_detailed.append('detailed.entries[' + str(i) + '].name')
        keys_dict_detailed_post.append('detailed.entries[' + str(i) + '].POST_results')
        keys_dict_detailed_units.append('detailed.entries[' + str(i) + '].units')
        keys_dict_detailed_flag.append('detailed.entries[' + str(i) + '].Flag')
        keys_dict_detailed_gless.append('detailed.entries[' + str(i) + '].GreatOrLess')
        keys_dict_detailed_outofspec.append('detailed.entries[' + str(i) + '].OutOfSpec')
        keys_dict_detailed_description.append('detailed.entries[' + str(i) + '].Description')

    # esoes = eval(keys_dict_entry[:])
    '''Create single list of post results and units'''

    post_dict_value = [keys_dict_summoutofspec_post + keys_dict_decision_meeting_post + keys_dict_edlmetrics_post +
                       keys_dict_trn_post + keys_dict_bud_post + keys_dict_entry_post + keys_dict_parachute_post +
                       keys_dict_poweredflight_post + keys_dict_timeline_post + keys_dict_edlcom_post +
                       keys_dict_telecom_post + keys_dict_efc_post + keys_dict_summary_post + keys_dict_failures_post +
                       keys_dict_detailed_post]
    post_dict_value = [item for items in post_dict_value for item in items]

    units_dict_value = [keys_dict_summoutofspec_units + keys_dict_decision_meeting_units + keys_dict_edlmetrics_units +
                        keys_dict_trn_units + keys_dict_bud_units + keys_dict_entry_units + keys_dict_parachute_units +
                        keys_dict_poweredflight_units + keys_dict_timeline_units + keys_dict_edlcom_units +
                        keys_dict_telecom_units + keys_dict_efc_units + keys_dict_summary_units + keys_dict_failures_units +
                        keys_dict_detailed_units]
    units_dict_value = [item for items in units_dict_value for item in items]

    flag_dict_value = [keys_dict_summoutofspec_flag + keys_dict_decision_meeting_flag + keys_dict_edlmetrics_flag +
                       keys_dict_trn_flag + keys_dict_bud_flag + keys_dict_entry_flag + keys_dict_parachute_flag +
                       keys_dict_poweredflight_flag + keys_dict_timeline_flag + keys_dict_edlcom_flag +
                       keys_dict_telecom_flag + keys_dict_efc_flag + keys_dict_summary_flag + keys_dict_failures_flag +
                       keys_dict_detailed_flag]
    flag_dict_value = [(item) for (items) in flag_dict_value for (item) in (items)]

    gless_dict_value = [keys_dict_summoutofspec_gless + keys_dict_decision_meeting_gless + keys_dict_edlmetrics_gless +
                        keys_dict_trn_gless + keys_dict_bud_gless + keys_dict_entry_gless + keys_dict_parachute_gless +
                        keys_dict_poweredflight_gless + keys_dict_timeline_gless + keys_dict_edlcom_gless +
                        keys_dict_telecom_gless + keys_dict_efc_gless + keys_dict_summary_gless + keys_dict_failures_gless +
                        keys_dict_detailed_gless]
    gless_dict_value = [item for items in gless_dict_value for item in items]

    outofspec_dict_value = [
        keys_dict_summoutofspec_outofspec + keys_dict_decision_meeting_outofspec + keys_dict_edlmetrics_outofspec +
        keys_dict_trn_outofspec + keys_dict_bud_outofspec + keys_dict_entry_outofspec
        + keys_dict_parachute_outofspec +
        keys_dict_poweredflight_outofpec + keys_dict_timeline_outofspec + keys_dict_edlcom_outofspec +
        keys_dict_telecom_outofspec + keys_dict_efc_outofspec + keys_dict_summary_outofspec + keys_dict_failures_outofspec +
        keys_dict_detailed_outofspec]
    outofspec_dict_value = [item for items in outofspec_dict_value for item in items]


    description_dict_value = [keys_dict_summoutofspec_description + keys_dict_decision_meeting_description +
                              keys_dict_edlmetrics_description + keys_dict_trn_description + keys_dict_bud_description +
                              keys_dict_entry_description + keys_dict_parachute_description +
                              keys_dict_poweredflight_description + keys_dict_timeline_gless + keys_dict_edlcom_description +
                              keys_dict_telecom_description + keys_dict_efc_description + keys_dict_summary_description +
                              keys_dict_failures_description + keys_dict_detailed_description]
    description_dict_value = [item for items in description_dict_value for item in items]

    '''================================================== Dictionary =================================================='''
    list_of_lists_all = [list_of_metrics, post_dict_value, units_dict_value, gless_dict_value, flag_dict_value,
                         outofspec_dict_value]

    for i in range(len(post_dict_value)):
        post_dict_value[i] = eval(post_dict_value[i])
        units_dict_value[i] = eval(units_dict_value[i])
        flag_dict_value[i] = eval(flag_dict_value[i])
        gless_dict_value[i] = eval(gless_dict_value[i])
        outofspec_dict_value[i] = eval(outofspec_dict_value[i])
        description_dict_value[i] = eval(description_dict_value[i])

    all_metrics_dict = {z[0]: (list((z[1:]))) for (z) in zip(*list_of_lists_all)}

    value =(str(all_metrics_dict[scorecard_post_param][0]))
    units = str(all_metrics_dict[scorecard_post_param][1])
    scorecard_post_result_returned = str(value) + " " + str(units)

    '''Save the dictionary'''
    json.dump(all_metrics_dict, open("/Users/ssantini/Desktop/Code Daphne/daphne_brain/dict_for_flags_outofspec.txt",
              'w'))

    return scorecard_post_result_returned

def get_flag_summary(edl_scorecard, context, *flag_type):

    '''================================================== Get flagged values ===================================='''
    dict_NL = json.load(open("/Users/ssantini/Desktop/Code Daphne/daphne_brain/dict_for_flags_outofspec.txt"))
    all_metrics_dict = dict_NL

    df = pd.read_excel(
        '/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get renamed metrics
    list_of_metrics = list(df[0]) # made some modifications

    flagged_metrics = []
    flagged_value = []
    flagged_unit = []
    flagged_operator = []
    flagged_flagval = []
    flagged_note = []

    outofspec_metrics = []
    outofspec_value = []
    outofspec_unit = []
    outofspec_operator = []
    outofspec_outofspec = []
    outofspec_note = []

    for item in list_of_metrics:
        value = (str((all_metrics_dict[item][0])))
        unit = (str((all_metrics_dict[item][1])))
        operator = (str((all_metrics_dict[item][2])))
        flag_val = (str((all_metrics_dict[item][3])))
        outofspec_val = (str((all_metrics_dict[item][4])))
        if value != 'nan' and operator != 'nan' and flag_val != 'nan' and outofspec_val != 'nan':
            if eval(str(value) + str(operator) + str(flag_val)) == False \
                    and eval(str(value) + str(operator) + str(outofspec_val)) == True:
                flagged_metrics.append(item)
                flagged_value.append(value)
                flagged_unit.append(unit)
                flagged_operator.append(str(operator))
                flagged_flagval.append(str(flag_val))
                flagged_note.append(str('is not satisfied'))
            if eval(str(value) + str(operator) + str(flag_val)) == False \
                    and eval(str(value) + str(operator) + str(outofspec_val)) == False:
                outofspec_metrics.append(item)
                outofspec_value.append((value))
                outofspec_unit.append((unit))
                outofspec_operator.append(str(operator))
                outofspec_outofspec.append(str(flag_val))
                outofspec_note.append(str('is not satisfied'))
    if ('flagged_results' in flag_type):
        flagged_values = []
        for name, value, unit, operator, flagval, note in zip(flagged_metrics, flagged_value, flagged_unit, flagged_operator,
                                                        flagged_flagval, flagged_note):
            flagged_values.append(
                {
                    'command_result': "  ".join([name, value, operator, flagval, unit, note])
                }
            )
        return flagged_values
    if ('outofspec_results' in flag_type):
        out_of_spec_values = []
        for name, value, unit, operator, flagval, note in zip(outofspec_metrics, outofspec_value, outofspec_unit,
                                                              outofspec_operator, outofspec_outofspec, outofspec_note):
            out_of_spec_values.append(
                {
                    'command_result': "  ".join([name, value, operator, flagval, unit, note])
                }
            )
        return out_of_spec_values

def get_scorecard_post_results_edlmetrics(edl_scorecard,scorecard_post_param, context):
    path_scorecard = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', edl_scorecard)
    scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

    '''Here we get all lists from all metrics and fields'''
    NAMES_EDLSHEET = []
    TYPES_EDLSHEET = []
    UNITS_EDLSHEET = []
    GREATORLESSS_EDL_SHEET = []
    POST_RESULTS_EDLSHEET = []
    FLAG_EDLSHEET = []
    OUTOFSPEC_EDLSHEET = []
    DESCRIPT_EDLSHEET = []
    CALC_EDLSHEET = []

    '''Remove all of the fields we dont want'''
    sheets = scorecard.sheet_names
    for sheet in sheets:
        df = pd.read_excel('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx', sheet_name=sheet)  # get data from sheet
        column_names = list(df.columns)
        metric_col = column_names[1]  # metric sheet will be the reference for deleting empty rows or label rows
        length_col = len(df[metric_col])  # original number of rows in the excel sheet
        if sheet == sheets[0]:
            for i in range(length_col):
                algo = df[metric_col][i]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric':
                    df.drop([i], inplace=True)
                    DF_EDLMETRICS = df

            NAMES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[1]]))
            TYPES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[2]]))
            UNITS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[3]]))
            POST_RESULTS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[4]]))
            GREATORLESSS_EDL_SHEET.append(list(DF_EDLMETRICS[column_names[5]]))
            FLAG_EDLSHEET.append(list(DF_EDLMETRICS[column_names[6]]))
            OUTOFSPEC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[7]]))
            CALC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[10]]))
            DESCRIPT_EDLSHEET.append(list(DF_EDLMETRICS[column_names[9]]))

    '''Create objects and classes'''

    class ScoreCardCategory(object):
        def __init__(self, name=0, entries=0):
            self.name = name  # these are the tab names (categories)
            self.entries = entries  # These are all the metrics in each

        def __call__(self, name, entries):
            print(name)
            print(entries)

    class ScoreCardMetrics(object):
        def __init__(self, name=0, type=0, units=0, POST_results=0, GreatOrLess=0, Flag=0, OutOfSpec=0, Enum=0,
                     Description=0, Calculation=0, CalculationCheckedBy=0, MetricCheckedBy=0, FlagOutOfSpecOwner=0):
            self.name = name
            self.type = type
            self.units = units
            self.POST_results = POST_results
            self.GreatOrLess = GreatOrLess
            self.Flag = Flag
            self.OutOfSpec = OutOfSpec
            self.Enum = Enum
            self.Description = Description
            self.Calculation = Calculation
            self.CalculationCheckedBy = CalculationCheckedBy
            self.MetricCheckedBy = MetricCheckedBy
            self.FlagOutOfSpecOwner = FlagOutOfSpecOwner

        def __call__(self, name, type, units, POST_results, GreatOrLess, Flag, OutOfSpec, Enum,
                     Description, Calculation, CalculationCheckedBy, MetricCheckedBy, FlagOutOfSpecOwner):
            print(name)
            print(type)
            print(units)
            print(POST_results)
            print(GreatOrLess)
            print(Flag)
            print(OutOfSpec)
            print(Enum)
            print(Description)
            print(Calculation)
            print(CalculationCheckedBy)
            print(MetricCheckedBy)
            print(FlagOutOfSpecOwner)

    METRIC_OBJECTS_GROUPED_EDLMETRIC = []
    METRIC_OBJECTS_EDLMETRIC = []
    for i in range(len(NAMES_EDLSHEET[0])):  # number of metrics in each sheet
        METRIC_OBJECTS_EDLMETRIC.append(ScoreCardMetrics(name=NAMES_EDLSHEET[0][i], type=TYPES_EDLSHEET[0][i],
                                                         units=UNITS_EDLSHEET[0][i],
                                                         POST_results=POST_RESULTS_EDLSHEET[0][i],
                                                         GreatOrLess=GREATORLESSS_EDL_SHEET[0][i],
                                                         Flag=FLAG_EDLSHEET[0][i],
                                                         OutOfSpec=OUTOFSPEC_EDLSHEET[0][i], Enum=0,
                                                         Description=DESCRIPT_EDLSHEET[0][i],
                                                         Calculation=CALC_EDLSHEET[0][i], CalculationCheckedBy=0,
                                                         MetricCheckedBy=0, FlagOutOfSpecOwner=0))
        METRIC_OBJECTS = list(METRIC_OBJECTS_EDLMETRIC)
    METRIC_OBJECTS_GROUPED_EDLMETRIC.append(METRIC_OBJECTS)

    edl_metric_objects = METRIC_OBJECTS_GROUPED_EDLMETRIC[0]
    edl_metric = ScoreCardCategory(scorecard.sheet_names[0], edl_metric_objects)

    '''Here we want to get the call values to convert to a dictionary using the NL language descriptions'''
    '''This dictionary is to get the POST results with the units'''
    value_edlmetric_name = []
    value_edlmetric_units = []
    value_edlmetric_post = []
    value_edlmetric_type = []
    value_edlmetric_greatorless = []
    value_edlmetric_flag = []
    value_edlmetric_description = []
    value_edlmetric_outofspec = []

    for i in range(len(edl_metric_objects)):
        value_edlmetric_type.append('edl_metric.entries[' + str(i) + '].type')
        value_edlmetric_units.append('edl_metric.entries[' + str(i) + '].units')
        value_edlmetric_post.append('edl_metric.entries[' + str(i) + '].POST_results')
        value_edlmetric_greatorless.append('edl_metric.entries[' + str(i) + '].GreatOrLess')
        value_edlmetric_flag.append('edl_metric.entries[' + str(i) + '].Flag')
        value_edlmetric_outofspec.append('edl_metric.entries[' + str(i) + '].OutofSpec')
        value_edlmetric_description.append('edl_metric.entries[' + str(i) + '].Description')

    '''=========================================Dictionary========================================================='''
    list_of_metrics_edlmetric = [item for items in NAMES_EDLSHEET for item in items]
    list_of_lists = [list_of_metrics_edlmetric, value_edlmetric_type, value_edlmetric_units, value_edlmetric_post,
                     value_edlmetric_greatorless, value_edlmetric_flag, value_edlmetric_outofspec,
                     value_edlmetric_description]
    dictionary_edlmetrics = {z[0]: list(z[1:]) for z in zip(*list_of_lists)}

    value = eval(dictionary_edlmetrics[scorecard_post_param][2])
    units = eval(dictionary_edlmetrics[scorecard_post_param][1])
    scorecard_post_result_returned_edlmetrics = str(value) + " " + units
    return scorecard_post_result_returned_edlmetrics

# def get_scorecard_sumamry_edlmetrics(edl_scorecard, context):
#     path_scorecard = os.path.join('/Users/ssantini/Desktop/Code Daphne/daphne_brain/', edl_scorecard)
#     scorecard = pd.ExcelFile('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx')

#     '''Here we get all lists from all metrics and fields'''
#     NAMES_EDLSHEET = []
#     TYPES_EDLSHEET = []
#     UNITS_EDLSHEET = []
#     GREATORLESSS_EDL_SHEET = []
#     POST_RESULTS_EDLSHEET = []
#     FLAG_EDLSHEET = []
#     OUTOFSPEC_EDLSHEET = []
#     DESCRIPT_EDLSHEET = []
#     CALC_EDLSHEET = []


#     '''Remove all of the fields we dont want'''
#     sheets = scorecard.sheet_names
#     for sheet in sheets:
#         df = pd.read_excel('/Users/ssantini/Desktop/Code Daphne/daphne_brain/ScoreCardResults.xlsx', sheet_name=sheet)  # get data from sheet
#         column_names = list(df.columns)
#         metric_col = column_names[1]  # metric sheet will be the reference for deleting empty rows or label rows
#         length_col = len(df[metric_col])  # original number of rows in the excel sheet
#         if sheet == sheets[0]:
#             for i in range(length_col):

#                 if type(df[metric_col][i]) == float:
#                     df.drop([i], inplace=True)
#                 elif (df[metric_col][i]) == 'Metric':
#                     df.drop([i], inplace=True)
#                     DF_EDLMETRICS = df

#             NAMES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[1]]))
#             TYPES_EDLSHEET.append(list(DF_EDLMETRICS[column_names[2]]))
#             UNITS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[3]]))
#             POST_RESULTS_EDLSHEET.append(list(DF_EDLMETRICS[column_names[4]]))
#             GREATORLESSS_EDL_SHEET.append(list(DF_EDLMETRICS[column_names[5]]))
#             FLAG_EDLSHEET.append(list(DF_EDLMETRICS[column_names[6]]))
#             OUTOFSPEC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[7]]))
#             CALC_EDLSHEET.append(list(DF_EDLMETRICS[column_names[10]]))
#             DESCRIPT_EDLSHEET.append(list(DF_EDLMETRICS[column_names[9]]))

#     '''Create objects and classes'''

#     class ScoreCardCategory(object):
#         def __init__(self, name=0, entries=0):
#             self.name = name  # these are the tab names (categories)
#             self.entries = entries  # These are all the metrics in each

#         def __call__(self, name, entries):
#             print(name)
#             print(entries)

#     class ScoreCardMetrics(object):
#         def __init__(self, name=0, type=0, units=0, POST_results=0, GreatOrLess=0, Flag=0, OutOfSpec=0, Enum=0,
#                      Description=0, Calculation=0, CalculationCheckedBy=0, MetricCheckedBy=0, FlagOutOfSpecOwner=0):
#             self.name = name
#             self.type = type
#             self.units = units
#             self.POST_results = POST_results
#             self.GreatOrLess = GreatOrLess
#             self.Flag = Flag
#             self.OutOfSpec = OutOfSpec
#             self.Enum = Enum
#             self.Description = Description
#             self.Calculation = Calculation
#             self.CalculationCheckedBy = CalculationCheckedBy
#             self.MetricCheckedBy = MetricCheckedBy
#             self.FlagOutOfSpecOwner = FlagOutOfSpecOwner

#         def __call__(self, name, type, units, POST_results, GreatOrLess, Flag, OutOfSpec, Enum,
#                      Description, Calculation, CalculationCheckedBy, MetricCheckedBy, FlagOutOfSpecOwner):
#             print(name)
#             print(type)
#             print(units)
#             print(POST_results)
#             print(GreatOrLess)
#             print(Flag)
#             print(OutOfSpec)
#             print(Enum)
#             print(Description)
#             print(Calculation)
#             print(CalculationCheckedBy)
#             print(MetricCheckedBy)
#             print(FlagOutOfSpecOwner)

#     METRIC_OBJECTS_GROUPED_EDLMETRIC = []
#     METRIC_OBJECTS_EDLMETRIC = []
#     for i in range(len(NAMES_EDLSHEET[0])):  # number of metrics in each sheet
#         METRIC_OBJECTS_EDLMETRIC.append(ScoreCardMetrics(name=NAMES_EDLSHEET[0][i], type=TYPES_EDLSHEET[0][i],
#                                                          units=UNITS_EDLSHEET[0][i],
#                                                          POST_results=POST_RESULTS_EDLSHEET[0][i],
#                                                          GreatOrLess=GREATORLESSS_EDL_SHEET[0][i],
#                                                          Flag=FLAG_EDLSHEET[0][i],
#                                                          OutOfSpec=OUTOFSPEC_EDLSHEET[0][i], Enum=0,
#                                                          Description=DESCRIPT_EDLSHEET[0][i],
#                                                          Calculation=CALC_EDLSHEET[0][i], CalculationCheckedBy=0,
#                                                          MetricCheckedBy=0, FlagOutOfSpecOwner=0))
#         METRIC_OBJECTS = list(METRIC_OBJECTS_EDLMETRIC)
#     METRIC_OBJECTS_GROUPED_EDLMETRIC.append(METRIC_OBJECTS)

#     edl_metric_objects = METRIC_OBJECTS_GROUPED_EDLMETRIC[0]
#     edl_metric = ScoreCardCategory(scorecard.sheet_names[0], edl_metric_objects)
#     '''===================================Create Summary ==========================================================='''
#     name = []
#     types = []
#     units = []
#     post = []
#     GorLess = []
#     flag = []
#     outofspec = []
#     description = []
#     calculation = []

#     for i in range(len(edl_metric_objects)):
#         name.append(str((edl_metric.entries[i].name)))
#         types.append(str((edl_metric.entries[i].type)))
#         units.append(str((edl_metric.entries[i].units)))
#         post.append(str((edl_metric.entries[i].POST_results)))
#         flag.append(str((edl_metric.entries[i].Flag)))
#         outofspec.append(str((edl_metric.entries[i].OutOfSpec)))
#         GorLess.append(str((edl_metric.entries[i].GreatOrLess)))
#         description.append(str((edl_metric.entries[i].Description)))
#         calculation.append(str((edl_metric.entries[i].Calculation)))

#     table = BeautifulTable()
#     table.column_headers = ['metric', 'type', 'POST2 Result', 'units', 'direction', 'flag value', 'out of spec value',
#                             'calculation','description']

#     for row in zip((name), (types), (post), (units), (GorLess), (flag), (outofspec),
#                    (calculation), (description)):
#         table.append_row(row)

#     table.column_widths = [30, 10, 15, 10, 8, 10, 15, 20, 10]
#     print(table.get_string(recalculate_width=False))

#     table_summary_edlmetrics = table
#     return table_summary_edlmetrics
