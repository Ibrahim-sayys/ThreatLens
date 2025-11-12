from dateutil import parser

def normalize_date(date_string):
    """
    Converts any date string to DD/MM/YYYY format.
    Removes time if present.
    Returns empty string if unable to parse.
    """
    if not date_string or not isinstance(date_string, str):
        return ""
    try:
        # Parse date (ignore time)
        dt = parser.parse(date_string, fuzzy=True, dayfirst=False)
        return "{:02d}/{:02d}/{}".format(dt.day, dt.month, dt.year)
    except Exception:
        return ""