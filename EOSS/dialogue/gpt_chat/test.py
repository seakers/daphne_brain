"""EXAMPLE QUERIES:
Example 1: "Which missions can measure Glacier Cover?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%glacier cover%'
ORDER BY m.launch_date;

Example 2: "Which missions from NASA can measure Precipitation between 2010 and 2020?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
WHERE LOWER(me.name) LIKE '%precipitation%'
AND LOWER(a.name) LIKE '%nasa%'
AND m.launch_date < '2020-01-01'
AND m.eol_date > '2010-01-01'
ORDER BY m.launch_date;

Example 3: "Which missions do we currently use to measure Soil Moisture?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%soil moisture%'
AND m.launch_date < CURRENT_DATE
AND m.eol_date > CURRENT_DATE
ORDER BY m.launch_date;

Example 4: "Which instruments can measure Visibility?"
SELECT DISTINCT i.name 
FROM ceos_instruments i
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%visibility%'
ORDER BY i.name;

Example 5: "Which instruments from INTA can measure Visibility?"
SELECT DISTINCT i.name 
FROM ceos_instruments i
JOIN ceos_instruments_in_mission im ON i.id = im.instrument_id
JOIN ceos_missions m ON im.mission_id = m.id
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%visibility%'
AND LOWER(a.name) LIKE '%inta%'
ORDER BY i.name;

Example 6: "Which missions have flown Radar?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
LEFT JOIN ceos_type_of_instrument toi ON i.id = toi.instrument_id
LEFT JOIN ceos_instrument_types it ON toi.instrument_type_id = it.id
WHERE LOWER(i.technology) LIKE '%radar%' OR LOWER(it.name) LIKE '%radar%'
ORDER BY m.launch_date;

Example 7: "Which missions are currently flying Spectrometers?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
LEFT JOIN ceos_type_of_instrument toi ON i.id = toi.instrument_id
LEFT JOIN ceos_instrument_types it ON toi.instrument_type_id = it.id
WHERE (LOWER(i.technology) LIKE '%spectrometer%' OR LOWER(it.name) LIKE '%spectrometer%')
AND m.launch_date < CURRENT_DATE
AND m.eol_date > CURRENT_DATE
ORDER BY m.launch_date;

Example 8: "Which orbit is the most common for Lidar?"
SELECT orbit
FROM ceos_techtype_most_common_orbits
WHERE LOWER(techtype) LIKE '%lidar%'
LIMIT 1;

Example 9: "Which orbit is the most common for Ocean Color measurements?"
SELECT orbit
FROM ceos_measurement_most_common_orbits
WHERE LOWER(measurement) LIKE '%ocean color%'
LIMIT 1;

Example 10: "When was mission Sentinel-1 launched?"
SELECT launch_date
FROM ceos_missions
WHERE LOWER(name) LIKE '%sentinel-1%'
LIMIT 1;

Example 11: "Which missions have been launched by ESA?"
SELECT DISTINCT m.name
FROM ceos_missions m
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
WHERE LOWER(a.name) LIKE '%esa%'
ORDER BY m.launch_date;

Example 12: "Show me a timeline of missions which measure Aerosols"
SELECT m.name, m.status, m.launch_date, m.eol_date
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%aerosols%'
ORDER BY m.launch_date;

Example 13: "What measurements can ASCAT make?"
SELECT DISTINCT me.name
FROM ceos_measurements me
JOIN ceos_measurements_of_instrument mi ON me.id = mi.measurement_id
JOIN ceos_instruments i ON mi.instrument_id = i.id
WHERE LOWER(i.name) LIKE '%ascat%'
ORDER BY me.name;

Example 14: "Show me all agencies that operate missions measuring Precipitation"
SELECT DISTINCT a.name
FROM ceos_agencies a
JOIN ceos_operators op ON a.id = op.agency_id
JOIN ceos_missions m ON op.mission_id = m.id
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%precipitation%'
ORDER BY a.name;

Example 15: "Which instruments are on the Terra mission?"
SELECT DISTINCT i.name
FROM ceos_instruments i
JOIN ceos_instruments_in_mission im ON i.id = im.instrument_id
JOIN ceos_missions m ON im.mission_id = m.id
WHERE LOWER(m.name) LIKE '%terra%'
ORDER BY i.name;

Return ONLY the SQL query with no explanations.
SQL:"""



'''
QUERY EXAMPLES:
For "Which missions can measure Ocean Color?":
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%ocean color%'
ORDER BY m.launch_date;

For "Which instruments from INTA can measure Visibility?":
SELECT DISTINCT i.name 
FROM ceos_instruments i
JOIN ceos_instruments_in_mission im ON i.id = im.instrument_id
JOIN ceos_missions m ON im.mission_id = m.id
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%visibility%'
AND LOWER(a.name) LIKE '%inta%'
ORDER BY i.name;

For "Which orbit is the most common for Lidar?":
SELECT orbit
FROM ceos_techtype_most_common_orbits
WHERE LOWER(techtype) LIKE '%lidar%'
LIMIT 1;

For "What measurements can ASCAT make?":
SELECT DISTINCT me.name
FROM ceos_measurements me
JOIN ceos_measurements_of_instrument mi ON me.id = mi.measurement_id
JOIN ceos_instruments i ON mi.instrument_id = i.id
WHERE LOWER(i.name) LIKE '%ascat%'
ORDER BY me.name;

'''



'''
SELECT i.name
FROM ceos_instruments i
JOIN ceos_measurements_of_instrument moi ON i.id = moi.instrument_id
JOIN ceos_measurements m ON moi.measurement_id = m.id
JOIN ceos_designers d ON i.id = d.instrument_id
JOIN ceos_agencies a ON d.agency_id = a.id
WHERE m.name ILIKE 'volcanic ash'
AND a.name ILIKE 'inta'
GROUP BY i.name                                 
ORDER BY (
  SELECT MIN(mission.launch_date)
  FROM ceos_missions mission
  JOIN ceos_instruments_in_mission iim ON mission.id = iim.mission_id
  WHERE iim.instrument_id = i.id
);^C
daphneeo=# SELECT       
    ceos_instrumenCOUNT(*) FROM ceos_missions;
                                              
    ceos_instrumeni.namee
'''