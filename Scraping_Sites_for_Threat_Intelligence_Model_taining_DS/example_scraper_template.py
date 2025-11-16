#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example scraping script template using the standardized scraping schema.
Copy this template for each new site you want to scrape.
"""

import requests
from bs4 import BeautifulSoup
import sys
from datetime import datetime

# Import the standardized schema
from scraping_schema import (
    ThreatDataFields,
    ThreatDataCSVWriter,
    DataCategory,
    SeverityLevel,
    IncidentStatus,
    create_empty_record,
    validate_record
)

# Import helper methods
sys.path.append('../..')
from helper_methods._string_cleaner import clean_newlines
from helper_methods._date_Normalizer import normalize_date

# --- Configuration ---
TARGET_URL = "http://example.onion"  # Replace with your target URL
OUTPUT_CSV = "scraped_data.csv"
TIMEOUT = 30

# Tor proxy configuration
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
PROXIES = {
    "http": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
    "https": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
}
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def scrape_site(url: str, use_tor: bool = False):
    """
    Scrape threat intelligence data from a website.

    Args:
        url: Target URL to scrape
        use_tor: Whether to use Tor proxy (for .onion sites)

    Returns:
        List of dictionaries containing scraped data
    """
    print(f"[INFO] Scraping: {url}")

    # Setup session
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # Use Tor proxy for .onion sites or if explicitly requested
    if use_tor or url.endswith('.onion'):
        session.proxies.update(PROXIES)
        print("[INFO] Using Tor proxy")

    try:
        # Fetch the page
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Clean unwanted elements
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        # Extract data - CUSTOMIZE THIS SECTION FOR EACH SITE
        scraped_data = []

        # Example: Find all posts/cards/articles
        posts = soup.find_all('div', class_='post')  # Adjust selector based on site structure

        for post in posts:
            # Create a new empty record
            record = create_empty_record()

            # Extract company name
            company_elem = post.find('h2', class_='company')  # Adjust selector
            if company_elem:
                record[ThreatDataFields.COMPANY_NAME.value] = clean_newlines(company_elem.get_text())

            # Extract date
            date_elem = post.find('span', class_='date')  # Adjust selector
            if date_elem:
                raw_date = date_elem.get_text()
                normalized_date = normalize_date(raw_date)
                record[ThreatDataFields.BREACH_DATE.value] = normalized_date

            # Extract country
            country_elem = post.find('span', class_='country')  # Adjust selector
            if country_elem:
                record[ThreatDataFields.COUNTRY.value] = clean_newlines(country_elem.get_text())

            # Extract description
            desc_elem = post.find('p', class_='description')  # Adjust selector
            if desc_elem:
                record[ThreatDataFields.DESCRIPTION.value] = clean_newlines(desc_elem.get_text())

            # Extract industry/sector
            industry_elem = post.find('span', class_='industry')  # Adjust selector
            if industry_elem:
                record[ThreatDataFields.INDUSTRY.value] = clean_newlines(industry_elem.get_text())

            # Add source information
            record[ThreatDataFields.SOURCE_URL.value] = url
            record[ThreatDataFields.SOURCE_TITLE.value] = soup.find('title').get_text() if soup.find('title') else ""

            # Add category (adjust based on site type)
            record[ThreatDataFields.CATEGORY.value] = DataCategory.RANSOMWARE.value

            # Add status
            record[ThreatDataFields.STATUS.value] = IncidentStatus.ACTIVE.value

            # Validate record before adding
            is_valid, missing = validate_record(record)
            if is_valid:
                scraped_data.append(record)
                print(f"[SUCCESS] Extracted: {record[ThreatDataFields.COMPANY_NAME.value]}")
            else:
                print(f"[WARNING] Skipping invalid record. Missing fields: {missing}")

        return scraped_data

    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout after {TIMEOUT} seconds")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []


def main():
    """Main execution function"""
    print("=== Threat Intelligence Scraper ===")
    print(f"Target: {TARGET_URL}")
    print(f"Output: {OUTPUT_CSV}\n")

    # Scrape the site
    is_onion = TARGET_URL.endswith('.onion')
    data = scrape_site(TARGET_URL, use_tor=is_onion)

    if not data:
        print("\n[WARNING] No data scraped!")
        return

    # Write to CSV using the standardized writer
    print(f"\n[INFO] Writing {len(data)} records to {OUTPUT_CSV}")

    with ThreatDataCSVWriter(OUTPUT_CSV) as writer:
        writer.write_rows(data)

    print("[SUCCESS] Scraping completed!")
    print(f"[INFO] Total records: {len(data)}")


if __name__ == "__main__":
    main()

