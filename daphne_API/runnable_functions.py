import logging
from VASSAR_API.api import VASSARClient
from data_mining_API.api import DataMiningClient
from daphne_API.critic.critic import CRITIC

logger = logging.getLogger('VASSAR')

ORBIT_DATASET = [
    {"name": "LEO-600-polar-NA", "type": "Inclined, non-sun-synchronous", "altitude": 600, "LST": ""},
    {"name": "SSO-600-SSO-AM", "type": "Sun-synchronous", "altitude": 600, "LST": "AM"},
    {"name": "SSO-600-SSO-DD", "type": "Sun-synchronous", "altitude": 600, "LST": "DD"},
    {"name": "SSO-800-SSO-DD", "type": "Sun-synchronous", "altitude": 800, "LST": "DD"},
    {"name": "SSO-800-SSO-PM", "type": "Sun-synchronous", "altitude": 800, "LST": "PM"}]

INSTRUMENT_DATASET = [
    {"name": "ACE_ORCA", "type": "Ocean colour instruments", "technology": "Medium-resolution spectro-radiometer", "geometry": "Cross-track scanning", "wavebands": ["UV","VIS","NIR","SWIR"]},
    {"name": "ACE_POL", "type": "Multiple direction/polarisation radiometers", "technology": "Multi-channel/direction/polarisation radiometer", "geometry": "ANY", "wavebands": ["VIS","NIR","SWIR"]},
    {"name": "ACE_LID", "type": "Lidars", "technology": "Atmospheric lidar", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR"]},
    {"name": "CLAR_ERB", "type": "Hyperspectral imagers", "technology": "Multi-purpose imaging Vis/IR radiometer", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR","SWIR","TIR","FIR"]},
    {"name": "ACE_CPR", "type": "Cloud profile and rain radars", "technology": "Cloud and precipitation radar", "geometry": "Nadir-viewing", "wavebands": ["MW"]},
    {"name": "DESD_SAR", "type": "Imaging microwave radars", "technology": "Imaging radar (SAR)", "geometry": "Side-looking", "wavebands": ["MW","L-Band","S-Band"]},
    {"name": "DESD_LID", "type": "Lidars", "technology": "Lidar altimeter", "geometry": "ANY", "wavebands": ["NIR"]},
    {"name": "GACM_VIS", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["UV","VIS"]},
    {"name": "GACM_SWIR", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["SWIR"]},
    {"name": "HYSP_TIR", "type": "Imaging multi-spectral radiometers (vis/IR)", "technology": "Medium-resolution IR spectrometer", "geometry": "Whisk-broom scanning", "wavebands": ["MWIR", "TIR"]},
    {"name": "POSTEPS_IRS", "type": "Atmospheric temperature and humidity sounders", "technology": "Medium-resolution IR spectrometer", "geometry": "Cross-track scanning", "wavebands": ["MWIR", "TIR"]},
    {"name": "CNES_KaRIN", "type": "Radar altimeters", "technology": "Radar altimeter", "geometry": "Nadir-viewing", "wavebands": ["MW", "Ku-Band"]}]


def parse_base_feature_expression(feature_expression):

    e = feature_expression[1:-1]
    out = None
    
    featureType = e.split("[",1)[0]
    arguments = e.split("[",1)[1][:-1]
    
    argSplit = arguments.split(";")
    
    orbitIndices = argSplit[0]
    instrumentIndices = argSplit[1]
    numbers = argSplit[2]
    
    print(feature_expression)
    
    if orbitIndices:
        orbitNames = [ORBIT_DATASET[int(i)]['name'] for i in orbitIndices.split(",")]
    if instrumentIndices:
        instrumentNames = [INSTRUMENT_DATASET[int(i)]['name'] for i in instrumentIndices.split(",")]
    if numbers:
        numbers = [int(n) for n in numbers.split(",")]  
        
    try:
    
        if featureType == "present":
            out = "{} is used".format(instrumentNames[0])
        elif featureType == "absent":
            out = "{} is not used".format(instrumentNames[0])
        elif featureType == "inOrbit":
            out = ["Instruments", ", ".join(instrumentNames),"are assigned to",orbitNames[0]]
            out = " ".join(out)
        elif featureType == "notInOrbit":
            out = ["Instruments", ", ".join(instrumentNames),"are not assigned to",orbitNames[0]]
            out = " ".join(out)
        elif featureType == "together":
            out = "Instruments {} are assigned to the same orbit".format(", ".join(instrumentNames))
        elif featureType == "separate":
            out = "Instruments {} are never assigned to the same orbit".format(", ".join(instrumentNames))        
        elif featureType == "emptyOrbit":
            out = "No spacecraft flies in {}".format(orbitNames[0])
        else:
            raise ValueError()
    
        return out
    
    except ValueError as e:
        msg = "Error in parsing feature expression: {}".format(feature_expression) 
        print(msg)
        logger.error(msg)        
    
def parse_feature_expression(feature_expression):
    out = []
    if "&&" in feature_expression:
        individual_features = feature_expression.split("&&")
        for feat in individual_features:
            out.append(parse_base_feature_expression(feat))
    elif "||" in feature_expression:
        pass
    else:
        out.append(parse_base_feature_expression(feature_expression))
    
    return " and ".join(out)
    

def data_mining_run(designs, behavioral, non_behavioral):
    
    client = DataMiningClient()
    try:
        # Start connection with data_mining
        client.startConnection()
        
        support_threshold = 0.002
        confidence_threshold = 0.2
        lift_threshold = 1
        
        features = client.getDrivingFeatures(behavioral, non_behavioral, designs, support_threshold, confidence_threshold, lift_threshold)
        
        # End the connection before return statement
        client.endConnection()
        
        result = []
        for i in range(3): # Generate answers for the first 5 features
            print(features[i]['name'])            
            advice = parse_feature_expression(features[i]['name'])
            result.append({
                "type": "Expert",
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


def Critic_general_call(design_id, designs):
    client = VASSARClient()
    critic = CRITIC()

    try:
        # Start connection with VASSAR
        client.startConnection()
        num_design_id = int(design_id[1:])
        # Criticize architecture (based on rules)
        result1 = client.client.getCritique(designs[num_design_id]['inputs'])
        client.endConnection()
        result = []
        for advice in result1:
            result.append({
                "type": "Expert",
                "advice": advice
            })
        # Criticize architecture (based on database)
        result2 = critic.criticize_arch(designs[num_design_id]['inputs'])
        result.extend(result2)
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
