from AT.simulator_thread.scenario_tools import add_variable
from AT.simulator_thread.scenario_tools import add_to_anomaly
from AT.simulator_thread.scenario_tools import add_event

# USER SECTION

# Simulator variables
add_variable('Cabin pressure', 0.5, 0.9, 1, 1.1, 1.5)
add_variable('N2 concentration', 60, 70, 79, 85, 90)
add_variable('Dummy variable', 150, 180, 200, 220, 250)

# Simulator anomaly settings
add_to_anomaly('n2_tank_burst', 'N2 concentration', 0.1, -0.1, 1)
add_to_anomaly('n2_tank_burst', 'Cabin pressure', 0.02, -0.02, 0.5)
# add_to_anomaly('custom', 'n2_concentration', -0.05, 0.1, -2)

# Simulator event timeline
add_event('n2_tank_burst', '00:00:01', '00:00:30')
# add_event('custom', '00:00:08', '00:0:30')
