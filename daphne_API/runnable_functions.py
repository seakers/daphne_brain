import logging
from VASSAR_API.api import VASSARClient
from data_mining_API.api import DataMiningClient
from daphne_API.critic.critic import CRITIC
import pandas

import traceback
import math
import numpy as np
import sys

logger = logging.getLogger('VASSAR')

ORBIT_DATASET = [
    {"alias": "1", "name": "LEO-600-polar-NA", "type": "Inclined, non-sun-synchronous", "altitude": 600, "LST": ""},
    {"alias": "2", "name": "SSO-600-SSO-AM", "type": "Sun-synchronous", "altitude": 600, "LST": "AM"},
    {"alias": "3", "name": "SSO-600-SSO-DD", "type": "Sun-synchronous", "altitude": 600, "LST": "DD"},
    {"alias": "4", "name": "SSO-800-SSO-DD", "type": "Sun-synchronous", "altitude": 800, "LST": "DD"},
    {"alias": "5", "name": "SSO-800-SSO-PM", "type": "Sun-synchronous", "altitude": 800, "LST": "PM"}]

INSTRUMENT_DATASET = [
    {"alias": "A", "name": "ACE_ORCA", "type": "Ocean colour instruments", "technology": "Medium-resolution spectro-radiometer", "geometry": "Cross-track scanning", "wavebands": ["UV","VIS","NIR","SWIR"]},
    {"alias": "B", "name": "ACE_POL", "type": "Multiple direction/polarisation radiometers", "technology": "Multi-channel/direction/polarisation radiometer", "geometry": "ANY", "wavebands": ["VIS","NIR","SWIR"]},
    {"alias": "C", "name": "ACE_LID", "type": "Lidars", "technology": "Atmospheric lidar", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR"]},
    {"alias": "D", "name": "CLAR_ERB", "type": "Hyperspectral imagers", "technology": "Multi-purpose imaging Vis/IR radiometer", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR","SWIR","TIR","FIR"]},
    {"alias": "E", "name": "ACE_CPR", "type": "Cloud profile and rain radars", "technology": "Cloud and precipitation radar", "geometry": "Nadir-viewing", "wavebands": ["MW"]},
    {"alias": "F", "name": "DESD_SAR", "type": "Imaging microwave radars", "technology": "Imaging radar (SAR)", "geometry": "Side-looking", "wavebands": ["MW","L-Band","S-Band"]},
    {"alias": "G", "name": "DESD_LID", "type": "Lidars", "technology": "Lidar altimeter", "geometry": "ANY", "wavebands": ["NIR"]},
    {"alias": "H", "name": "GACM_VIS", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["UV","VIS"]},
    {"alias": "I", "name": "GACM_SWIR", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["SWIR"]},
    {"alias": "J", "name": "HYSP_TIR", "type": "Imaging multi-spectral radiometers (vis/IR)", "technology": "Medium-resolution IR spectrometer", "geometry": "Whisk-broom scanning", "wavebands": ["MWIR", "TIR"]},
    {"alias": "K", "name": "POSTEPS_IRS", "type": "Atmospheric temperature and humidity sounders", "technology": "Medium-resolution IR spectrometer", "geometry": "Cross-track scanning", "wavebands": ["MWIR", "TIR"]},
    {"alias": "L", "name": "CNES_KaRIN", "type": "Radar altimeters", "technology": "Radar altimeter", "geometry": "Nadir-viewing", "wavebands": ["MW", "Ku-Band"]}]


def data_mining_run(designs, behavioral, non_behavioral):
    
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
        maxFeatures = 3
        if len(features) > 3:
            pass
        else:
            maxFeatures = len(features)

        for i in range(maxFeatures): # Generate answers for the first 3 features
            advice = feature_expression_to_string(features[i]['name'])
            result.append({
                "type": "Analyzer",
                "advice": advice
            })
        return result
    
    except Exception:
        logger.exception('Exception in running data mining')
        client.endConnection()
        return None


def VASSAR_load_objectives_information(design_id, designs):
    client = VASSARClient()

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id[1:])
        list = client.client.getScoreExplanation(designs[num_design_id]['inputs'])

        # End the connection before return statement
        client.endConnection()
        return list

    except Exception:
        logger.exception('Exception in loading objective information')
        client.endConnection()
        return None


def VASSAR_get_instrument_parameter(vassar_instrument, instrument_parameter, context):
    context["vassar_instrument"] = vassar_instrument
    context["instrument_parameter"] = instrument_parameter
    capabilities_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric Instrument Capability Definition2.xls',
                                           sheet_name='CHARACTERISTICS')
    capability_found = False
    capability_value = None
    for row in capabilities_sheet.itertuples(name='Instrument'):
        if row[0].split()[1] == vassar_instrument:
            for i in range(1, len(row)):
                if row[i].split()[0] == instrument_parameter:
                    capability_found = True
                    capability_value = row[i].split()[1]

    if capability_found:
        return 'The ' + instrument_parameter + ' for ' + vassar_instrument + ' is ' + capability_value
    else:
        instrument_sheet = pandas.read_excel('./daphne_API/xls/Climate-centric Instrument Capability Definition2.xls',
                                               sheet_name=vassar_instrument, header=None)
        for i in range(2, len(instrument_sheet.columns)):
            if instrument_sheet[i][0].split()[0] == instrument_parameter:
                capability_found = True
            if capability_found:
                return 'I have found different values for this parameter depending on the measurement. ' \
                       'Please tell me for which measurement you want this parameter: ' \
                       + ', '.join([measurement[11:-1] for measurement in instrument_sheet[1]])
            else:
                return 'I have not found any information for this measurement.'


def Critic_general_call(design_id, designs, experiment_stage=0):
    client = VASSARClient()
    critic = CRITIC()

    try:
        this_design = None
        num_design_id = int(design_id[1:])
                
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
        
        # Criticize architecture (based on rules)
        result1 = client.client.getCritique(this_design['inputs'])
        result = []
        for advice in result1:
            result.append({
                "type": "Expert",
                "advice": advice
            })
            
        # Criticize architecture (based on explorer)
        def getAdvicesFromBitStringDiff(diff):
            out = []
            ninstr = len(INSTRUMENT_DATASET)
                        
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
                advice.append("instrument {}".format(INSTRUMENT_DATASET[instrIndex]['alias']))
                advice.append("to orbit {}".format(ORBIT_DATASET[orbitIndex]['alias']))
                    
                advice = " ".join(advice)
                out.append(advice)
            
            out = ", and ".join(out)
            out = out[0].upper() + out[1:]
            return out
                
        original_outputs = this_design['outputs']
        original_inputs = this_design['inputs']
        
        archs = client.runLocalSearch(this_design['inputs'], experiment_stage)
        advices = []
        for arch in archs:
            new_outputs = arch['outputs']
            
            new_design_inputs = arch['inputs']
            diff = [a-b for a,b in zip(new_design_inputs,original_inputs)]  
            advice = [getAdvicesFromBitStringDiff(diff)]
            
            # TODO: Generalize the code for comparing each metric. Currently it assumes two metrics: science and cost
            if new_outputs[0] > original_outputs[0] and new_outputs[1] < original_outputs[1]:
                # New solution dominates the original solution
                advice.append(" to increase science and lower cost.")
            elif new_outputs[0] > original_outputs[0]:
                advice.append(" to increase science.")
            elif new_outputs[1] < original_outputs[1]:
                advice.append(" to lower cost.")
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
                unsatisfied = get_feature_unsatisfied(features[0]['name'], this_design)
                satisfied = get_feature_satisfied(features[0]['name'], this_design)
                                
                if type(unsatisfied) is not list:
                    unsatisfied = [unsatisfied]
                    
                if type(satisfied) is not list:
                    satisfied = [satisfied]
                    
                for exp in unsatisfied:
                    if exp == "":
                        continue
                    advices.append("Based on the data mining result, I advise you to make the following change: " + feature_expression_to_string(exp, isCritique=True))
                
                for exp in satisfied:
                    if exp == "":
                        continue
                    advices.append("Based on the data mining result, these are the good features. Consider keeping them: " + feature_expression_to_string(exp, isCritique=False))                    
            
            # End the connection before return statement
            client.endConnection()
            
            for i in range(len(advices)): # Generate answers for the first 5 features
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


def Critic_specific_call(design_id, agent, designs):
    critic = CRITIC()
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
    

def base_feature_expression_to_string(feature_expression, isCritique = False):    
    
    try:    
    
        e = feature_expression[1:-1]
        out = None

        featureType = e.split("[")[0]
        arguments = e.split("[")[1][:-1]

        argSplit = arguments.split(";")

        orbitIndices = argSplit[0]
        instrumentIndices = argSplit[1]
        numbers = argSplit[2]

        if orbitIndices:
            orbitNames = [ORBIT_DATASET[int(i)]['alias'] for i in orbitIndices.split(",")]
        if instrumentIndices:
            instrumentNames = [INSTRUMENT_DATASET[int(i)]['alias'] for i in instrumentIndices.split(",")]
        if numbers:
            numbers = [int(n) for n in numbers.split(",")]  
        
        if featureType == "present":
            if isCritique:
                out = "add {}".format(instrumentNames[0])
            else:
                out = "{} is used".format(instrumentNames[0])
        elif featureType == "absent":
            if isCritique:
                out = "remove {}".format(instrumentNames[0])
            else:            
                out = "{} is not used in any orbit".format(instrumentNames[0])
        elif featureType == "inOrbit":
            if isCritique:
                out = ["assign instruments", ", ".join(instrumentNames),"to orbit",orbitNames[0]]
            else:               
                out = ["instruments", ", ".join(instrumentNames),"are assigned to orbit",orbitNames[0]]
            out = " ".join(out)
            
        elif featureType == "notInOrbit":
            if isCritique:
                out = ["remove instruments", ", ".join(instrumentNames),"in orbit",orbitNames[0]]
            else:               
                out = ["instruments", ", ".join(instrumentNames),"are not assigned to orbit",orbitNames[0]]
            out = " ".join(out)
        elif featureType == "together":
            if isCritique:
                out = "assign instruments {} to the same orbit".format(", ".join(instrumentNames))
            else:    
                out = "instruments {} are assigned to the same orbit".format(", ".join(instrumentNames))
        elif featureType == "separate":
            if isCritique:
                out = "do not assign instruments {} to the same orbit".format(", ".join(instrumentNames))        
            else:    
                out = "instruments {} are never assigned to the same orbit".format(", ".join(instrumentNames))        
        elif featureType == "emptyOrbit":
            if isCritique:
                out = "no spacecraft should fly in orbit {}".format(orbitNames[0])
            else:              
                out = "no spacecraft flies in orbit {}".format(orbitNames[0])
        else:
            raise ValueError('Uncrecognized feature name: {}'.format(featureType))
        return out
    
    except Exception as e:
        msg = "Error in parsing feature expression: {}".format(feature_expression) 
        print(msg)
        traceback.print_exc(file=sys.stdout)
        logger.error(msg)  
        
    
def feature_expression_to_string(feature_expression, isCritique = False):
    out = []
    # TODO: Generalize the feature expression parsing. 
    # Currently assumes that the feature only contains conjunctions but no disjunction
    if "&&" in feature_expression:
        individual_features = feature_expression.split("&&")
        for feat in individual_features:
            if feat == "":
                continue
            out.append(base_feature_expression_to_string(feat, isCritique))
    elif "||" in feature_expression:
        pass
    else:
        if not feature_expression == "":
            out.append(base_feature_expression_to_string(feature_expression, isCritique))
    
    out = " AND ".join(out)
    out = out[0].upper() + out[1:]
    
    return out


def get_feature_satisfied(expression, design):
    
    out = []
    
    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp,design))
        return out
    
    else:
        # TODO: Generalize the feature expression parsing. 
        # Currently assumes that the feature only contains conjunctions but no disjunction        
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]
            
        for feat in individual_features:  
            satisfied = apply_base_filter(feat,design)
            if satisfied:
                out.append(feat)        
        return "&&".join(out)


def get_feature_unsatisfied(expression, design):
    
    out = []
    
    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp,design))
        return out
    
    else:
        # TODO: Generalize the feature expression parsing. 
        # Currently assumes that the feature only contains conjunctions but no disjunction        
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]
            
        for feat in individual_features:  
            satisfied = apply_base_filter(feat,design)
            if not satisfied:
                out.append(feat)
        return "&&".join(out)
    
        
def apply_base_filter(filterExpression,design):

    expression = filterExpression
    
    # Preset filter: {presetName[orbits;instruments;numbers]} 
    if expression[0] == "{" and expression[-1] == "}":
        expression = expression[1:-1]
    
    norb = len(ORBIT_DATASET)
    ninstr = len(INSTRUMENT_DATASET)
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
            if len(instr)==0:
                return False
            out = False
            instr = int(instr)
            for i in range(norb):
                if inputs[ninstr*i + instr]:
                    out=True
                    break

        elif featureType == "absent":
            if len(instr)==0:
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
                

            



