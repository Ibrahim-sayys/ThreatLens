#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom scraper for site with modal popups referenced by "More info" buttons.
Extracts fields into the standardized record schema.
"""

import sys
import os
from urllib.parse import urljoin
from datetime import datetime
import re

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper_base import (
    BaseScraper,
    ThreatDataFields,
    create_empty_record,
    clean_newlines,
    validate_record,
)
from helper_methods._data_size_normalizer import sum_sizes_in_text
from config import OUTPUT_PATH
from scraping_schema import ThreatDataCSVWriter
from helper_methods._breach_dept import SpacyDepartmentExtractor
from helper_methods._industry_extractor import IndustryClassifier

# --- Configuration ---
TARGET_URL = "http://sarcomawmawlhov7o5mdhz4eszxxlkyaoiyiy2b5iwxnds2dmb4jakad.onion/"  # replace with actual site root when running


class ModalSiteScraper(BaseScraper):
    """Scraper that extracts details from modals referenced by buttons."""

    def __init__(self, target_url: str, use_tor: bool = None):
        super().__init__(target_url, use_tor)
        self.dept_extractor = SpacyDepartmentExtractor()
        self.industry_classifier = IndustryClassifier()

    def parse_leak_data(self, soup):
        scraped = []

        # Find containers that include the company buttons
        rows = soup.find_all('div', class_='row row-cols-4 mb-4')
        if not rows:
            print('[WARNING] No rows found')
            return scraped

        for row in rows:
            # find all buttons in this row
            buttons = row.find_all('button', class_=lambda c: c and 'company_button' in c)
            for btn in buttons:
                try:
                    # Each button references a modal via data-bs-target attribute like '#company_145'
                    target = btn.get('data-bs-target') or btn.get('data-target')
                    if not target:
                        continue

                    modal_id = target.lstrip('#')
                    modal = soup.find(id=modal_id)
                    if not modal:
                        # modal might be injected elsewhere; try by id globally
                        modal = soup.find(id=modal_id)
                    if not modal:
                        print(f"[WARNING] Modal {modal_id} not found for button; skipping")
                        continue

                    # Create record template
                    record = create_empty_record()

                    # Company name from modal header h5.modal-title
                    company_elem = modal.find('h5', class_=lambda c: c and 'modal-title' in c)
                    company_name = clean_newlines(company_elem.get_text()) if company_elem else ''
                    record[ThreatDataFields.m_company_name.value] = company_name

                    # Full modal text content as m_content
                    modal_body = modal.find('div', class_=lambda c: c and 'modal-body' in c)
                    content_text = ''
                    if modal_body:
                        content_text = clean_newlines(modal_body.get_text(separator=' ')).strip()
                        record[ThreatDataFields.m_content.value] = content_text

                    # Use helper to extract departments from content
                    if content_text:
                        departments = self.dept_extractor.extract_departments(content_text)
                        if departments:
                            record[ThreatDataFields.m_data_type.value] = ', '.join(departments)

                        # Use helper to classify industry from content
                        industry = self.industry_classifier.get_industry(content_text)
                        if industry:
                            record[ThreatDataFields.m_industry.value] = industry

                    # Country: look for a div containing 'GEO:' and take the text after it
                    country = ''
                    geo_el = modal.find(string=re.compile(r'GEO\s*:\s*', re.IGNORECASE))
                    if geo_el:
                        # geo_el may be a NavigableString; get its parent text and extract
                        geo_text = geo_el if isinstance(geo_el, str) else geo_el.get_text()
                        m = re.search(r'GEO\s*:\s*(.+)', geo_text, re.IGNORECASE)
                        if m:
                            country = m.group(1).strip()
                    else:
                        # fallback: search for any text like 'GEO: Country' in modal
                        for div in modal.find_all(text=re.compile(r'GEO\s*:\s*', re.IGNORECASE)):
                            m = re.search(r'GEO\s*:\s*(.+)', div, re.IGNORECASE)
                            if m:
                                country = m.group(1).strip()
                                break
                    if country:
                        # remove trailing words like ' ' or extra descriptors
                        country = country.split()[0] if ' ' in country else country
                        record[ThreatDataFields.m_country.value] = country

                    # Leak size: delegate entire modal/modal_body text to helper
                    text_for_size_parsing = modal_body.get_text(separator=' ') if modal_body else modal.get_text(separator=' ')
                    try:
                        s = sum_sizes_in_text(text_for_size_parsing)
                        if s:
                            record[ThreatDataFields.m_leak_size.value] = s
                    except Exception as e:
                        print(f"    [WARNING] Leak size parsing failed: {e}")

                    # Download link
                    download_link = ''
                    dl_div = modal.find('div', string=re.compile(r'Download Link', re.IGNORECASE))
                    if dl_div:
                        a = dl_div.find_next('a')
                        if a and a.has_attr('href'):
                            download_link = a.get('href')
                    else:
                        a = modal.find('a', href=True)
                        if a:
                            download_link = a.get('href')
                    if download_link:
                        record[ThreatDataFields.m_download_link.value] = download_link

                    # Images
                    images = []
                    if modal_body:
                        imgs = modal_body.find_all('img')
                        for img in imgs:
                            src = img.get('src')
                            if src:
                                images.append(urljoin(self.target_url, src))
                    if images:
                        record[ThreatDataFields.m_image_url.value] = ', '.join(images)

                    # Populate metadata
                    record[ThreatDataFields.m_source_url.value] = self.target_url
                    record[ThreatDataFields.m_category.value] = 'ransomware'
                    record[ThreatDataFields.m_status.value] = 'active'
                    record[ThreatDataFields.m_scraped_date.value] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Validate & append
                    ok, missing = validate_record(record)
                    if ok:
                        scraped.append(record)
                        print(f"  ✓ Extracted: {company_name}")
                    else:
                        print(f"  ✗ Skipping invalid record (missing: {missing}): {company_name}")

                except Exception as ex:
                    print(f"  ✗ Error processing modal/button: {ex}")
                    continue

        return scraped

    def _get_next_page_url(self, soup, current_page=1):
        """Find the next page link by looking for an anchor whose text equals current_page+1."""
        nav = soup.find('div', class_=lambda c: c and 'text-center' in c and 'text-white' in c)
        if not nav:
            return None
        next_text = str(current_page + 1)
        a = nav.find('a', string=lambda s: s and s.strip() == next_text)
        if a and a.has_attr('href'):
            return urljoin(self.target_url, a.get('href'))
        return None


def main():
    scraper = ModalSiteScraper(TARGET_URL)

    # Crawl pages until no next page found
    current_page = 1
    total_records = 0
    try:
        soup = scraper.fetch_page()
        while True:
            print(f"[INFO] Processing page {current_page}")
            records = scraper.parse_leak_data(soup)
            total_records += len(records)

            # Write extracted records to the shared CSV immediately (append or create)
            try:
                mode = 'a' if os.path.exists(OUTPUT_PATH) else 'w'
                with ThreatDataCSVWriter(OUTPUT_PATH, mode=mode) as writer:
                    if records:
                        writer.write_rows(records)
                        print(f"  [INFO] Wrote {len(records)} records to {OUTPUT_PATH}")
                    else:
                        print("  [INFO] No valid records to write for this page")
            except Exception as e:
                print(f"  [ERROR] Failed to write records to CSV: {e}")

            next_url = scraper._get_next_page_url(soup, current_page=current_page)
            if not next_url:
                break
            # fetch next page
            soup = scraper.fetch_page(next_url)
            current_page += 1
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")

    print(f"\n[DONE] Total extracted records: {total_records}")


if __name__ == '__main__':
    main()
