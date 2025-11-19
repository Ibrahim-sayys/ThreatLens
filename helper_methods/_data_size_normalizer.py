"""Data size normalizer helper

Functions:
- parse_size_to_gb(size_str, binary=False) -> float
    Parse a single size string like '43 TB' or '2.5gb' and return size in GB (float).

- extract_sizes_from_text(text, binary=False) -> List[float]
    Find all size occurrences in a piece of text and return list of sizes in GB.

- sum_sizes_in_text(text, binary=False, round_result=True) -> Optional[str]
    Extract sizes, sum them, and return the total as an integer string (GB).
    Returns None when no sizes are found.

Notes:
- Default conversion uses decimal SI units (1 TB = 1000 GB). Set binary=True to use 1024-based units.
- Recognizes shorthand (kb, mb, gb, tb, pb) and full words (kilobyte, megabyte, etc.).

Examples:
>>> sum_sizes_in_text('2 GB and 34 TB')  # decimal
'34002'
>>> sum_sizes_in_text('43tb')
'43000'
>>> sum_sizes_in_text('512 MB and 1.5 GB', binary=False)
'2'
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Regex to find numeric size tokens and unit names (supports decimal/comma separators)
_SIZE_RE = re.compile(
    r"(?P<number>\d{1,3}(?:[\d,_]*\d)?(?:[\.,]\d+)?)\s*(?P<unit>k|kb|kilobyte|kilobytes|m|mb|megabyte|megabytes|g|gb|gigabyte|gigabytes|t|tb|terabyte|terabytes|p|pb|petabyte|petabytes)\b",
    flags=re.IGNORECASE,
)

# Map unit keys to canonical short unit
_UNIT_CANON = {
    'k': 'KB', 'kb': 'KB', 'kilobyte': 'KB', 'kilobytes': 'KB',
    'm': 'MB', 'mb': 'MB', 'megabyte': 'MB', 'megabytes': 'MB',
    'g': 'GB', 'gb': 'GB', 'gigabyte': 'GB', 'gigabytes': 'GB',
    't': 'TB', 'tb': 'TB', 'terabyte': 'TB', 'terabytes': 'TB',
    'p': 'PB', 'pb': 'PB', 'petabyte': 'PB', 'petabytes': 'PB',
}


def _normalize_number(num_str: str) -> float:
    """Normalize numeric string with commas/underscores and return float."""
    s = num_str.replace(',', '').replace('_', '')
    s = s.replace(' ', '')
    s = s.replace('\u00A0', '')  # NBSP
    s = s.replace('−', '-')  # unicode minus
    s = s.replace('\u2009', '')
    # Replace comma decimal with dot if present and there's only one comma
    if s.count(',') == 1 and '.' not in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except Exception:
        # As a last resort try to extract digits
        digits = re.sub(r'[^0-9\.]', '', s)
        return float(digits) if digits else 0.0


def parse_size_to_gb(size_str: str, binary: bool = False) -> float:
    """Parse a single size string (e.g., '43 TB', '512MB') and return GB as float.

    Args:
        size_str: single token or short phrase containing number+unit
        binary: whether to use binary multiples (1024) instead of decimal (1000)
    Returns:
        size in GB (float)
    """
    m = _SIZE_RE.search(size_str)
    if not m:
        raise ValueError(f"No size found in '{size_str}'")

    number = _normalize_number(m.group('number'))
    unit_key = m.group('unit').lower()
    unit = _UNIT_CANON.get(unit_key, 'B')

    if binary:
        # binary multipliers (base 1024)
        multipliers = {
            'KB': 1.0 / (1024 ** 2),  # KB -> GB
            'MB': 1.0 / 1024,         # MB -> GB
            'GB': 1.0,
            'TB': 1024.0,
            'PB': 1024.0 ** 2,
        }
    else:
        # decimal SI multipliers (base 1000)
        multipliers = {
            'KB': 1.0e-6,
            'MB': 1.0e-3,
            'GB': 1.0,
            'TB': 1.0e3,
            'PB': 1.0e6,
        }

    factor = multipliers.get(unit, 0.0)
    return number * factor


def extract_sizes_from_text(text: str, binary: bool = False) -> List[float]:
    """Find all sizes in text and return list of sizes expressed in GB (floats).

    Preserves appearance order.
    """
    if not text or not isinstance(text, str):
        return []

    sizes: List[float] = []
    for m in _SIZE_RE.finditer(text):
        token = m.group(0)
        try:
            gb = parse_size_to_gb(token, binary=binary)
            sizes.append(gb)
        except Exception:
            # skip malformed token
            continue
    return sizes


def sum_sizes_in_text(text: str, binary: bool = False, round_result: bool = True) -> Optional[str]:
    """Extract sizes from `text`, sum them (in GB) and return total as integer string.

    Returns None if no sizes detected.
    """
    sizes = extract_sizes_from_text(text, binary=binary)
    if not sizes:
        return None

    total = sum(sizes)
    if round_result:
        total_int = int(round(total))
    else:
        total_int = total
    return str(total_int)


# Minimal self-test when run directly
if __name__ == '__main__':
    examples = [
        '2 gb, 34tb',
        '43tb',
        '512 MB and 1.5 GB',
        'No sizes here'
    ]
    for ex in examples:
        print(f"Input: {ex!r} -> Total GB: {sum_sizes_in_text(ex)}")

