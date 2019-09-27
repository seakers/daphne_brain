import pandas

assignation_problems = ['SMAP', 'SMAP_JPL1', 'SMAP_JPL2', 'ClimateCentric']
partition_problems = ['Decadal2017Aerosols']

CC_ORBIT_DATASET = [
    {"alias": "1000", "name": "LEO-600-polar-NA", "type": "Inclined, non-sun-synchronous", "altitude": 600, "LST": ""},
    {"alias": "2000", "name": "SSO-600-SSO-AM", "type": "Sun-synchronous", "altitude": 600, "LST": "AM"},
    {"alias": "3000", "name": "SSO-600-SSO-DD", "type": "Sun-synchronous", "altitude": 600, "LST": "DD"},
    {"alias": "4000", "name": "SSO-800-SSO-DD", "type": "Sun-synchronous", "altitude": 800, "LST": "DD"},
    {"alias": "5000", "name": "SSO-800-SSO-PM", "type": "Sun-synchronous", "altitude": 800, "LST": "PM"}]


CC_INSTRUMENT_DATASET = [
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


cc_capabilities_sheet = pandas.read_excel('../VASSAR_resources/problems/ClimateCentric/xls/Instrument Capability Definition.xls',
                                       sheet_name='CHARACTERISTICS')

cc_instrument_sheet = lambda vassar_instrument: pandas.read_excel('../VASSAR_resources/problems/ClimateCentric/xls/Instrument Capability Definition.xls',
                                        sheet_name=vassar_instrument, header=None)

cc_requirements_sheet = pandas.read_excel('../VASSAR_resources/problems/ClimateCentric/xls/Requirement Rules.xls',
                                           sheet_name='Attributes')

cc_instruments_sheet = pandas.read_excel('../VASSAR_resources/problems/ClimateCentric/xls/AttributeSet.xls', sheet_name='Instrument')
cc_measurements_sheet = pandas.read_excel('../VASSAR_resources/problems/ClimateCentric/xls/AttributeSet.xls', sheet_name='Measurement')
cc_param_names = []
for row in cc_measurements_sheet.itertuples(index=True, name='Measurement'):
    if row[2] == 'Parameter':
        for i in range(6, len(row)):
            cc_param_names.append(row[i])

cc_orbits_info = [
    "<b>Orbit name: Orbit information</b>",
    "LEO-600-polar-NA: Low Earth, Medium Altitude (600 km), Polar",
    "SSO-600-SSO-AM: Low Earth, Sun-synchronous, Medium Altitude (600 km), Morning",
    "SSO-600-SSO-DD: Low Earth, Sun-synchronous, Medium Altitude (600 km), Dawn-Dusk",
    "SSO-800-SSO-DD: Low Earth, Sun-synchronous, High Altitude (800 km), Dawn-Dusk",
    "SSO-800-SSO-PM: Low Earth, Sun-synchronous, High Altitude (800 km), Afternoon"
]


cc_instruments_info = [
    "<b>Instrument name: Instrument type, Instrument technology</b>",
    "ACE_ORCA: Ocean colour instruments, Medium-resolution spectro-radiometer",
    "ACE_POL: Multiple direction/polarisation radiometers, Multi-channel/direction/polarisation radiometer",
    "ACE_LID: Lidars, Atmospheric lidar",
    "CLAR_ERB: Hyperspectral imagers, Multi-purpose imaging Vis/IR radiometer",
    "ACE_CPR: Cloud profile and rain radars, Cloud and precipitation radar",
    "DESD_SAR: Imaging microwave radars, Imaging radar (SAR)",
    "DESD_LID: Lidars, Lidar altimeter",
    "GACM_VIS: Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "GACM_SWIR: Atmospheric chemistry, High-resolution nadir-scanning IR spectrometer",
    "HYSP_TIR: Imaging multi-spectral radiometers (vis/IR), Medium-resolution IR spectrometer",
    "POSTEPS_IRS: Atmospheric temperature and humidity sounders, Medium-resolution IR spectrometer",
    "CNES_KaRIN: Radar altimeters, Radar altimeter"
]

cc_stakeholder_list = ["Atmospheric", "Oceanic", "Terrestrial"]


SMAP_ORBIT_DATASET = [
    {"alias": "1000", "name": "LEO-600-polar-NA", "type": "Inclined, non-sun-synchronous", "altitude": 600, "LST": ""},
    {"alias": "2000", "name": "SSO-600-SSO-AM", "type": "Sun-synchronous", "altitude": 600, "LST": "AM"},
    {"alias": "3000", "name": "SSO-600-SSO-DD", "type": "Sun-synchronous", "altitude": 600, "LST": "DD"},
    {"alias": "4000", "name": "SSO-800-SSO-AM", "type": "Sun-synchronous", "altitude": 800, "LST": "AM"},
    {"alias": "5000", "name": "SSO-800-SSO-DD", "type": "Sun-synchronous", "altitude": 800, "LST": "DD"}]


SMAP_INSTRUMENT_DATASET = [
    {"alias": "A", "name": "BIOMASS", "type": "Imaging microwave radars", "technology": "Imaging radar (SAR)",
     "geometry": "Conical scanning", "wavebands": ["P-band"]},
    {"alias": "B", "name": "SMAP_RAD", "type": "Imaging microwave radars", "technology": "Imaging radar (SAR)",
     "geometry": "Conical scanning", "wavebands": ["L-band"]},
    {"alias": "C", "name": "SMAP_MWR", "type": "Imaging multi-spectral radiometers (passive microwave)",
     "technology": "Multi-purpose imaging MW radiometer", "geometry": "Conical scanning", "wavebands": ["L-band"]},
    {"alias": "D", "name": "CMIS", "type": "Imaging multi-spectral radiometers (passive microwave)",
     "technology": "Multi-purpose imaging MW radiometer", "geometry": "Conical scanning",
     "wavebands": ["C-band", "X-band", "K-band", "Ka-band", "W-band"]},
    {"alias": "E", "name": "VIIRS", "type": "High-resolution nadir-scanning IR spectrometer",
     "technology": "Atmospheric temperature and humidity sounders", "geometry": "Nadir-viewing",
     "wavebands": ["VIS", "NIR", "SWIR", "MWIR", "TIR"]},
]


smap_capabilities_sheet = pandas.read_excel('../VASSAR_resources/problems/SMAP/xls/Instrument Capability Definition.xls',
                                            sheet_name='CHARACTERISTICS')

smap_instrument_sheet = lambda vassar_instrument: pandas.read_excel('../VASSAR_resources/problems/SMAP/xls/Instrument Capability Definition.xls',
                                                                    sheet_name=vassar_instrument, header=None)

smap_requirements_sheet = pandas.read_excel('../VASSAR_resources/problems/SMAP/xls/Requirement Rules.xls',
                                            sheet_name='Attributes')

smap_instruments_sheet = pandas.read_excel('../VASSAR_resources/problems/SMAP/xls/AttributeSet.xls', sheet_name='Instrument')
smap_measurements_sheet = pandas.read_excel('../VASSAR_resources/problems/SMAP/xls/AttributeSet.xls', sheet_name='Measurement')
smap_param_names = []
for row in smap_measurements_sheet.itertuples(index=True, name='Measurement'):
    if row[2] == 'Parameter':
        for i in range(6, len(row)):
            smap_param_names.append(row[i])


smap_orbits_info = [
    "<b>Orbit name: Orbit information</b>",
    "LEO-600-polar-NA: Low Earth, Medium Altitude (600 km), Polar",
    "SSO-600-SSO-AM: Low Earth, Sun-synchronous, Medium Altitude (600 km), Morning",
    "SSO-600-SSO-DD: Low Earth, Sun-synchronous, Medium Altitude (600 km), Dawn-Dusk",
    "SSO-800-SSO-AM: Low Earth, Sun-synchronous, High Altitude (800 km), Morning",
    "SSO-800-SSO-DD: Low Earth, Sun-synchronous, High Altitude (800 km), Dawn-Dusk"
]


smap_instruments_info = [
    "<b>Instrument name: Instrument type, Instrument technology, Band, Mass, Power</b>",
    "BIOMASS: Imaging microwave radars, Imaging radar (SAR), P-band, 500kg, 1672W",
    "SMAP_RAD: Imaging microwave radars, Imaging radar (SAR), L-band, 45.2kg, 1672W",
    "SMAP_MWR: Imaging multi-spectral radiometers (passive microwave), Multi-purpose imaging MW radiometer, L-band, 10.4kg, 45.2W",
    "CMIS: Imaging multi-spectral radiometers (passive microwave), Multi-purpose imaging MW radiometer, C-band/X-band/K-band/Ka-band/W-band, 257kg, 340W",
    "VIIRS: High-resolution nadir-scanning IR spectrometer, Atmospheric temperature and humidity sounders, VIS/NIR/SWIR/MWIR/TIR, 199kg, 134W",
]

smap_stakeholder_list = ["Weather", "Climate", "Land and ecosystems", "Water", "Human health"]


def get_orbit_dataset(problem):
    if problem == "ClimateCentric":
        return CC_ORBIT_DATASET
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return SMAP_ORBIT_DATASET
    if problem == "Decadal2017Aerosols":
        return SMAP_ORBIT_DATASET


def get_instrument_dataset(problem):
    if problem == "ClimateCentric":
        return CC_INSTRUMENT_DATASET
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return SMAP_INSTRUMENT_DATASET
    if problem == "Decadal2017Aerosols":
        return SMAP_INSTRUMENT_DATASET


def get_capabilities_sheet(problem):
    if problem == "ClimateCentric":
        return cc_capabilities_sheet
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_capabilities_sheet


def get_instrument_sheet(problem, instrument):
    if problem == "ClimateCentric":
        return cc_instrument_sheet(instrument)
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_instrument_sheet(instrument)


def get_instruments_sheet(problem):
    if problem == "ClimateCentric":
        return cc_instruments_sheet
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_instruments_sheet


def get_requirements_sheet(problem):
    if problem == "ClimateCentric":
        return cc_requirements_sheet
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_requirements_sheet


def get_param_names(problem):
    if problem == "ClimateCentric":
        return cc_param_names
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_param_names


def get_orbits_info(problem):
    if problem == "ClimateCentric":
        return cc_orbits_info
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_orbits_info
    if problem == "Decadal2017Aerosols":
        return smap_orbits_info


def get_instruments_info(problem):
    if problem == "ClimateCentric":
        return cc_instruments_info
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_instruments_info
    if problem == "Decadal2017Aerosols":
        return smap_instruments_info


def get_stakeholders_list(problem):
    if problem == "ClimateCentric":
        return cc_stakeholder_list
    if problem == "SMAP" or problem == "SMAP_JPL1" or problem == "SMAP_JPL2":
        return smap_stakeholder_list
