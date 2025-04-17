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