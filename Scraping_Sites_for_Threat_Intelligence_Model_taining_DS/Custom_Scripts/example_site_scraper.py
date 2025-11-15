#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example scraper for a specific site.
Copy this template for each new site you want to scrape.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper_base import (
    BaseScraper,
    ThreatDataFields,
    create_empty_record,
    clean_newlines,
    normalize_date,
    validate_record
)

# --- Configuration ---
TARGET_URL = "http://example.onion"  # CHANGE THIS to your target site


class ExampleSiteScraper(BaseScraper):
    """Scraper for Example Site"""

    def parse_leak_data(self, soup):
        """
        Parse leak data from the page.
        CUSTOMIZE THIS METHOD based on the site's HTML structure.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of dictionaries containing scraped data
        """
        scraped_data = []

        # CUSTOMIZE: Find all posts/cards/articles based on site structure
        posts = soup.find_all('div', class_='post')  # Adjust selector

        print(f"[INFO] Found {len(posts)} posts to process")

        for idx, post in enumerate(posts, 1):
            print(f"[INFO] Processing post {idx}/{len(posts)}")

            # Create a new empty record
            record = create_empty_record()

            # CUSTOMIZE: Extract company name
            company_elem = post.find('h2', class_='company')  # Adjust selector
            if company_elem:
                record[ThreatDataFields.m_company_name.value] = clean_newlines(company_elem.get_text())

            # CUSTOMIZE: Extract date
            date_elem = post.find('span', class_='date')  # Adjust selector
            if date_elem:
                raw_date = date_elem.get_text()
                normalized_date = normalize_date(raw_date)
                record[ThreatDataFields.m_breach_date.value] = normalized_date

            # CUSTOMIZE: Extract country
            country_elem = post.find('span', class_='country')  # Adjust selector
            if country_elem:
                record[ThreatDataFields.m_country.value] = clean_newlines(country_elem.get_text())

            # CUSTOMIZE: Extract description
            desc_elem = post.find('p', class_='description')  # Adjust selector
            if desc_elem:
                record[ThreatDataFields.m_description.value] = clean_newlines(desc_elem.get_text())

            # CUSTOMIZE: Extract industry/sector
            industry_elem = post.find('span', class_='industry')  # Adjust selector
            if industry_elem:
                record[ThreatDataFields.m_industry.value] = clean_newlines(industry_elem.get_text())

            # CUSTOMIZE: Extract threat actor/ransomware group
            threat_elem = post.find('span', class_='threat-actor')  # Adjust selector
            if threat_elem:
                record[ThreatDataFields.m_threat_actor.value] = clean_newlines(threat_elem.get_text())

            # Add source information
            record[ThreatDataFields.m_source_url.value] = self.target_url

            # Get page title
            title_elem = soup.find('title')
            if title_elem:
                record[ThreatDataFields.m_source_title.value] = clean_newlines(title_elem.get_text())

            # CUSTOMIZE: Set category based on site type (use string values)
            record[ThreatDataFields.m_category.value] = "ransomware"  # or "data_breach", "malware", etc.

            # CUSTOMIZE: Set severity (use string values)
            record[ThreatDataFields.m_severity.value] = "high"  # or "critical", "medium", "low"

            # CUSTOMIZE: Set status (use string values)
            record[ThreatDataFields.m_status.value] = "active"  # or "resolved", "investigating", etc.

            # Validate record before adding
            is_valid, missing = validate_record(record)
            if is_valid:
                scraped_data.append(record)
                company = record.get(ThreatDataFields.m_company_name.value, "Unknown")
                print(f"  ✓ Extracted: {company}")
            else:
                print(f"  ✗ Skipping invalid record. Missing: {missing}")

        return scraped_data


def main():
    """Run this scraper individually"""
    scraper = ExampleSiteScraper(TARGET_URL)
    records_count = scraper.run()
    print(f"\n[DONE] Total records scraped: {records_count}")


if __name__ == "__main__":
    main()
