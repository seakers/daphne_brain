from EOSS.data.problem_specific import get_orbit_dataset, get_instrument_dataset
import os
import json
from EOSS.tse.neoj_connection import Neo4jKnowledgeGraph

def get_instrument_names(problem):
        """Get instrument names from problem definition"""
        instrument_dataset = get_instrument_dataset_json(problem)["instruments"]
        instrument_names = []
        for i in range(len(instrument_dataset)):
            instrument_names.append(instrument_dataset[i]['Name'])
        return instrument_names  # Return a dictionary instead of the dataset

def get_orbit_names(problem):
    """Get orbit names from problem definition"""
    orbit_dataset = get_orbit_dataset_json(problem)
    orbit_names = []
    for i in range(len(orbit_dataset)):
        orbit_names.append(orbit_dataset[i]['name'])
    return orbit_names

def get_orbit_types():
    problem_types = ["Decadal2007", "ClimateCentric", "SMAP", "SMAP_JPL1", "SMAP_JPL2"]
    orbit_types = set()
    for problem in problem_types:
        orbit_dataset = get_orbit_dataset_json(problem)
        for i in range(len(orbit_dataset)):
            orbit_types.add(orbit_dataset[i]['type'])
    return list(orbit_types)

def get_neo4j_functions():
    uri = os.getenv("NEO4J_URI", "neo4j+s://3272b738.databases.neo4j.io")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "0tNj_x2cJuGZFrIljmm-rqAmiOoZ02zj5T7x_AciVwg")
    
    # Initialize connector
    kg = Neo4jKnowledgeGraph(uri, username, password)
    tools = []
    functions = []
    metrics = []
    if kg.connect():
        try:
            # Export the knowledge graph to JSON
            # output_path = os.path.join(os.path.dirname(__file__), "knowledge_graph.json")
            # data = kg.export_knowledge_graph(output_path)
            
            # tools = kg.get_all_tools()
            functions_tools = kg.get_function_to_tools_dict()
            metrics = kg.get_all_metrics()
            
        finally:
            kg.close()
    else:
        print("Failed to connect to Neo4j database")
    return metrics, functions_tools


def transform_frontend_config(problem,frontend_config):
    """
    Transform the frontend configuration to the format expected by the backend
    
    Args:
        frontend_config: Configuration from the frontend
        problem: Problem type 
    
    Returns:
        dict: Formatted configuration for the backend
    """
    import json
    from datetime import datetime, timedelta

    # const configuration = {
    #     problem_name: this.problemName,
    #     problem_type: this.problemType,
    #     evaluation: {
    #         metrics: metricOptions,
    #         functions: functionTools
    #     },
    #     design: {
    #         instruments: this.selectedInstruments,
    #         orbits: this.selectedOrbits
    #     },
    #     settings: this.settings
    #     };

        
    
    # Get data from frontend config
    problem_name = frontend_config.get('problemName', 'Default Mission')
    problem_type = frontend_config.get('problemType', 'Assigning')
    metrics = frontend_config.get('evaluation', {}).get('metrics', {})
    functions = frontend_config.get('evaluation', {}).get('functions', {})
    selected_instruments = frontend_config.get('design', {}).get('instruments', [])
    selected_orbits = frontend_config.get('design', {}).get('orbits', [])
    settings = frontend_config.get('settings', {})
    
    # Prepare the backend configuration
    backend_config = {
        "evaluation": {
            "metrics": {},
            "tool_constraints": {}
        },
        "mission": {
            "name": "TROPICS",
            "acronym": "TROPICS",
            "agency": {
                "agencyType": "GOVERNMENT",
                "@type": "Agency"
            },
            "start": datetime.now().strftime("%Y-%m-%dT00:00:00Z"),
            "duration": "P0Y0M07D",
            "target": [
                {
                    "latitude": {
                        "minValue": -90,
                        "maxValue": 90,
                        "@type": "QuantitativeValue"
                    },
                    "longitude": {
                        "minValue": -180,
                        "maxValue": 180,
                        "@type": "QuantitativeValue"
                    },
                    "@type": "Region"
                }
            ],
            "objectives": [
                {
                    "objectiveName": "MeanRevisitTime",
                    "objectiveType": "MIN",
                    "evaluator": "science_score"
                },
                {
                    "objectiveName": "lifecycleCost",
                    "objectiveType": "MIN",
                    "evaluator": "lifecycle_cost"
                },
                {
                    "objectiveName": "Coverage",
                    "objectiveType": "MAX",
                    "evaluator": "science_score"
                }
            ],
            "@type": "MissionConcept"
        },
        "designSpace": {
            "decisionVariables": {
                "orbitAssignment": {
                    "type": problem_type,
                    "parents": [],
                    "L": "payload",
                    "R": "orbit",
                    "resultType": "payload_orbit"
                }
            },
            "spaceSegment": [
                {
                    "constellationType": "DELTA_HOMOGENEOUS",
                    "numberSatellites": 1,
                    "numberPlanes": 1,
                    "orbit": [],
                    "satellites": [
                        {
                            "name": "MicroMAS-2",
                            "acronym": "MicroMAS-2",
                            "mass": 4,
                            "dryMass": 2.5,
                            "volume": 0.003,
                            "power": 9.1,
                            "commBand": ["X"],
                            "payload": [],
                            "techReadinessLevel": 9,
                            "isGroundCommand": True,
                            "isSpare": False,
                            "propellantType": "MONO_PROP",
                            "stabilizationType": "AXIS_3",
                            "@type": "Satellite"
                        }
                    ],
                    "@type": "Constellation"
                }
            ],
            "groundSegment": [
                {
                    "name": "TROPICS ground network",
                    "acronym": "TROPICS GN",
                    "numberStations": 1,
                    "groundStations": [
                        {
                            "name": "Wallops",
                            "acronym": "Wallops",
                            "agency": {
                                "agencyType": "GOVERNMENT",
                                "@type": "Agency"
                            },
                            "latitude": 37.940194,
                            "longitude": -75.466389,
                            "elevation": 1570,
                            "commBand": ["UHF"],
                            "@type": "GroundStation"
                        }
                    ],
                    "@type": "GroundNetwork"
                }
            ],
            "@type": "DesignSpace"
        },
        "settings": {
            "includePropulsion": False,
            "outputs": {
                "obsTimeStep": True,
                "keepLowLevelData": False,
                "@type": "AnalysisOutputs",
                "orbits.global": True,
                "orbits.local": True,
                "orbits.states": True,
                "orbits.access": True,
                "orbits.instrumentAccess": True
            },

            "@type": "AnalysisSettings"
        },

        "@type": "TradespaceSearch"
    }
    
    # Copy settings from frontend config to backend config
    for key in ["searchStrategy", "proxyInstrument", "proxyCostRisk", "proxyLaunch", 
                "proxyOrbits", "proxyValue", "proxyMaintenance", "useCache", "useThreading"]:
        if key in settings:
            backend_config["settings"][key] = settings[key]
    
    # Copy search parameters from frontend config to backend config
    if "searchParameters" in settings:
        backend_config["settings"]["searchParameters"] = settings["searchParameters"]
    
    # Process metrics
    for metric_name, minmax in metrics.items():
        print("metric_name", metric_name, "direction", minmax)
        # Convert metric name to match backend format
        backend_config["evaluation"]["metrics"][metric_name] = minmax.upper()
        
        # Add corresponding objective
        objective_type = "MAX" if minmax.upper() == "MAX" else "MIN"
        evaluator = metric_name_to_evaluator(metric_name)
        
        # backend_config["mission"]["objectives"].append({
        #     "objectiveName": metric_name,
        #     "objectiveType": objective_type,
        #     "evaluator": evaluator
        # })
    
    # Process tool constraints
    for func, tools in frontend_config.get('evaluation', {}).get('functions', {}).items():
        if tools and len(tools) > 0:
            backend_config["evaluation"]["tool_constraints"][func] = tools[0]
    
    # Process orbits
    orbit_dataset = get_orbit_dataset_json(problem)
    for orbit_name in selected_orbits:
        # Find orbit in dataset
        orbit_data = next((o for o in orbit_dataset if o["name"] == orbit_name), None)
        if orbit_data:
            orbit = {
                "orbitType": orbit_data.get("type", "LEO").upper(),
                "altitude": orbit_data.get("altitude", 600),
                "inclination": orbit_data.get("inclination", 98),
                "eccentricity": 0.0,
                "@type": "Orbit"
            }
            backend_config["designSpace"]["spaceSegment"][0]["orbit"].append(orbit)
    
    # Process instruments
    instrument_dataset = get_instrument_dataset_json(problem)["instruments"]
    print("instrument_dataset", instrument_dataset)

    for instrument_name in selected_instruments:
        # Find instrument in dataset
        for i in instrument_dataset:
            print("intrument i", i)
            if i["Name"] == instrument_name:
                print("instrument_data name", i)
                break
        instrument_data = next((i for i in instrument_dataset if i["Name"] == instrument_name), None)
        print("new instrument_data", instrument_data)
        if instrument_data:
            instrument = build_instrument_object(instrument_data)
            backend_config["designSpace"]["spaceSegment"][0]["satellites"][0]["payload"].append(instrument)
    
    return backend_config

def metric_name_to_evaluator(metric_name):
    """Convert metric name to evaluator name"""
    mapping = {
        "ScienceScore": "science_score",
        "LifecycleCost": "lifecycle_cost",
        "Coverage": "coverage",
        "HarmonicMeanRevisitTime": "revisit_time"
    }
    return mapping.get(metric_name, metric_name.lower())

def get_orbit_type(orbit_data):
    """Determine orbit type from orbit data"""
    name = orbit_data.get("name", "")
    if "SSO" in name:
        return "SSO"
    elif "LEO" in name:
        return "LEO"
    elif "GEO" in name:
        return "GEO"
    elif "MEO" in name:
        return "MEO"
    else:
        # Default to LEO if unknown
        return "LEO"

def build_instrument_object(instrument_data):
    """Build an instrument object from instrument data"""

    def nil_to_none(value):
        if value == "nil" or value == "NA" or value == "":
            return None
        return value
    
    def get_value(key, default=None, convert=None):
        value = instrument_data.get(key, default)
        value = nil_to_none(value)
        
        if value is None:
            return None
        
        # Try conversion if a conversion function is provided
        if convert and value is not None:
            try:
                return convert(value)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert {key}={value} to {convert.__name__}")
                return default
        return value
    
    dimensions = [1, 1, 1]
    if "dimension-x" in instrument_data and "dimension-y" in instrument_data and "dimension-z" in instrument_data:
        # Get dimensions from separate x, y, z fields
        try:
            dim_x = float(get_value("dimension-x", 1))
            dim_y = float(get_value("dimension-y", 1))
            dim_z = float(get_value("dimension-z", 1))
            dimensions = [dim_x, dim_y, dim_z]
        except ValueError:
            # Handle case where dimensions might be strings that can't be converted to float
            print(f"Warning: Could not parse dimensions for instrument {get_value('name')}")
    volume = dimensions[0] * dimensions[1] * dimensions[2]
    return {
        "scanTechnique": get_value("scanTechnique", "PUSHBROOM"),
        "type": get_value("type", "basic"),
        "numberOfDetectorsRowsAlongTrack": None,
        "numberOfDetectorsColsCrossTrack": None,
        "Fnum": get_value("Fnum", None),
        "focalLength": get_value("focalLength", None),
        "apertureDia": get_value("Aperture", None),
        "operatingWavelength": get_value("operatingWavelength", None),
        "bandwidth": get_value("bandwidth", None),
        "opticsSysEff": None,
        "quantumEff": None,
        "numOfReadOutE": None,
        "targetBlackBodyTemp": 20.0,
        "temperatureRange": [-10, 50],
        "detectorWidth": None,
        "maxDetectorExposureTime": None,
        "snrThreshold": None,
        "name": get_value("Name", "Unknown"),
        "acronym": get_value("Name", get_value("Name", "Unknown")),
        "mass": get_value("mass", 100),
        "dimensions": dimensions,
        "volume": volume,
        "power": get_value("characteristic-power", 100),
        "peakPower": get_value("characteristic-power", 100),
        "resolution": get_value("resolution", 10),
        "orientation": {
            "convention": "SIDE_LOOK",
            "sideLookAngle": None,
            "@type": "Orientation"
        },
        "fieldOfView": {
            "sensorGeometry": "RECTANGULAR",
            "fullConeAngle": None,
            "alongTrackFieldOfView": None,
            "crossTrackFieldOfView": get_value("Field-of-view", 55),
            "fieldOfRegard": get_value("fieldOfRegard", 100),
            "@type": "FieldOfView"
        },
        "dataRate": get_value("average-data-rate", 10.0),
        "bitsPerPixel": None,
        "techReadinessLevel": None,
        "mountType": "BODY",
        "@type": "Passive Optical Scanner"
    }

def get_orbit_dataset_json(problem):
    json_folder = os.path.join(os.path.dirname(__file__))
    json_file = os.path.join(json_folder, f"orbit_characteristics_{problem}.json")
    with open(json_file, 'r') as f:
        orbit_data = json.load(f)
    return orbit_data

def get_instrument_dataset_json(problem):
    json_folder = os.path.join(os.path.dirname(__file__))
    json_file = os.path.join(json_folder, f"instrument_characteristics_{problem}.json")
    with open(json_file, 'r') as f:
        instrument_data = json.load(f)
    return instrument_data


def save_backend_config(backend_config, problem_name=None):
    """
    Save the backend configuration to a JSON file
    
    Args:
        backend_config (dict): The backend configuration to save
        problem_name (str, optional): Name to use for the file. If None, uses timestamp
        
    Returns:
        str: Path to the saved file
    """
    import os
    import json
    import datetime
    
    # Create directory for saved configurations if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), "saved_configs")
    os.makedirs(config_dir, exist_ok=True)
    
    # Generate filename based on problem name or timestamp
    if problem_name:
        safe_name = "".join([c if c.isalnum() else "_" for c in problem_name])
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{timestamp}.json"
    
    # Full path to save file
    file_path = os.path.join(config_dir, filename)
    
    try:
        # Save configuration to JSON file with nice formatting
        with open(file_path, 'w') as f:
            json.dump(backend_config, f, indent=2, default=str)
        
        print(f"Configuration saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        return None
    

def transform_frontend_config_combining(problem, configuration):
    """
    Transform the frontend configuration for combinatorial problems into the backend format.
    
    Args:
        problem (str): The problem name
        configuration (dict): The frontend configuration
    
    Returns:
        dict: The transformed backend configuration
    """
    # Initialize the backend configuration
    backend_config = {
         "@type": "TradespaceSearch"
    }
    
    # Extract necessary components from frontend configuration
    problem_name = configuration.get('problem_name', 'Unnamed Problem')
    evaluation = configuration.get('evaluation', {})
    design_space = configuration.get('design', {})
    settings = configuration.get('settings', {})
    combining_decisions = configuration.get('combiningDecisions', [])
    
    # Transform evaluation section
    metrics = {}
    for metric, opt in evaluation.get('metrics', {}).items():
        # Convert min/max to MIN/MAX format
        metrics[metric] = opt.upper()
    
    # Transform functions to tool_constraints format
    tool_constraints = {}
    for func, tools in evaluation.get('functions', {}).items():
        # For each function, use the first tool if available
        if isinstance(tools, list) and tools:
            tool_constraints[func] = tools[0]
        elif isinstance(tools, str):
            tool_constraints[func] = tools
    
    backend_config['evaluation'] = {
        "metrics": metrics,
        "tool_constraints": tool_constraints
    }
    
    # Create default mission section
    backend_config['mission'] = {
        "name": "TROPICS",
        "acronym": "TROPICS",
        "agency": {
            "agencyType": "GOVERNMENT",
            "@type": "Agency"
        },
        "start": "2019-08-01T00:00:00Z",
        "duration": "P0Y0M07D",
        "target": [
            {
                "latitude": {
                    "minValue": -90,
                    "maxValue": 90,
                    "@type": "QuantitativeValue"
                },
                "longitude": {
                    "minValue": -180,
                    "maxValue": 180,
                    "@type": "QuantitativeValue"
                },
                "@type": "Region"
            }
        ],
        "objectives": [
            {
                "objectiveName": "MeanRevisitTime",
                "objectiveType": "MIN",
                "evaluator": "science_score"
            },
            {
                "objectiveName": "lifecycleCost",
                "objectiveType": "MIN",
                "evaluator": "lifecycle_cost"
            },
            {
                "objectiveName": "Coverage",
                "objectiveType": "MAX",
                "evaluator": "science_score"
            }
        ],
        "@type": "MissionConcept"
    }
    
    # Process design space
    space_segment = design_space.get('spaceSegment', [])
    if space_segment:
        # Ensure we're using the variable values for combining decisions
        # Process fixed and variable design values
        for segment in space_segment:
            # Process orbit parameters
            if 'orbit' in segment and segment['orbit']:
                orbit = segment['orbit']
                
                # Handle orbit parameters that might be design variables
                for param in ['altitude', 'inclination', 'orbitType']:
                    if param in combining_decisions:
                        # Get the variable values from designValues
                        if param in design_space.get('designValues', {}):
                            orbit[param] = design_space['designValues'].get(param, [])
                
            # Process satellite parameters
            if 'satellites' in segment and segment['satellites']:
                for satellite in segment['satellites']:
                    # Process payload parameters
                    if 'payload' in satellite and satellite['payload']:
                        for payload in satellite['payload']:
                            for param in combining_decisions:
                                if param in payload:
                                    # Get values for payload design variables
                                    if param in design_space.get('designValues', {}):
                                        payload[param] = design_space['designValues'].get(param, [])
    
    # Create design space structure
    backend_config['designSpace'] = {
        "decisionVariables": {
            "missionConfigurations": {
                "type": "Combining",
                "combiningDecisions": combining_decisions,
                "parents": []
            }
        },
        "spaceSegment": space_segment,
        "groundSegment": [
            {
                "name": "TROPICS ground network",
                "acronym": "TROPICS GN",
                "numberStations": 1,
                "groundStations": [
                    {
                        "name": "Wallops",
                        "acronym": "Wallops",
                        "agency": {
                            "agencyType": "GOVERNMENT",
                            "@type": "Agency"
                        },
                        "latitude": 37.940194,
                        "longitude": -75.466389,
                        "elevation": 1570,
                        "commBand": ["UHF"],
                        "@type": "GroundStation"
                    }
                ],
                "@type": "GroundNetwork"
            }
        ],
        "@type": "DesignSpace"
    }
    
    # Add settings section
    backend_config['settings'] = settings.copy()
    
    # Add default output settings if not provided
    if 'outputs' not in backend_config['settings']:
        backend_config['settings']['outputs'] = {
            "obsTimeStep": True,
            "keepLowLevelData": False,
            "@type": "AnalysisOutputs",
            "orbits.global": True,
            "orbits.local": True,
            "orbits.states": True,
            "orbits.access": True,
            "orbits.instrumentAccess": True
        }
    
    # Add includePropulsion if not provided
    if 'includePropulsion' not in backend_config['settings']:
        backend_config['settings']['includePropulsion'] = False
    
    return backend_config