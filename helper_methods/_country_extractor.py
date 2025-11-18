#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Country Extractor Helper Method
Extracts up to two country names from text using comprehensive country lists.
Returns canonical full country names; allows only a small set of short forms (UK, US/USA, UAE).
"""

import re
from typing import List, Optional

# Full country names only (no abbreviations or codes)
FULL_COUNTRY_NAMES = {
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
    "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
    "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
    "Korea North", "Korea South", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal",
    "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea",
    "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
    "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
    "Tanzania", "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom",
    "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela",
    "Vietnam", "Yemen", "Zambia", "Zimbabwe",
}

# Common short forms that are allowed (mapped to full names)
COMMON_SHORT_FORMS = {
    "uk": "United Kingdom",
    "usa": "United States",
    "us": "United States",
    "uae": "United Arab Emirates",
}

# Build canonical mapping (lowercased -> canonical full name)
CANONICAL_MAP = {name.lower(): name for name in FULL_COUNTRY_NAMES}
CANONICAL_MAP.update(COMMON_SHORT_FORMS)

# Prepare pattern alternation with longer names first to avoid partial matches
IDENTIFIERS = sorted(CANONICAL_MAP.keys(), key=lambda s: -len(s))
PATTERN = re.compile(r"\b(" + r"|".join(re.escape(k) for k in IDENTIFIERS) + r")\b", flags=re.IGNORECASE)


def extract_countries(text: str, max_countries: int = 2) -> Optional[List[str]]:
    """
    Extract up to `max_countries` country names from text in appearance order.
    Returns a list of canonical full country names (mapped from allowed short forms).

    Args:
        text: input text
        max_countries: maximum number of countries to return (default 2)

    Returns:
        List of country full names (<= max_countries) or None if none found
    """
    if not text or not isinstance(text, str):
        return None

    found: List[str] = []
    seen = set()
    for m in PATTERN.finditer(text):
        key = m.group(1).lower()
        canonical = CANONICAL_MAP.get(key)
        if not canonical:
            # fallback - should not normally happen
            canonical = m.group(1).title()
        if canonical not in seen:
            found.append(canonical)
            seen.add(canonical)
        if len(found) >= max_countries:
            break

    return found if found else None


def has_countries(text: str) -> bool:
    """Return True if any country (allowed identifiers) is found in text."""
    return extract_countries(text) is not None


def get_country_count(text: str, max_countries: int = 2) -> int:
    """Return number of countries found (capped at max_countries)."""
    countries = extract_countries(text, max_countries=max_countries)
    return len(countries) if countries else 0


if __name__ == "__main__":
    # Minimal print to indicate module is ready and show usage
    print("Country extractor ready. Call: extract_countries(text, max_countries=2)")
