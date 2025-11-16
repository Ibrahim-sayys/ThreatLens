from dateutil import parser
from datetime import datetime, timedelta
import re

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


def parse_relative_date(date_string):
    """
    Converts relative date strings like "Published 1 week ago", "2 days ago",
    "3 months ago" to actual date in DD/MM/YYYY format.

    Supports:
    - seconds/minutes/hours ago
    - days/weeks ago
    - months/years ago
    - yesterday, today

    Args:
        date_string: String containing relative date like "1 week ago"

    Returns:
        Date string in DD/MM/YYYY format, or empty string if unable to parse

    Examples:
        "Published 1 week ago" -> "07/11/2025" (if today is 14/11/2025)
        "2 days ago" -> "12/11/2025"
        "3 months ago" -> "14/08/2025"
    """
    if not date_string or not isinstance(date_string, str):
        return ""

    # Convert to lowercase for easier matching
    text = date_string.lower().strip()

    # Get current date
    now = datetime.now()

    # Handle "yesterday"
    if 'yesterday' in text:
        target_date = now - timedelta(days=1)
        return "{:02d}/{:02d}/{}".format(target_date.day, target_date.month, target_date.year)

    # Handle "today"
    if 'today' in text or 'just now' in text:
        return "{:02d}/{:02d}/{}".format(now.day, now.month, now.year)

    # Pattern to match relative dates: "X unit(s) ago"
    # Examples: "1 week ago", "2 days ago", "3 months ago"
    pattern = r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago'
    match = re.search(pattern, text)

    if match:
        number = int(match.group(1))
        unit = match.group(2)

        # Calculate the date based on the unit
        if unit == 'second':
            target_date = now - timedelta(seconds=number)
        elif unit == 'minute':
            target_date = now - timedelta(minutes=number)
        elif unit == 'hour':
            target_date = now - timedelta(hours=number)
        elif unit == 'day':
            target_date = now - timedelta(days=number)
        elif unit == 'week':
            target_date = now - timedelta(weeks=number)
        elif unit == 'month':
            # Approximate: 1 month = 30 days
            target_date = now - timedelta(days=number * 30)
        elif unit == 'year':
            # Approximate: 1 year = 365 days
            target_date = now - timedelta(days=number * 365)
        else:
            return ""

        return "{:02d}/{:02d}/{}".format(target_date.day, target_date.month, target_date.year)

    # If no relative date pattern found, return empty string
    return ""


def smart_date_parse(date_string):
    """
    Smart date parser that tries multiple methods:
    1. First tries to parse relative dates ("1 week ago", etc.)
    2. Then tries standard date parsing
    3. Returns empty string if all methods fail

    This is the recommended function to use for parsing any date string.

    Args:
        date_string: Any date string (relative or absolute)

    Returns:
        Date string in DD/MM/YYYY format

    Examples:
        "Published 1 week ago" -> "07/11/2025"
        "2025-01-15" -> "15/01/2025"
        "Jan 15, 2025" -> "15/01/2025"
    """
    if not date_string or not isinstance(date_string, str):
        return ""

    # Try relative date parsing first
    relative_result = parse_relative_date(date_string)
    if relative_result:
        return relative_result

    # Fall back to standard date parsing
    return normalize_date(date_string)
