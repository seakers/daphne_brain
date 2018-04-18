import dateparser
import datetime

def not_processed(extracted_data, options, context):
    return extracted_data


def process_mission(extracted_data, options, context):
    return extracted_data[1:]


def process_date(extracted_data, options, context):
    date_parsing_settings = {}
    if options == "begin":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 1, 1)}
    elif options == "end":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 12, 31)}
    return dateparser.parse(extracted_data, settings=date_parsing_settings)


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