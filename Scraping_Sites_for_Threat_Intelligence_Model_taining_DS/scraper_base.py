#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base scraper module - Provides common functionality for all scrapers.
Handles HTTP requests, proxy setup, and CSV writing.
"""

import requests
from bs4 import BeautifulSoup
import sys
from datetime import datetime
import time

# Import configuration
from config import (
    PROXIES, USER_AGENT, TIMEOUT, USE_TOR_BY_DEFAULT,
    OUTPUT_PATH, DELAY_BETWEEN_REQUESTS, MAX_RETRIES
)

# Import the standardized schema
from scraping_schema import (
    ThreatDataFields,
    ThreatDataCSVWriter,
    create_empty_record,
    validate_record
)

# Import helper methods
sys.path.append('..')
from helper_methods._string_cleaner import clean_newlines
from helper_methods._date_Normalizer import normalize_date


class BaseScraper:
    """
    Base class for all scrapers. Handles HTTP requests and CSV writing.
    Individual scrapers only need to implement parse_leak_data().
    """

    def __init__(self, target_url: str, use_tor: bool = None):
        """
        Initialize the scraper.

        Args:
            target_url: The URL to scrape
            use_tor: Whether to use Tor proxy (defaults to config setting)
        """
        self.target_url = target_url
        self.use_tor = use_tor if use_tor is not None else (USE_TOR_BY_DEFAULT or target_url.endswith('.onion'))
        self.session = self._create_session()

    def _create_session(self):
        """Create and configure a requests session"""
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        if self.use_tor:
            session.proxies.update(PROXIES)
            print(f"[INFO] Using Tor proxy for {self.target_url}")

        return session

    def fetch_page(self, url: str = None) -> BeautifulSoup:
        """
        Fetch and parse a page.

        Args:
            url: URL to fetch (defaults to target_url)

        Returns:
            BeautifulSoup object of the page

        Raises:
            Exception: If request fails after all retries
        """
        url = url or self.target_url

        for attempt in range(MAX_RETRIES):
            try:
                print(f"[INFO] Fetching: {url} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(url, timeout=TIMEOUT)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Clean unwanted elements
                for tag in soup(['script', 'style', 'noscript', 'iframe']):
                    tag.decompose()

                return soup

            except requests.exceptions.Timeout:
                print(f"[WARNING] Timeout on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS * 2)
                else:
                    raise Exception(f"Timeout after {MAX_RETRIES} attempts")

            except requests.exceptions.RequestException as e:
                print(f"[WARNING] Request failed on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS * 2)
                else:
                    raise Exception(f"Request failed after {MAX_RETRIES} attempts: {e}")

    def parse_leak_data(self, soup: BeautifulSoup) -> list:
        """
        Parse the page and extract leak data.
        This method MUST be implemented by each scraper.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of dictionaries containing scraped data
        """
        raise NotImplementedError("Each scraper must implement parse_leak_data()")

    def run(self) -> int:
        """
        Run the scraper: fetch page, parse data, write to CSV.

        Returns:
            Number of records scraped
        """
        print(f"\n{'='*60}")
        print(f"Scraping: {self.target_url}")
        print(f"{'='*60}\n")

        try:
            # Fetch the page
            soup = self.fetch_page()

            # Parse leak data (implemented by child class)
            scraped_data = self.parse_leak_data(soup)

            if not scraped_data:
                print("[WARNING] No data extracted from this site")
                return 0

            # Write to the shared CSV (append mode)
            print(f"\n[INFO] Writing {len(scraped_data)} records to {OUTPUT_PATH}")

            with ThreatDataCSVWriter(OUTPUT_PATH, mode='a') as writer:
                writer.write_rows(scraped_data)

            print(f"[SUCCESS] Successfully scraped {len(scraped_data)} records!")
            return len(scraped_data)

        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")
            return 0


# Helper function to create records easily
def create_record(**kwargs):
    """
    Create a record with provided fields.

    Usage:
        record = create_record(
            company_name="Example Corp",
            country="USA",
            breach_date="2025-01-15"
        )
    """
    record = create_empty_record()
    for key, value in kwargs.items():
        # Convert snake_case to enum if needed
        if hasattr(ThreatDataFields, key.upper()):
            field = getattr(ThreatDataFields, key.upper())
            record[field.value] = value
        else:
            record[key] = value
    return record


# Export commonly used items
__all__ = [
    'BaseScraper',
    'create_record',
    'create_empty_record',
    'ThreatDataFields',
    'clean_newlines',
    'normalize_date',
    'validate_record',
]
