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
from Naked.toolshed.shell import execute_rb, muterun_rb, run_rb
from beautifultable import BeautifulTable
import json
from daphne_API import GetScorecardObjects
from daphne_API.MatEngine_object import eng1
from daphne_API import ScorecardDataFrameFuncs
import yaml
from numpy import nan
import re



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
    if mission_name == 'None':
        file_path = mat_file
    else:
        file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files/', mission_name, mat_file)

    edl_mat_load = eng1.load(file_path, param_name, nargout=0) # loads in engine
    param_array = np.array(eng1.workspace[param_name])

    # mat_dict = scipy.io.loadmat(file_path)
    # '''Get list of keys in mat dict'''
    # list_keys = list(mat_dict.keys())
    # param_array = mat_dict[param_name]
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


    stat = []
    for name, value in zip(name_of_stat, value_of_stat):
        stat.append(
            {
                'command_result': " = ".join([name, value.astype(str)])
            }
        )


    val2 = eng1.workspace[param_name] # returns to python
    my_list = []
    for _ in range(val2.size[1]):
        my_list.append(val2._data[_ * val2.size[0]:_ * val2.size[0] + val2.size[0]].tolist())
    return stat, my_list[0]

def load_scorecard(mission_name, mat_file, context):
    if mission_name == 'None':
        file_to_search = os.path.basename(mat_file.replace(".mat", ".yml"))
    else:
        file_to_search = mat_file.replace(".mat", ".yml")
    '''Check if scorecard exists already'''
    if os.path.exists(os.path.join("/Users/ssantini/Desktop/Code_Daphne/daphne_brain/", file_to_search)) == True:
        i = 1
        scorecard_path = os.path.join('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/', file_to_search)

    else:
        ''' Set Paths:
         1. mat file path;
         2. the scorecard template path''
         '''
        if mission_name == 'None':
            mat_file_path = mat_file # this is actually a path
        else:
            mat_file_path = os.path.join('/Users/ssantini/Desktop/EDL_Simulation_Files', mission_name, mat_file)
        scorecard_template_path = '"/Users/ssantini/Desktop/Code_Daphne/daphne_brain/ScoreCardTemplate.xlsx"'

        ''' Connect to the local computer and generate scorecard'''
        os.system('echo $SHELL')
        os.system('setenv DYLD_FALLBACK_LIBRARY_PATH $LD_LIBRARY_PATH')
        # The scorecard ruby location is: /Volumes/Encrypted/Mars2020/mars2020/bin/scorecard.rb'''
        # The Scorecard template is: /Users/ssantini/Code/ExtractDataMatlab/ScoreCardTemplate.xlsx '''
        os.system('~/scorecard.rb --help')
        os.system('pushd "~/Users/ssantini/Desktop/Code_Daphne/daphne_brain/"')
        os.system('pwd')
        os.environ['MATLAB_PATH']= "/Volumes/Encrypted/Mars2020/mars2020/MATLAB/"
        print(os.environ['MATLAB_PATH'])
        os.system(('~/scorecard.rb --yaml --template="/Users/ssantini/Desktop/Code_Daphne/daphne_brain/ScoreCardTemplate.xlsx"') + ' ' + mat_file_path)

        ''' Rename the Scorecard to the mat file'''
        scorecard_temp_path = mat_file.replace(".mat", "")
        scorecard_name = os.path.basename(scorecard_temp_path)+'.yml'
        scorecard_path = os.path.join('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/', scorecard_name)
        if os.path.isfile('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.yml'):
            os.rename('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.yml', scorecard_path)

    context["current_scorecard_file"] = os.path.basename(scorecard_path)
    context["current_scorecard"] = scorecard_path
    return 'Score Card Loaded and Populated'


def get_scorecard_post_results(edl_scorecard,scorecard_post_param, context):
    with open(os.path.basename(edl_scorecard), encoding='utf-8') as scorecard_file:
        scorecard_dict = yaml.load(scorecard_file)
    scorecard_df = ScorecardDataFrameFuncs.generate_scorecard_dataframe(scorecard_dict)

    '''Search in dictionary what is contained '''
    possible_metrics = scorecard_df.metric_name.str.contains(str(scorecard_post_param), case = False, na = False)
    indexes_in_df = possible_metrics[possible_metrics == True].index.tolist()
    post_results = scorecard_df.iloc[indexes_in_df]

    post_results_list = []
    for row in post_results.itertuples():
        post_results_list.append(
            {
                'command_result': " ".join([str(row.metric_name), str('='), str(row.post_results), str(row.units), "(",
                                            str(row.type), ")"])
            }
        )
    return post_results_list

def get_flag_summary(edl_scorecard,context, *flag_type):

    ''' 1. Convert to dataframe
    2. Add column with labels : flagged, out of spec, N/A or value is ok
    3. Get dataframe for flagged metrics and one data frame for out of spec'''

    scorecard_name = os.path.basename(edl_scorecard)
    with open(scorecard_name, encoding='utf-8') as scorecard_file:
        scorecard_dict = yaml.load(scorecard_file)

    scorecard_df = ScorecardDataFrameFuncs.generate_scorecard_dataframe(scorecard_dict)
    scorecard_df_labeled = ScorecardDataFrameFuncs.generate_scorecard_dataframe_labeled(scorecard_df)
    flagged_df = scorecard_df_labeled[scorecard_df_labeled.status == 'flagged']
    out_of_spec_df = scorecard_df_labeled[scorecard_df_labeled.status == 'out of spec']

    ''' Now we want to get what metrics are flagged and which are out of spec as a list'''
    if 'flagged_results' in flag_type:
        flagged_list = []
        for row in flagged_df.itertuples():
            flagged_list.append(
                {
                    'command_result':" ".join([str(row.metric_name), str(row.post_results), str(row.units), "(",
                                               str(row.type), ")",
                                               str(row.direction), str(row.flag), str(row.units), 'is not satisfied'])
                }
            )
        return flagged_list
    if 'outofspec_results' in flag_type:
        outofspec_list = []
        for row in out_of_spec_df.itertuples():
            outofspec_list.append(
                {
                    'command_result': " ".join([str(row.metric_name), str(row.post_results),  str(row.units), "(",
                                                str(row.type), ")",
                                                str(row.direction), str(row.flag), str(row.units),'is not satisfied'])
                }
            )
        return outofspec_list

# TODO: add function for calculating the metrics from a matfile (5007)
def calculate_scorecard_metric(mat_file, edl_scorecard_calculate, scorecard_post_param, context):

    '''Get from the template the details of the metric being calculated'''
    with open('/Users/ssantini/Desktop/Code_Daphne/daphne_brain/scorecard.json') as file:
        scorecard_json = json.load(file)
        for item in scorecard_json:
            if item['metric'] == scorecard_post_param:
                units = item['units']
                type_result = item['type']
                eval_string = item['evalString']
    ''' Check if the variables in the string to be calculate exist in the matfile, this uses a function called vars_for_calc(list, mat_file_path) and returns a list we can use to load them in the workspace'''
    # split the calculation string
    eng1.addpath('/Volumes/Encrypted/Mars2020/mars2020/MATLAB/', nargout=0)
    eng1.addpath('/Users/ssantini/Code/ExtractDataMatlab/MatlabEngine/', nargout=0)

    ''' Equations to calculate and remove the things left to the equal side '''
    eqs_to_calc = edl_scorecard_calculate.split(';')
    eqs_to_calc_rhs = [item[item.find('='):][1:] for item in eqs_to_calc if
                       item.find('=') != 1]  # we care about the variables in the rhs of the equation
    eq_vars = re.split('[,()/*;~= ]', "".join(eqs_to_calc_rhs)) # variable list

    ''' Check if variables are in the mat file '''
    path_mat = '/Users/ssantini/Code/ExtractDataMatlab/matout.mat'
    list_for_load = eng1.vars_for_calc(eq_vars, path_mat) # matlab script that checks what file is in the matfile'

    ''' Load  variables into workspace'''
    [eng1.load('/Users/ssantini/Code/ExtractDataMatlab/matout.mat', item, nargout=0) for item in list_for_load]  # load each
    [eng1.workspace[item] for item in list_for_load]  # add each to workspace

    for item in eqs_to_calc:
        eng1.eval(item, nargout=0)
    calculation_result = eng1.workspace['ans']
    calculation_string = eng1.eval(eval_string)

    calculation_response = "".join([str('The'), str(' '), str(scorecard_post_param),  str(' = '), str(calculation_string),
                                                str(units), str(" ("), str(type_result),str(") ")])

    return calculation_response

# TODO: add function for plotting metrics  (5010)
def edl_plot_from_matfile(mat_file, param_name1, param_name2, context):
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))

    for i in range(len(dict_NL)):
        key1 = param_name1
        if key1 in dict_NL:
            param_name1 = dict_NL[param_name1][0]  # this returns the value of the key

        else:
            param_name1 = param_name1
        key2 = param_name2
        if key2 in dict_NL:
            param_name2 = dict_NL[param_name2][0]  # this returns the value of the key

        else:
            param_name2 = param_name2
    var1_mat = eng1.load(mat_file, param_name1, nargout=0)
    var2_mat = eng1.load(mat_file, param_name2, nargout=0)  # loads in engine
    output_case = eng1.load(mat_file, 'output_case', nargout=0)
    val1 = eng1.workspace[param_name1] # returns to python
    val2 = eng1.workspace[param_name2]
    output_case = eng1.workspace['output_case']
    my_list = []
    output_case_py = []
    for _ in range(val2.size[0]):
        if output_case is not None:
            my_list.append((val1._data[_], val2._data[_], output_case._data[_]))
        else:
            my_list.append((val1._data[_], val2._data[_], None))


    return my_list

