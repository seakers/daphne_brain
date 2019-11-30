import pandas as pd
from asgiref.sync import async_to_sync
import os
from queue import Queue
import time


def load_data():
    # Load the telemetry feed values
    filename = os.path.join(os.getcwd(), 'AT', 'databases', 'telemetry_feed_values.csv')
    values = pd.read_csv(filename)

    # Load the variables thresholds and nominal values
    filename = os.path.join(os.getcwd(), 'AT', 'databases', 'telemetry_feed_info.csv')
    info = pd.read_csv(filename)
    info = info.set_index('parameter')

    # Build the telemetry feed dictionary
    tf = {'values': values, 'info': info}
    return tf


def simulate(sim_to_hub, hub_to_sim):
    # Load the complete telemetry feed csv files and set the window size
    tf = load_data()
    window_span = 60

    # Initialize the telemetry feed simulation counters and window
    k = 1
    lower_row = 0
    upper_row = window_span - 1
    counter_limit = len(tf['values'].index) - window_span
    tf_window = {'values': tf['values'].iloc[lower_row:(upper_row + 1)], 'info': tf['info']}

    # Simulate the real time feeding by "scrolling the window down"
    while k < counter_limit:
        # Check the communication queue messages
        if not hub_to_sim.empty():
            signal = hub_to_sim.get()
            if signal == 'stop':
                break

        # Send a new window to the thread handler thread
        sim_to_hub.put(tf_window)

        # Update the counters
        k += 1
        lower_row += 1
        upper_row += 1

        # Update the telemetry feed window
        new_info = tf['values'].iloc[upper_row]
        tf_window['values'] = tf_window['values'].drop(index=lower_row - 1)
        tf_window['values'].loc[upper_row] = new_info

        # Wait
        time.sleep(1)

    print('Simulator thread stopped.')
    return None