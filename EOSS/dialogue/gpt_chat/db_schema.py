DB_SCHEMA = """
-- SCHEMA DEFINITION FOR EARTH OBSERVATION DATABASE

-- Broad Measurement Categories
CREATE TABLE ceos_broad_measurement_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    description VARCHAR
);

-- Measurement Categories
CREATE TABLE ceos_measurement_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    description VARCHAR,
    broad_measurement_category_id INTEGER REFERENCES ceos_broad_measurement_categories(id)
);

-- Measurements
CREATE TABLE ceos_measurements (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    description VARCHAR,
    measurement_category_id INTEGER REFERENCES ceos_measurement_categories(id)
);

-- Agencies
CREATE TABLE ceos_agencies (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    country VARCHAR,
    website VARCHAR
);

-- Missions
CREATE TABLE ceos_missions (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    full_name VARCHAR,
    status VARCHAR,
    launch_date TIMESTAMP,
    eol_date TIMESTAMP,
    applications VARCHAR,
    orbit_type VARCHAR,
    orbit_period VARCHAR,
    orbit_sense VARCHAR,
    orbit_inclination VARCHAR,
    orbit_inclination_num FLOAT,
    orbit_inclination_class VARCHAR CHECK (orbit_inclination_class IN ('Equatorial', 'Near Equatorial', 'Mid Latitude', 'Near Polar', 'Polar')),
    orbit_altitude VARCHAR,
    orbit_altitude_num INTEGER,
    orbit_altitude_class VARCHAR CHECK (orbit_altitude_class IN ('VL', 'L', 'M', 'H', 'VH')),
    orbit_longitude VARCHAR,
    orbit_LST VARCHAR,
    orbit_LST_time TIME,
    orbit_LST_class VARCHAR CHECK (orbit_LST_class IN ('DD', 'AM', 'Noon', 'PM')),
    repeat_cycle VARCHAR,
    repeat_cycle_num FLOAT,
    repeat_cycle_class VARCHAR CHECK (repeat_cycle_class IN ('Long', 'Short'))
);

-- Instrument Types
CREATE TABLE ceos_instrument_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR
);

-- Geometry Types
CREATE TABLE ceos_geometry_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR
);

-- Wavebands
CREATE TABLE ceos_wavebands (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    wavelengths VARCHAR
);

-- Instruments
CREATE TABLE ceos_instruments (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    full_name VARCHAR,
    status VARCHAR,
    maturity VARCHAR,
    technology VARCHAR CHECK (technology IN (
        'Absorption-band MW radiometer/spectrometer', 'Atmospheric lidar', 'Broad-band radiometer',
        'Cloud and precipitation radar', 'Communications system', 'Data collection system',
        'Doppler lidar', 'Electric field sensor', 'GNSS radio-occultation receiver',
        'GNSS receiver', 'Gradiometer/accelerometer', 'High resolution optical imager',
        'High-resolution nadir-scanning IR spectrometer',
        'High-resolution nadir-scanning SW spectrometer', 'Imaging radar (SAR)',
        'Laser retroreflector', 'Lidar altimeter', 'Lightning imager',
        'Limb-scanning IR spectrometer', 'Limb-scanning MW spectrometer',
        'Limb-scanning SW spectrometer', 'Magnetometer', 'Medium-resolution IR spectrometer',
        'Medium-resolution spectro-radiometer', 'Multi-channel/direction/polarisation radiometer',
        'Multi-purpose imaging MW radiometer', 'Multi-purpose imaging Vis/IR radiometer',
        'Narrow-band channel IR radiometer', 'Non-scanning MW radiometer', 'Radar altimeter',
        'Radar scatterometer', 'Radio-positioning system', 'Satellite-to-satellite ranging system',
        'Solar irradiance monitor', 'Space environment monitor', 'Star tracker'
    )),
    sampling VARCHAR CHECK (sampling IN ('Imaging', 'Sounding', 'Other', 'TBD')),
    data_access VARCHAR CHECK (data_access IN ('Open Access', 'Constrained Access', 'Very Constrained Access', 'No Access')),
    data_format VARCHAR,
    measurements_and_applications VARCHAR,
    resolution_summary VARCHAR,
    best_resolution VARCHAR,
    swath_summary VARCHAR,
    max_swath VARCHAR,
    accuracy_summary VARCHAR,
    waveband_summary VARCHAR
);

-- Relationship Tables
CREATE TABLE ceos_operators (
    agency_id INTEGER REFERENCES ceos_agencies(id),
    mission_id INTEGER REFERENCES ceos_missions(id)
);

CREATE TABLE ceos_designers (
    agency_id INTEGER REFERENCES ceos_agencies(id),
    instrument_id INTEGER REFERENCES ceos_instruments(id)
);

CREATE TABLE ceos_type_of_instrument (
    instrument_id INTEGER REFERENCES ceos_instruments(id),
    instrument_type_id INTEGER REFERENCES ceos_instrument_types(id)
);

CREATE TABLE ceos_geometry_of_instrument (
    instrument_id INTEGER REFERENCES ceos_instruments(id),
    instrument_geometry_id INTEGER REFERENCES ceos_geometry_types(id)
);

CREATE TABLE ceos_instruments_in_mission (
    mission_id INTEGER REFERENCES ceos_missions(id),
    instrument_id INTEGER REFERENCES ceos_instruments(id)
);

CREATE TABLE ceos_measurements_of_instrument (
    instrument_id INTEGER REFERENCES ceos_instruments(id),
    measurement_id INTEGER REFERENCES ceos_measurements(id)
);

CREATE TABLE ceos_instrument_wavebands (
    instrument_id INTEGER REFERENCES ceos_instruments(id),
    waveband_id INTEGER REFERENCES ceos_wavebands(id)
);

-- Most Common Orbit Tables
CREATE TABLE ceos_techtype_most_common_orbits (
    id INTEGER PRIMARY KEY,
    techype VARCHAR,
    orbit VARCHAR
);

CREATE TABLE ceos_measurement_most_common_orbits (
    id INTEGER PRIMARY KEY,
    measurement VARCHAR,
    orbit VARCHAR
);

-- Common query patterns examples:
-- 1. Find missions measuring specific phenomena
-- SELECT m.name FROM ceos_missions m 
--   JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
--   JOIN ceos_instruments i ON im.instrument_id = i.id
--   JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
--   JOIN ceos_measurements me ON mi.measurement_id = me.id
--   WHERE LOWER(me.name) LIKE '%ocean color%'
--   ORDER BY m.launch_date;

-- 2. Find current active missions with specific technology
-- SELECT m.name FROM ceos_missions m 
--   JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
--   JOIN ceos_instruments i ON im.instrument_id = i.id
--   JOIN ceos_type_of_instrument ti ON i.id = ti.instrument_id
--   JOIN ceos_instrument_types it ON ti.instrument_type_id = it.id
--   WHERE (LOWER(i.technology) LIKE '%radar%' OR LOWER(it.name) LIKE '%radar%')
--   AND m.launch_date < NOW() AND m.eol_date > NOW()
--   ORDER BY m.launch_date;

-- 3. Find instruments for specific measurements across agencies
-- SELECT DISTINCT i.name FROM ceos_instruments i
--   JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
--   JOIN ceos_measurements m ON mi.measurement_id = m.id
--   JOIN ceos_designers d ON i.id = d.instrument_id
--   JOIN ceos_agencies a ON d.agency_id = a.id
--   WHERE LOWER(m.name) LIKE '%precipitation%'
--   AND LOWER(a.name) LIKE '%nasa%';

-- 4. Find most common orbit for a measurement
-- SELECT mo.orbit FROM ceos_measurement_most_common_orbits mo
--   WHERE LOWER(mo.measurement) LIKE '%temperature%';
"""