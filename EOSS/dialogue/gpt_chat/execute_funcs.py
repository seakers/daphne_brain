from sqlalchemy import and_, or_, func
from EOSS.dialogue.gpt_chat.db_client import Client
from EOSS.dialogue.gpt_chat.models import Mission, Instrument, Measurement, Agency, InstrumentType, TechTypeMostCommonOrbit, MeasurementMostCommonOrbit
from datetime import datetime
# from db_client import Client
# from models import Mission, Instrument, Measurement, Agency, InstrumentType, TechTypeMostCommonOrbit, MeasurementMostCommonOrbit

client = Client()
session = client.get_session()

def print_orbit(orbit):
    text_orbit = ""
    orbit_codes = {
        "GEO": "geostationary",
        "LEO": "low earth",
        "HEO": "highly elliptical",
        "SSO": "sun-synchronous",
        "Eq": "equatorial",
        "NearEq": "near equatorial",
        "MidLat": "mid latitude",
        "NearPo": "near polar",
        "Po": "polar",
        "DD": "dawn-dusk local solar time",
        "AM": "morning local solar time",
        "Noon": "noon local solar time",
        "PM": "afternoon local solar time",
        "VL": "very low altitude",
        "L": "low altitude",
        "M": "medium altitude",
        "H": "high altitude",
        "VH": "very high altitude",
        "NRC": "no repeat cycle",
        "SRC": "short repeat cycle",
        "LRC": "long repeat cycle"
    }
    if orbit is not None:
        orbit_parts = orbit.split('-')
        text_orbit = "a "
        first = True
        for orbit_part in orbit_parts:
            if first:
                first = False
            else:
                text_orbit += ', '
            text_orbit += orbit_codes[orbit_part]
        text_orbit += " orbit"
    else:
        text_orbit = "none"
    return text_orbit


def print_date(date):
    return date.strftime('%d %B %Y')

def query_missions_by_measurement(parameters):
    """
    Query missions that can take a certain measurement (Template 4000).
    
    Args:
        client: Database client with connection to the database
        parameters: Dictionary containing query parameters
    
    Returns:
        List of mission names matching the criteria
    """
    # Extract parameters
    measurement = parameters.get("measurement")
    year1 = parameters.get("year1")
    year2 = parameters.get("year2")
    space_agency = parameters.get("space_agency")
    print("the qyery paramters are", measurement, year1, year2, space_agency)
    
    if not measurement or measurement == "Unknown":
        return []
        
    query = session.query(Mission.name).distinct()\
        .join(Instrument, Mission.instruments)\
        .join(Instrument.measurements)\
        .filter(func.lower(Measurement.name).like(f"%{measurement.lower()}%"))
    print("initial query", query)
    # Add optional filters
    if year1 and year1 != "Unknown":
        query = query.filter(Mission.eol_date > year1)
    
    if year2 and year2 != "Unknown":
        query = query.filter(Mission.launch_date < year2)
    
    if space_agency and space_agency != "Unknown":
        query = query.join(Mission.agencies)\
                     .filter(func.lower(Agency.name).like(f"%{space_agency.lower()}%"))
    
    # Add ordering
    query = query.order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = [row[0] for row in query.all()]
        return missions
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []
    
def query_current_missions_by_measurement(parameters):
    """
    Query currently active missions that can take a certain measurement.
    
    Args:
        parameters: Dictionary containing query parameters:
            - measurement: Required, the measurement to search for
            - space_agency: Optional, space agency to filter by
    
    Returns:
        List of currently active mission names matching the criteria
    """
    # Extract parameters
    measurement = parameters.get("measurement")
    space_agency = parameters.get("space_agency")
    
    if not measurement or measurement == "Unknown":
        return []
    
    # Initialize client
    from db_client import Client
    client = Client()
    session = client.get_session()
    
    # Get current date for filtering active missions
    now = datetime.now()
    
    # Build query using SQLAlchemy
    query = session.query(Mission.name).distinct()\
        .join(Instrument, Mission.instruments)\
        .join(Instrument.measurements)\
        .filter(func.lower(Measurement.name).like(f"%{measurement.lower()}%"))\
        .filter(Mission.launch_date < now)\
        .filter(Mission.eol_date > now)
    
    print("initial query", query)
    
    # Add optional filter for space agency
    if space_agency and space_agency != "Unknown":
        query = query.join(Mission.agencies)\
                     .filter(func.lower(Agency.name).like(f"%{space_agency.lower()}%"))
    
    # Add ordering
    query = query.order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = [row[0] for row in query.all()]
        return missions
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def query_instruments_by_measurement(parameters):
    """
    Query instruments that can take a certain measurement.
    
    Args:
        parameters: Dictionary containing query parameters:
            - measurement: Required, the measurement to search for
            - year1: Optional, start year for filtering
            - year2: Optional, end year for filtering
            - space_agency: Optional, space agency to filter by
    
    Returns:
        List of instrument names matching the criteria
    """
    # Extract parameters
    measurement = parameters.get("measurement")
    year1 = parameters.get("year1")
    year2 = parameters.get("year2")
    space_agency = parameters.get("space_agency")
    
    if not measurement or measurement == "Unknown":
        return []
    
    # Build query using SQLAlchemy
    query = session.query(Instrument.name)\
        .join(Mission, Instrument.missions)\
        .group_by(Instrument.name)\
        .filter(Instrument.measurements.any(
            func.lower(Measurement.name).like(f"%{measurement.lower()}%")
        ))
    
    print("initial query", query.all())
    
    # Add optional filters
    if year1 and year1 != "Unknown":
        query = query.having(func.max(Mission.eol_date) > year1)
    print("initial query1", query.all())
    
    if year2 and year2 != "Unknown":
        query = query.having(func.min(Mission.launch_date) < year2)
    print("initial query2", query.all())
    
    if space_agency and space_agency != "Unknown":
        query = query.filter(Mission.agencies.any(
            func.lower(Agency.name).like(f"%{space_agency.lower()}%")
        ))
    print("initial query3", query.all())
    
    # Add ordering
    query = query.order_by(func.min(Mission.launch_date))
    print("initial query4", query.all())
    
    # Execute query
    try:
        instruments = [row[0] for row in query.all()]
        return instruments
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []
    
def query_missions_by_technology(parameters):
    """
    Query missions that have flown a certain technology.
    
    Args:
        parameters: Dictionary containing query parameters:
            - technology: Required, the technology to search for
            - year1: Optional, start year for filtering
            - year2: Optional, end year for filtering
            - space_agency: Optional, space agency to filter by
    
    Returns:
        List of mission names matching the criteria
    """
    # Extract parameters
    technology = parameters.get("technology")
    year1 = parameters.get("year1")
    year2 = parameters.get("year2")
    space_agency = parameters.get("space_agency")
    
    if not technology or technology == "Unknown":
        return []

    
    # Build query using SQLAlchemy - missions with specified technology
    query = session.query(Mission.name).distinct()\
        .join(Instrument, Mission.instruments)\
        .filter(
            or_(
                func.lower(Instrument.technology).like(f"%{technology.lower()}%"),
                Instrument.types.any(
                    func.lower(InstrumentType.name).like(f"%{technology.lower()}%")
                )
            )
        )
    
    print("initial query", query)
    
    # Add optional filters
    if year1 and year1 != "Unknown":
        query = query.filter(Mission.eol_date > year1)
    
    if year2 and year2 != "Unknown":
        query = query.filter(Mission.launch_date < year2)
    
    if space_agency and space_agency != "Unknown":
        query = query.filter(Mission.agencies.any(
            func.lower(Agency.name).like(f"%{space_agency.lower()}%")
        ))
    
    # Add ordering
    query = query.order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = [row[0] for row in query.all()]
        return missions
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def query_current_missions_by_technology(parameters):
    """
    Query currently active missions that have flown a certain technology.
    
    Args:
        parameters: Dictionary containing query parameters:
            - technology: Required, the technology to search for
            - space_agency: Optional, space agency to filter by
    
    Returns:
        List of currently active mission names matching the criteria
    """
    # Extract parameters
    technology = parameters.get("technology")
    space_agency = parameters.get("space_agency")
    
    if not technology or technology == "Unknown":
        return []
 
    # Get current date for filtering active missions
    now = datetime.now()
    
    # Build query using SQLAlchemy - current missions with specified technology
    query = session.query(Mission.name).distinct()\
        .join(Instrument, Mission.instruments)\
        .filter(
            or_(
                func.lower(Instrument.technology).like(f"%{technology.lower()}%"),
                Instrument.types.any(
                    func.lower(InstrumentType.name).like(f"%{technology.lower()}%")
                )
            )
        )\
        .filter(Mission.launch_date < now)\
        .filter(Mission.eol_date > now)
    
    print("initial query", query)
    
    # Add optional filter for space agency
    if space_agency and space_agency != "Unknown":
        query = query.filter(Mission.agencies.any(
            func.lower(Agency.name).like(f"%{space_agency.lower()}%")
        ))
    
    # Add ordering
    query = query.order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = [row[0] for row in query.all()]
        return missions
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def query_most_common_orbit_for_technology(parameters):
    """
    Query the most common orbit for a specific technology.
    
    Args:
        parameters: Dictionary containing query parameters:
            - technology: Required, the technology to search for
    
    Returns:
        Dictionary with orbit information or None if not found
    """
    # Extract parameters
    technology = parameters.get("technology")
    
    if not technology or technology == "Unknown":
        return None

        
    # Build query using SQLAlchemy
    query = session.query(TechTypeMostCommonOrbit)\
        .filter(func.lower(TechTypeMostCommonOrbit.techtype).like(f"%{technology.lower()}%"))
    
    # Execute query
    try:
        result = query.first()
        if result:
            # Format the orbit using the response helper
            orbit = print_orbit(result.orbit)
            return {"orbit": orbit, "technology": technology}
        else:
            return None
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return None

def query_most_common_orbit_for_measurement(parameters):
    """
    Query the most common orbit for a specific measurement.
    
    Args:
        parameters: Dictionary containing query parameters:
            - measurement: Required, the measurement to search for
    
    Returns:
        Dictionary with orbit information or None if not found
    """
    # Extract parameters
    measurement = parameters.get("measurement")
    
    if not measurement or measurement == "Unknown":
        return None
    
    # Import response helpers for orbit formatting    
    # Build query using SQLAlchemy
    query = session.query(MeasurementMostCommonOrbit)\
        .filter(func.lower(MeasurementMostCommonOrbit.measurement).like(f"%{measurement.lower()}%"))
    
    # Execute query
    try:
        result = query.first()
        if result:
            # Format the orbit using the response helper
            orbit = print_orbit(result.orbit)
            return {"orbit": orbit, "measurement": measurement}
        else:
            return None
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return None
    
def query_mission_launch_date(parameters):
    """
    Query the launch date of a specific mission.
    
    Args:
        parameters: Dictionary containing query parameters:
            - mission: Required, the mission name to search for
    
    Returns:
        Dictionary with mission and launch date information or None if not found
    """
    # Extract parameters
    mission = parameters.get("mission")
    
    if not mission or mission == "Unknown":
        return None
    
    # Build query using SQLAlchemy
    query = session.query(Mission)\
        .filter(func.lower(Mission.name).like(f"%{mission.lower()}%"))
    
    # Execute query
    try:
        result = query.first()
        if result:
            # Format the launch date using the response helper
            launch_date = print_date(result.launch_date)
            return {"mission": mission, "launch_date": launch_date}
        else:
            return None
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return None

def query_missions_by_agency(parameters):
    """
    Query missions built by a specific space agency.
    
    Args:
        parameters: Dictionary containing query parameters:
            - space_agency: Required, the space agency name to search for
    
    Returns:
        List of mission names built by the specified space agency
    """
    # Extract parameters
    space_agency = parameters.get("space_agency")
    
    if not space_agency or space_agency == "Unknown":
        return []
    
    # Build query using SQLAlchemy
    query = session.query(Mission.name)\
        .filter(Mission.agencies.any(
            func.lower(Agency.name).like(f"%{space_agency.lower()}%")
        ))\
        .order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = [row[0] for row in query.all()]
        return missions
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []
    
def query_mission_timeline_by_measurement(parameters):
    """
    Query timeline data for missions that take a certain measurement.
    
    Args:
        parameters: Dictionary containing query parameters:
            - measurement: Required, the measurement to search for
            - space_agency: Optional, space agency to filter by
    
    Returns:
        List of dictionaries with mission timeline information
    """
    # Extract parameters
    measurement = parameters.get("measurement")
    space_agency = parameters.get("space_agency")
    
    if not measurement or measurement == "Unknown":
        return []
    
    # Build query using SQLAlchemy
    query = session.query(Mission)\
        .join(Instrument, Mission.instruments)\
        .filter(Instrument.measurements.any(
            func.lower(Measurement.name).like(f"%{measurement.lower()}%")
        ))
    
    # Add optional filter for space agency
    if space_agency and space_agency != "Unknown":
        query = query.filter(Mission.agencies.any(
            func.lower(Agency.name).like(f"%{space_agency.lower()}%")
        ))
    
    # Add ordering
    query = query.order_by(Mission.launch_date)
    
    # Execute query
    try:
        missions = query.all()
        
        # Format results
        timeline_data = []
        for mission in missions:
            timeline_data.append({
                "name": mission.name,
                "status": mission.status,
                "launch_date": mission.launch_date,
                "end_date": mission.eol_date
            })
        
        return timeline_data
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []