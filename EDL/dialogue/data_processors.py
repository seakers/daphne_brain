import json
import pandas as pd

from dialogue.param_processing_helpers import not_processed


def process_parameter(extracted_data, options, context):
    db_names = {"entry mass": "Mission.entry_mass", "name":"Mission.name","status": "Mission.status",
                "launch date": "Mission.launch_date", "launch vehicle":"Mission.launch_vehicle",
                "full name":"Mission.full_name", "applications":"Mission.applications",
                "landing site": "Mission.landing_site", "landing site elevation":"Mission.landing_site_elevation",
                "touchdown mass":"Mission.touchdown_mass", "useful landed mass":"Mission.useful_landed_mass",
                "entry strategy":"Entry.entry_strategy", "entry vehicle": "Entry.entry_vehicle",
                "entry interface X":"Entry.entry_interfaceX", "entry interface Y":"Entry.entry_interfaceY",
                "entry interface Z": "Entry.entry_interfaceZ","orbital direction":"Entry.orbital_direction",
                "entry velocity":"Entry.entry_velocity", "entry lift control":"Entry.entry_lift_control",
                "entry attitude control":"Entry.entry_attitude_control", "entry guidance":"Entry.entry_guidance",
                "entry angle of attack":"Entry.entry_angle_of_attack",
                "ballistic coefficient":"Entry.ballistic_coefficient", "lift to drag ratio":"Entry.ld_ratio",
                "peak deceleration":"Entry.peak_deceleration",
                "descent attitude control":"ParachuteDescent.descent_attitude_control",
                "drag coefficient":"ParachuteDeployConditions.drag_coeff",
                "deploy mach number":"ParachuteDeployConditions.deploy_mach_no",
                "deploy dynamic pressure":"ParachuteDeployConditions.deploy_dyn_pressure",
                "wind relative velocity":"ParachuteDeployConditions.wind_rel_velocity",
                "altitude parachute deploy":"ParachuteDeployConditions.altitude_deploy",
                "backshell separation altitude":"BackshellSeparation.bs_separation_altitude",
                "backshell separation velocity":"BackshellSeparation.bs_separation_velocity",
                "backshell separation mechanism":"BackshellSeparation.bs_separation_mechanism",
                "heat shield geometry":"Heatshield.hs_geometry",
                "heat shield diameter":"HeatShield.hs_diameter",
                "heat shield TPS":"HeatShield.hs_tps",
                "heat shield thickness":"HeatShield.hs_thickness",
                "heat shield peak heat rate":"HeatShield.hs_peak_heat_rate",
                "heat shield peak stagnation pressure":"HeatShield.hs_peak_stagnation_pressure",
                "horizontal velocity sensing":"ParachuteDescentSensing.horizontal_velocity_sensing",
                "altitude sensing": "ParachuteDescentSensing.altitude_sensing",
                "horizontal velocity control":"PoweredDescent.horizontal_velocity_control",
                "terminal descent decelerator":"PoweredDescent.terminal_descent_decelerator",
                "terminal descent velocity control":"PoweredDescent.terminal_descent_velocity_control",
                "vertical descent rate":"PoweredDescent.vertical_descent_rate",
                "fuel burn":"PoweredDescent.fuel_burn",
                "touchdown vertical velocity":"Touchdown.touchdown_vertical_velocity",
                "touchdown horizontal velocity": "Touchdown.touchdown_horizontal_velocity",
                "touchdown attenuation":"Touchdown.touchdown_attenuation",
                "touchdown rock height capability":"Touchdown.touchdown_rock_height_capability",
                "touchdown slope capability":"Touchdown.touchdown_slope_capability",
                "touchdown sensor":"Touchdown.touchdown_sensor",
                "touchdown sensing":"Touchdown.touchdown_sensing", "simulation":"Mission.simulation_data"
                }
    return db_names[extracted_data]


def process_edl_mat_file_parameter(extracted_data, options, context):
    file_path = pd.read_excel('/Users/ssantini/Desktop/Code_Daphne/command_classifier/edlsimqueries.xlsx')
    list_descriptions = list(file_path[0])
    '''Load as dictionary'''
    dict_NL = json.load(open("/Users/ssantini/Code/ExtractDataMatlab/ExtractSimDataUsingNL/sim_data_dict.txt"))
    return dict_NL[extracted_data][0]


def process_edl_scorecard_calculate(extracted_data, options, context):
    metric_calculation = []
    with open('scorecard.json') as file:
        scorecard_json = json.load(file)
        scorecard_metrics = []
        for item in scorecard_json:
            scorecard_metrics.append(item['metric'])
            metric_calculation = {x['metric']: x['calculation'] for x in scorecard_json if x['metric'] is not None}

    return metric_calculation[extracted_data]

# def process_scorecard_post_results(extracted_data, options, context):
#     dict_all_metrics = json.load(open("/Users/ssantini/Desktop/Code_Daphne/daphne_brain/dict_all_metrics.txt"))
#     post_names = dict_all_metrics
#     return post_names[extracted_data]


def process_scorecard_edlmetricsheet_results(extracted_data, options, context):
    edlmetricssheet_names = {"Peak Decleration": ["edl_metric.entries[0].type", "edl_metric.entries[0].units",
                                                  "edl_metric.entries[0].POST_results",
                                                  "edl_metric.entries[0].GreatOrLess", "edl_metric.entries[0].Flag",
                                                  "edl_metric.entries[0].OutOfSpec",
                                                  "edl_metric.entries[0].Description"],
                             "Parachute Deploy Mach Number": ["edl_metric.entries[1].type",
                                                              "edl_metric.entries[1].units",
                                                              "edl_metric.entries[1].POST_results",
                                                              "edl_metric.entries[1].GreatOrLess",
                                                              "edl_metric.entries[1].Flag",
                                                              "edl_metric.entries[1].OutOfSpec",
                                                              "edl_metric.entries[1].Description"],
                             "Peak Parachute Inflation Load (MEV)": ["edl_metric.entries[2].type",
                                                                     "edl_metric.entries[2].units",
                                                                     "edl_metric.entries[2].POST_results",
                                                                     "edl_metric.entries[2].GreatOrLess",
                                                                     "edl_metric.entries[2].Flag",
                                                                     "edl_metric.entries[2].OutOfSpec",
                                                                     "edl_metric.entries[2].Description"],
                             "Parachute Deploy Range Error": ["edl_metric.entries[3].type",
                                                              "edl_metric.entries[3].units",
                                                              "edl_metric.entries[3].POST_results",
                                                              "edl_metric.entries[3].GreatOrLess",
                                                              "edl_metric.entries[3].Flag",
                                                              "edl_metric.entries[3].OutOfSpec",
                                                              "edl_metric.entries[3].Description"],
                             "Timeline Margin": ["edl_metric.entries[4].type", "edl_metric.entries[4].units",
                                                 "edl_metric.entries[4].POST_results",
                                                 "edl_metric.entries[4].GreatOrLess",
                                                 "edl_metric.entries[4].Flag",
                                                 "edl_metric.entries[4].OutOfSpec",
                                                 "edl_metric.entries[4].Description"],
                             "Touchdown Vertical Velocity": ["edl_metric.entries[5].type",
                                                             "edl_metric.entries[5].units",
                                                             "edl_metric.entries[5].POST_results",
                                                             "edl_metric.entries[5].GreatOrLess",
                                                             "edl_metric.entries[5].Flag",
                                                             "edl_metric.entries[5].OutOfSpec",
                                                             "edl_metric.entries[5].Description"],
                             "Touchdown Horizontal Velocity": ["edl_metric.entries[6].type",
                                                               "edl_metric.entries[6].units",
                                                               "edl_metric.entries[6].POST_results",
                                                               "edl_metric.entries[6].GreatOrLess",
                                                               "edl_metric.entries[6].Flag",
                                                               "edl_metric.entries[6].OutOfSpec",
                                                               "edl_metric.entries[6].Description"],
                             "Hazardous Landing Fraction": ["edl_metric.entries[7].type", "edl_metric.entries[7].units",
                                                            "edl_metric.entries[7].POST_results",
                                                            "edl_metric.entries[7].GreatOrLess",
                                                            "edl_metric.entries[7].Flag",
                                                            "edl_metric.entries[7].OutOfSpec",
                                                            "edl_metric.entries[7].Description"],
                             "Fuel Remaining": ["edl_metric.entries[8].type", "edl_metric.entries[8].units",
                                                "edl_metric.entries[8].POST_results",
                                                "edl_metric.entries[8].GreatOrLess", "edl_metric.entries[8].Flag",
                                                "edl_metric.entries[8].OutOfSpec", "edl_metric.entries[8].Description"],
                             "Fuel Used": ["edl_metric.entries[9].type", "edl_metric.entries[9].units",
                                           "edl_metric.entries[9].POST_results", "edl_metric.entries[9].GreatOrLess",
                                           "edl_metric.entries[9].Flag", "edl_metric.entries[9].OutOfSpec",
                                           "edl_metric.entries[9].Description"],
                             "Range to Target": ["edl_metric.entries[10].type", "edl_metric.entries[10].units",
                                                 "edl_metric.entries[10].POST_results",
                                                 "edl_metric.entries[10].GreatOrLess", "edl_metric.entries[10].Flag",
                                                 "edl_metric.entries[10].OutOfSpec",
                                                 "edl_metric.entries[10].Description"],
                             "TRN End-to-End Performance": ["edl_metric.entries[11].type",
                                                            "edl_metric.entries[11].units",
                                                            "edl_metric.entries[11].POST_results",
                                                            "edl_metric.entries[11].GreatOrLess",
                                                            "edl_metric.entries[11].Flag",
                                                            "edl_metric.entries[11].OutOfSpec",
                                                            "edl_metric.entries[11].Description"],
                             "LVS Reduced Performance Timeline Margin": ["edl_metric.entries[12].type",
                                                                         "edl_metric.entries[12].units",
                                                                         "edl_metric.entries[12].POST_results",
                                                                         "edl_metric.entries[12].GreatOrLess",
                                                                         "edl_metric.entries[12].Flag",
                                                                         "edl_metric.entries[12].OutOfSpec",
                                                                         "edl_metric.entries[12].Description"],
                             "LVS Fine Mode Timeline Margin": ["edl_metric.entries[13].type",
                                                               "edl_metric.entries[13].units",
                                                               "edl_metric.entries[13].POST_results",
                                                               "edl_metric.entries[13].GreatOrLess",
                                                               "edl_metric.entries[13].Flag",
                                                               "edl_metric.entries[13].OutOfSpec",
                                                               "edl_metric.entries[13].Description"],
                             "Probability of Success - Terrain Only": ["edl_metric.entries[14].type",
                                                                       "edl_metric.entries[14].units",
                                                                       "edl_metric.entries[14].POST_results",
                                                                       "edl_metric.entries[14].GreatOrLess",
                                                                       "edl_metric.entries[14].Flag",
                                                                       "edl_metric.entries[14].OutOfSpec",
                                                                       "edl_metric.entries[14].Description"],
                             "Parachute Deploy Flight Path Angle ": ["edl_metric.entries[15].type",
                                                                     "edl_metric.entries[15].units",
                                                                     "edl_metric.entries[15].POST_results",
                                                                     "edl_metric.entries[15].GreatOrLess",
                                                                     "edl_metric.entries[15].Flag",
                                                                     "edl_metric.entries[15].OutOfSpec",
                                                                     "edl_metric.entries[15].Description"],
                             "TDS NAV INIT (Mode 20) Altitude ": ["edl_metric.entries[16].type",
                                                                  "edl_metric.entries[16].units",
                                                                  "edl_metric.entries[16].POST_results",
                                                                  "edl_metric.entries[16].GreatOrLess",
                                                                  "edl_metric.entries[16].Flag",
                                                                  "edl_metric.entries[16].OutOfSpec",
                                                                  "edl_metric.entries[16].Description"],
                             "Backshell Separation Altitude ": ["edl_metric.entries[17].type",
                                                                "edl_metric.entries[17].units",
                                                                "edl_metric.entries[17].POST_results",
                                                                "edl_metric.entries[17].GreatOrLess",
                                                                "edl_metric.entries[17].Flag",
                                                                "edl_metric.entries[17].OutOfSpec",
                                                                "edl_metric.entries[17].Description"],
                             "Touchdown Ellipse Major Axis ": ["edl_metric.entries[18].type",
                                                               "edl_metric.entries[18].units",
                                                               "edl_metric.entries[18].POST_results",
                                                               "edl_metric.entries[18].GreatOrLess",
                                                               "edl_metric.entries[18].Flag",
                                                               "edl_metric.entries[18].OutOfSpec",
                                                               "edl_metric.entries[18].Description"],
                             "Touchdown Ellipse Minor Axis ": ["edl_metric.entries[19].type",
                                                               "edl_metric.entries[19].units",
                                                               "edl_metric.entries[19].POST_results",
                                                               "edl_metric.entries[19].GreatOrLess",
                                                               "edl_metric.entries[19].Flag",
                                                               "edl_metric.entries[19].OutOfSpec",
                                                               "edl_metric.entries[19].Description"],
                             "MLE Priming Time ": ["edl_metric.entries[20].type", "edl_metric.entries[20].units",
                                                   "edl_metric.entries[20].POST_results",
                                                   "edl_metric.entries[20].GreatOrLess",
                                                   "edl_metric.entries[20].Flag", "edl_metric.entries[20].OutOfSpec",
                                                   "edl_metric.entries[20].Description"],
                             "First Accordion Flown ": ["edl_metric.entries[21].type", "edl_metric.entries[21].units",
                                                        "edl_metric.entries[21].POST_results",
                                                        "edl_metric.entries[21].GreatOrLess",
                                                        "edl_metric.entries[21].Flag",
                                                        "edl_metric.entries[21].OutOfSpec",
                                                        "edl_metric.entries[21].Description"],
                             "Mortar Fire Dynamic Pressure ": ["edl_metric.entries[22].type",
                                                               "edl_metric.entries[22].units",
                                                               "edl_metric.entries[22].POST_results",
                                                               "edl_metric.entries[22].GreatOrLess",
                                                               "edl_metric.entries[22].Flag",
                                                               "edl_metric.entries[22].OutOfSpec",
                                                               "edl_metric.entries[22].Description"],
                             "Parachute Inflation Dynamic Pressure ": ["edl_metric.entries[23].type",
                                                                       "edl_metric.entries[23].units",
                                                                       "edl_metric.entries[23].POST_results",
                                                                       "edl_metric.entries[23].GreatOrLess",
                                                                       "edl_metric.entries[23].Flag",
                                                                       "edl_metric.entries[23].OutOfSpec",
                                                                       "edl_metric.entries[23].Description"],
                             "Peak Parachute Inflation Load (CBE) ": ["edl_metric.entries[24].type",
                                                                      "edl_metric.entries[24].units",
                                                                      "edl_metric.entries[24].POST_results",
                                                                      "edl_metric.entries[24].GreatOrLess",
                                                                      "edl_metric.entries[24].Flag",
                                                                      "edl_metric.entries[24].OutOfSpec",
                                                                      "edl_metric.entries[24].Description"]}
    return edlmetricssheet_names[extracted_data]


process_function = {}
process_function["parameter"] = process_parameter
process_function["edl_mission"] = not_processed
process_function["name"] = not_processed
process_function["edl_mat_file"] = not_processed
process_function["edl_mat_param"] = not_processed
process_function["extract_scorecard_filename"] = not_processed
process_function["scorecard_edlmetricsheet_results"] = not_processed
process_function["edl_metric_calculate"] = process_edl_scorecard_calculate
process_function["edl_metric_names"] = not_processed
