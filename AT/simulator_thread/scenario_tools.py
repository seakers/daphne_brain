import os

# Import the simulation settings
from AT.simulator_thread.simulation_parameters import variables
from AT.simulator_thread.simulation_parameters import anomalies
from AT.simulator_thread.simulation_parameters import timeline


def add_variable(name, lct, lwt, nom, hwt, hct):
    if name in variables.keys():
        print('Warning: This variable was added more than once.'
              'The latest settings will be applied.')

    variables[name] = {'low_critic_threshold': lct, 'low_warning_threshold': lwt, 'nominal': nom,
                       'high_warning_threshold': hwt, 'high_critic_threshold': hct}
    return


def add_to_anomaly(name, var, pace_in, pace_out, max_increment):
    if name in anomalies.keys():
        if var in anomalies[name].keys():
            print('Warning: This anomaly effect was added more than once.'
                  'The latest settings will be applied.')

    if name not in anomalies.keys():
        anomalies[name] = {}

    anomalies[name][var] = {'pace_in': pace_in, 'pace_out': pace_out, 'max_increment': max_increment}

    return


def hhmmss_to_sec(time_str):
    h, m, s = time_str.split(':')
    seconds = int(h) * 3600 + int(m) * 60 + int(s)

    return seconds


def add_event(name, start_string, duration_string):
    start = hhmmss_to_sec(start_string)
    duration = hhmmss_to_sec(duration_string)

    event = {'name': name, 'start': start, 'duration': duration}
    timeline.append(event)

    return


def set_simulation():
    filename = os.path.join(os.getcwd(), 'AT', 'simulator_thread', 'scenario_setting_user_script.py')
    exec(open(filename).read())

    return


