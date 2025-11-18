#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper for 5butbkrljkaorg5maepuca25oma7eiwo6a2rlhvkblb4v6mf3ki2ovid.onion
Extracts ransomware leak data with pagination support.
"""

import sys
import os
import re
from urllib.parse import urljoin
from datetime import datetime
from helper_methods._URL_extractor import extract_urls
from helper_methods._stopword_filtering import remove_stopwords
from helper_methods._date_Normalizer import parse_relative_date
from helper_methods._industry_extractor import IndustryClassifier
from helper_methods._country_extractor import extract_countries
from helper_methods._breach_dept import SpacyDepartmentExtractor

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper_base import (
    BaseScraper,
    ThreatDataFields,
    create_empty_record,
    clean_newlines,
    validate_record
)


# --- Configuration ---
TARGET_URL = "http://5butbkrljkaorg5maepuca25oma7eiwo6a2rlhvkblb4v6mf3ki2ovid.onion/#list"


class RansomSiteScraper(BaseScraper):
    """Scraper for 5butbkrljkaorg5maepuca25oma7eiwo6a2rlhvkblb4v6mf3ki2ovid.onion"""

    def __init__(self, target_url: str, use_tor: bool = None):
        """Initialize the scraper with helper classifiers"""
        super().__init__(target_url, use_tor)

        # Initialize helper classifiers (reuse across all records)
        print("[INFO] Initializing helper classifiers...")
        self.industry_classifier = IndustryClassifier()
        self.dept_extractor = SpacyDepartmentExtractor()
        print("[INFO] Helper classifiers ready!")

    def parse_leak_data(self, soup):
        """
        Parse leak data from the page with pagination support.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of dictionaries containing scraped data
        """
        all_scraped_data = []
        current_page = 1

        # Start with the first page
        current_soup = soup

        while True:
            print(f"\n[INFO] Processing page {current_page}")

            # Extract data from current page
            page_data = self._extract_page_data(current_soup)
            all_scraped_data.extend(page_data)

            print(f"[INFO] Extracted {len(page_data)} records from page {current_page}")

            # Find next page link
            next_page_url = self._get_next_page_url(current_soup)

            if not next_page_url:
                print(f"[INFO] No more pages found. Total pages processed: {current_page}")
                break

            # Fetch next page
            print(f"[INFO] Moving to next page: {next_page_url}")
            try:
                current_soup = self.fetch_page(next_page_url)
                current_page += 1
            except Exception as e:
                print(f"[ERROR] Failed to fetch next page: {e}")
                break

        print(f"\n[SUCCESS] Total records scraped from all pages: {len(all_scraped_data)}")
        return all_scraped_data

    def _extract_page_data(self, soup):
        """
        Extract data from a single page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of records from this page
        """
        scraped_data = []

        # Find all company items
        posts = soup.find_all('div', class_='companies-list__item')

        if not posts:
            print("[WARNING] No posts found with class 'companies-list__item'")
            return scraped_data

        print(f"[INFO] Found {len(posts)} posts to process")

        for idx, post in enumerate(posts, 1):
            try:
                # ============================================
                # STEP 1: Extract raw data into variables
                # ============================================

                # Extract company name from <div class="name">
                company_name = ""
                name_div = post.find('div', class_='name')
                if name_div:
                    company_link = name_div.find('a')
                    if company_link:
                        company_name = clean_newlines(company_link.get_text())
                        print(f"[INFO] Processing {idx}/{len(posts)}: {company_name}")

                # Extract content from <div class="text">
                content = ""
                website = ""
                text_div = post.find('div', class_='text')
                if text_div:
                    content = clean_newlines(text_div.get_text())

                    # Use the helper to extract URLs from content
                    urls = extract_urls(content)

                # Extract download link
                download_link = ""
                download_btn = post.find('a', class_='btn btn-primary')
                if download_btn and download_btn.has_attr('href'):
                    download_link = download_btn.get('href')

                # Extract data from <div class="image">
                image_url = ""
                published_date = ""
                views_count = ""

                image_div = post.find('div', class_='image')
                if image_div:
                    # Extract image URL
                    img_tag = image_div.find('img')
                    if img_tag and img_tag.has_attr('src'):
                        image_src = img_tag.get('src')
                        if image_src:
                            image_url = urljoin(self.target_url, image_src)

                    # Extract published date and views
                    p_tags = image_div.find_all('p')
                    for p_tag in p_tags:
                        p_text = p_tag.get_text().strip()

                        # Check for "Published X ago" pattern
                        if 'published' in p_text.lower() or 'ago' in p_text.lower():
                            parsed_date = parse_relative_date(p_text)
                            if parsed_date:
                                published_date = parsed_date

                        # Check for "Views: X" pattern
                        if 'views:' in p_text.lower():
                            views_match = re.search(r'views:\s*(\d+)', p_text, re.IGNORECASE)
                            if views_match:
                                views_count = views_match.group(1)

                # Extract page title
                page_title = ""
                title_elem = soup.find('title')
                if title_elem:
                    page_title = clean_newlines(title_elem.get_text())

                # ============================================
                # STEP 2: Map all extracted data to enum fields
                # ============================================

                record = create_empty_record()

                # Company and content information
                record[ThreatDataFields.m_company_name.value]     = company_name
                record[ThreatDataFields.m_content.value]          = content
                record[ThreatDataFields.m_website.value]          = website

                # Links and media
                record[ThreatDataFields.m_download_link.value]    = download_link
                record[ThreatDataFields.m_image_url.value]        = image_url

                # Dates and metrics
                record[ThreatDataFields.m_date.value]             = published_date
                record[ThreatDataFields.m_views_count.value]      = views_count
                record[ThreatDataFields.m_scraped_date.value]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Source information
                record[ThreatDataFields.m_source_url.value]       = self.target_url
                record[ThreatDataFields.m_source_title.value]     = page_title

                # Classification
                record[ThreatDataFields.m_category.value]         = "ransomware"
                record[ThreatDataFields.m_severity.value]         = "high"
                record[ThreatDataFields.m_status.value]           = "active"

                # ============================================
                # STEP 3: Use helper methods to extract additional data
                # ============================================

                # Extract industry from content
                if content:
                    try:
                        industry = self.industry_classifier.get_industry(content)
                        record[ThreatDataFields.m_industry.value] = industry
                    except Exception as e:
                        print(f"    [WARNING] Industry extraction failed: {e}")
                        record[ThreatDataFields.m_industry.value] = "Unknown"

                # Extract countries from content
                if content:
                    try:
                        countries = extract_countries(content)
                        if countries:
                            if isinstance(countries, list):
                                record[ThreatDataFields.m_country.value] = ", ".join(countries)
                            else:
                                record[ThreatDataFields.m_country.value] = countries
                    except Exception as e:
                        print(f"    [WARNING] Country extraction failed: {e}")

                # Extract departments (which can help infer records affected)
                if content:
                    try:
                        departments = self.dept_extractor.extract_departments(content)
                        if departments:
                            # Store departments in data_type field (or you can add a new field)
                            record[ThreatDataFields.m_data_type.value] = ", ".join(departments)

                            # Infer records_affected based on department count and severity
                            # This is a heuristic - adjust as needed
                            dept_count = len(departments)
                            if "General Breach" not in departments:
                                if dept_count >= 5:
                                    record[ThreatDataFields.m_records_affected.value] = "10000+"
                                elif dept_count >= 3:
                                    record[ThreatDataFields.m_records_affected.value] = "5000+"
                                elif dept_count >= 2:
                                    record[ThreatDataFields.m_records_affected.value] = "1000+"
                                else:
                                    record[ThreatDataFields.m_records_affected.value] = "500+"
                    except Exception as e:
                        print(f"    [WARNING] Department extraction failed: {e}")

                # ============================================
                # STEP 4: Validate and save
                # ============================================

                is_valid, missing = validate_record(record)
                if is_valid:
                    scraped_data.append(record)
                    print(f"  ✓ Extracted: {company_name}")
                else:
                    print(f"  ✗ Skipping invalid record. Missing: {missing}")

            except Exception as e:
                print(f"  ✗ Error processing post {idx}: {e}")
                continue

        return scraped_data

    def _get_next_page_url(self, soup):
        """
        Find the next page URL from pagination.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            URL of next page, or None if no next page
        """
        # Find pagination <ul class="pagination">
        pagination = soup.find('ul', class_='pagination')

        if not pagination:
            return None

        # Look for the "Next" link (››)
        # It's in a <li> tag, and the link has rel="next"
        next_link = pagination.find('a', rel='next')

        if next_link and next_link.has_attr('href'):
            next_url = next_link.get('href')
            # Make absolute URL if relative
            return urljoin(self.target_url, next_url)

        return None


def main():
    """Run this scraper individually"""
    scraper = RansomSiteScraper(TARGET_URL)
    records_count = scraper.run()
    print(f"\n[DONE] Total records scraped: {records_count}")


if __name__ == "__main__":
    main()
