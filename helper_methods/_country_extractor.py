#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Country Extractor Helper Method
Extracts country names from text using comprehensive country lists.
"""

import re
from typing import List, Set, Union

# Comprehensive list of country names and common variations
COUNTRY_NAMES = {
    # Full country names
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

    # Common country name variations and abbreviations
    "USA", "US", "United States of America", "America",
    "UK", "Britain", "Great Britain", "England",
    "UAE", "Dubai", "Abu Dhabi",
    "South Korea", "Korea",
    "North Korea", "Democratic People's Republic of Korea",
    "Czechia", "Czech Republic",
    "Ivory Coast", "Cote d'Ivoire",
    "Burma", "Myanmar",
    "East Timor", "Timor-Leste",
    "Swaziland", "Eswatini",
    "Macedonia", "North Macedonia",
    "Cape Verde", "Cabo Verde",
    "Vatican", "Holy See",
    "Palestine", "Palestinian Territories",
    "Taiwan", "Republic of China",
    "Hong Kong", "Macau",  # Special administrative regions
    "Puerto Rico", "Guam", "American Samoa",  # US territories
    "Greenland", "Faroe Islands",  # Danish territories
    "French Guiana", "Martinique", "Guadeloupe", "Reunion",  # French territories
    "Netherlands Antilles", "Aruba", "Curacao",  # Dutch territories
}

# Country codes (ISO 3166-1 alpha-2 and alpha-3)
COUNTRY_CODES = {
    # Alpha-2 codes
    "AF", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR", "AM", "AW", "AU", "AT", "AZ",
    "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BA", "BW", "BV", "BR",
    "IO", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "KY", "CF", "TD", "CL", "CN", "CX",
    "CC", "CO", "KM", "CG", "CD", "CK", "CR", "CI", "HR", "CU", "CY", "CZ", "DK", "DJ", "DM",
    "DO", "EC", "EG", "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ", "FI", "FR", "GF", "PF",
    "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD", "GP", "GU", "GT", "GG", "GN",
    "GW", "GY", "HT", "HM", "VA", "HN", "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM",
    "IL", "IT", "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG", "LA", "LV",
    "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MK", "MG", "MW", "MY", "MV", "ML", "MT",
    "MH", "MQ", "MR", "MU", "YT", "MX", "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM",
    "NA", "NR", "NP", "NL", "AN", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MP", "NO", "OM",
    "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN", "PL", "PT", "PR", "QA", "RE", "RO",
    "RU", "RW", "SH", "KN", "LC", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL",
    "SG", "SK", "SI", "SB", "SO", "ZA", "GS", "ES", "LK", "SD", "SR", "SJ", "SZ", "SE", "CH",
    "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV",
    "UG", "UA", "AE", "GB", "US", "UM", "UY", "UZ", "VU", "VE", "VN", "VG", "VI", "WF", "EH",
    "YE", "ZM", "ZW",

    # Alpha-3 codes (subset)
    "AFG", "ALB", "DZA", "ASM", "AND", "AGO", "AIA", "ATA", "ATG", "ARG", "ARM", "ABW", "AUS",
    "AUT", "AZE", "BHS", "BHR", "BGD", "BRB", "BLR", "BEL", "BLZ", "BEN", "BMU", "BTN", "BOL",
    "BIH", "BWA", "BVT", "BRA", "IOT", "BRN", "BGR", "BFA", "BDI", "KHM", "CMR", "CAN", "CPV",
    "CYM", "CAF", "TCD", "CHL", "CHN", "CXR", "CCK", "COL", "COM", "COG", "COD", "COK", "CRI",
    "CIV", "HRV", "CUB", "CYP", "CZE", "DNK", "DJI", "DMA", "DOM", "ECU", "EGY", "SLV", "GNQ",
    "ERI", "EST", "ETH", "FLK", "FRO", "FJI", "FIN", "FRA", "GUF", "PYF", "ATF", "GAB", "GMB",
    "GEO", "DEU", "GHA", "GIB", "GRC", "GRL", "GRD", "GLP", "GUM", "GTM", "GGY", "GIN", "GNB",
    "GUY", "HTI", "HMD", "VAT", "HND", "HKG", "HUN", "ISL", "IND", "IDN", "IRN", "IRQ", "IRL",
    "IMN", "ISR", "ITA", "JAM", "JPN", "JEY", "JOR", "KAZ", "KEN", "KIR", "PRK", "KOR", "KWT",
    "KGZ", "LAO", "LVA", "LBN", "LSO", "LBR", "LBY", "LIE", "LTU", "LUX", "MAC", "MKD", "MDG",
    "MWI", "MYS", "MDV", "MLI", "MLT", "MHL", "MTQ", "MRT", "MUS", "MYT", "MEX", "FSM", "MDA",
    "MCO", "MNG", "MNE", "MSR", "MAR", "MOZ", "MMR", "NAM", "NRU", "NPL", "NLD", "ANT", "NCL",
    "NZL", "NIC", "NER", "NGA", "NIU", "NFK", "MNP", "NOR", "OMN", "PAK", "PLW", "PSE", "PAN",
    "PNG", "PRY", "PER", "PHL", "PCN", "POL", "PRT", "PRI", "QAT", "REU", "ROU", "RUS", "RWA",
    "SHN", "KNA", "LCA", "SPM", "VCT", "WSM", "SMR", "STP", "SAU", "SEN", "SRB", "SYC", "SLE",
    "SGP", "SVK", "SVN", "SLB", "SOM", "ZAF", "SGS", "ESP", "LKA", "SDN", "SUR", "SJM", "SWZ",
    "SWE", "CHE", "SYR", "TWN", "TJK", "TZA", "THA", "TLS", "TGO", "TKL", "TON", "TTO", "TUN",
    "TUR", "TKM", "TCA", "TUV", "UGA", "UKR", "ARE", "GBR", "USA", "UMI", "URY", "UZB", "VUT",
    "VEN", "VNM", "VGB", "VIR", "WLF", "ESH", "YEM", "ZMB", "ZWE",
}

# Combine all country identifiers
ALL_COUNTRY_IDENTIFIERS = COUNTRY_NAMES.union(COUNTRY_CODES)


def extract_countries(text: str) -> List[str]:
    """
    Extract country names from text.

    This function searches for country names and codes in the given text
    and returns a list of all countries found.

    Args:
        text: The text to search for country names

    Returns:
        List of country names/codes found in the text (may be empty)

    Examples:
        >>> extract_countries("I live in Germany and work in France")
        ['Germany', 'France']

        >>> extract_countries("The company is based in USA and UK")
        ['USA', 'UK']

        >>> extract_countries("This text has no countries")
        []
    """
    if not text or not isinstance(text, str):
        return []

    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Find all country matches
    found_countries = set()

    for country in ALL_COUNTRY_IDENTIFIERS:
        # Use word boundaries to avoid partial matches
        # For example, "US" shouldn't match "USA" or "Russia"
        country_lower = country.lower()

        # Use regex with word boundaries for better matching
        pattern = r'\b' + re.escape(country_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_countries.add(country)

    # Return as sorted list for consistent output
    return sorted(list(found_countries))


def has_countries(text: str) -> bool:
    """
    Check if text contains any country names.

    Args:
        text: The text to check

    Returns:
        True if any countries are found, False otherwise

    Examples:
        >>> has_countries("I live in Germany")
        True

        >>> has_countries("This is just text")
        False
    """
    return len(extract_countries(text)) > 0


def get_country_count(text: str) -> int:
    """
    Get the number of different countries mentioned in text.

    Args:
        text: The text to analyze

    Returns:
        Number of unique countries found

    Examples:
        >>> get_country_count("Germany and France are EU countries")
        2

        >>> get_country_count("No countries here")
        0
    """
    return len(extract_countries(text))


# Test the functions if run directly
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "I live in Germany and work in France",
        "The company is based in USA and has offices in UK and Canada",
        "This text mentions no countries at all",
        "Welcome to China, the most populous country in Asia",
        "Brazil is a beautiful country with amazing beaches",
        "The meeting will be held in Switzerland (CH) and Germany (DE)",
        "No country names here, just regular text",
        "Afghanistan and Albania are both in Europe",  # Test for partial matches
    ]

    print("=== Country Extraction Test ===\n")

    for i, text in enumerate(test_texts, 1):
        countries = extract_countries(text)
        has_any = has_countries(text)
        count = get_country_count(text)

        print(f"Test {i}:")
        print(f"  Text: {text}")
        print(f"  Countries found: {countries}")
        print(f"  Has countries: {has_any}")
        print(f"  Count: {count}")
        print()

