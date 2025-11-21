#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom scraper for Rhysida site with company list and modal details.
Extracts fields into the standardized record schema.
Uses Playwright for better JavaScript rendering.
"""

import sys
import os
from urllib.parse import urljoin
from datetime import datetime
import re

# Ensure project root on path (two levels up) so `helper_methods` and other top-level packages resolve
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Also keep the scraping package directory on path for local imports
scraping_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if scraping_pkg not in sys.path:
    sys.path.insert(0, scraping_pkg)

from scraping_schema import ThreatDataFields, create_empty_record, validate_record
from helper_methods._string_cleaner import clean_newlines
from helper_methods._data_size_normalizer import sum_sizes_in_text
from config import OUTPUT_PATH
from scraping_schema import ThreatDataCSVWriter
from helper_methods._breach_dept import SpacyDepartmentExtractor
from helper_methods._industry_extractor import IndustryClassifier

# Playwright imports
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup

# --- Configuration ---
TARGET_URL = "http://rhysidafohrhyy2aszi7bm32tnjat5xri65fopcxkdfxhi4tidsg7cad.onion/"


class RhysidaScraper:
    """Scraper that extracts details from company list and modals using Playwright."""

    def __init__(self, target_url: str):
        self.target_url = target_url
        self.dept_extractor = SpacyDepartmentExtractor()
        self.industry_classifier = IndustryClassifier()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def start_browser(self):
        """Start Playwright browser with Tor proxy."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:9050"}
        )
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def stop_browser(self):
        """Stop browser and cleanup."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_page(self):
        """Fetch page using Playwright, click the companies button to load dynamic content."""
        print(f"[INFO] Navigating to {self.target_url}")
        self.page.goto(self.target_url, wait_until="domcontentloaded")

        print("[INFO] Waiting for companies button...")
        self.page.wait_for_selector("#companies_online", timeout=30000)

        print("[INFO] Clicking companies button...")
        self.page.click("#companies_online")

        print("[INFO] Waiting for company divs to load...")
        self.page.wait_for_selector("div.border.m-2.p-2", timeout=30000)

        self.page.wait_for_timeout(2000)
        html = self.page.content()
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def parse_leak_data(self, soup, writer=None):
        scraped = []

        try:
            live_buttons = self.page.query_selector_all('button[data-company]')
        except Exception:
            live_buttons = []

        if live_buttons:
            print(f"[INFO] Found {len(live_buttons)} live buttons (Playwright)")
            live_mode = True
        else:
            print('[WARNING] No live buttons found; falling back to static HTML')
            live_mode = False

        if live_mode:
            containers = live_buttons
        else:
            containers = soup.find_all('div', class_='border m-2 p-2')

        for idx, container in enumerate(containers, 1):
            try:
                record = create_empty_record()

                if live_mode:
                    btn = container
                    data_company = btn.get_attribute('data-company')
                    if not data_company:
                        print(f"[{idx}] Live button missing data-company; skipping")
                        continue

                    modal_id = f"company_{data_company}"
                    modal_soup = None

                    try:
                        btn.scroll_into_view_if_needed()

                        try:
                            outer = btn.evaluate('el => el.outerHTML')
                            print(f"  [DEBUG] Clicking button outerHTML: {outer[:200]}")
                        except Exception:
                            pass

                        try:
                            btn.click(force=True)
                        except TypeError:
                            try:
                                btn.evaluate('el => el.click()')
                            except Exception:
                                btn.click()

                        try:
                            self.page.wait_for_selector(f'#{modal_id}', state='visible', timeout=15000)
                            modal_html = self.page.inner_html(f'#{modal_id}')
                            modal_soup = BeautifulSoup(modal_html, 'html.parser')
                        except Exception:

                            try:
                                self.page.wait_for_selector('.modal.show', state='visible', timeout=15000)
                                modal_el = self.page.query_selector('.modal.show')
                                if modal_el:
                                    modal_html = modal_el.inner_html()
                                    modal_soup = BeautifulSoup(modal_html, 'html.parser')
                            except Exception:
                                fname = f"/tmp/modal_debug_{os.getpid()}_{idx}.png"
                                try:
                                    self.page.screenshot(path=fname, full_page=True)
                                    print(f"  [DEBUG] Screenshot saved: {fname}")
                                except Exception:
                                    pass

                                modal = soup.find(id=modal_id)
                                if not modal:
                                    print(f"[{idx}] Modal {modal_id} missing; skipping")
                                    continue

                                modal_soup = modal

                        header = modal_soup.find(class_=re.compile(r'modal-title'))
                        if header and header.get_text(strip=True):
                            record[ThreatDataFields.m_company_name.value] = clean_newlines(header.get_text()).strip()

                        else:
                            try:
                                ancestor = btn.evaluate_handle('el => el.closest(".row")')
                                if ancestor:
                                    link = ancestor.query_selector('a[href]')
                                    if link:
                                        record[ThreatDataFields.m_company_name.value] = clean_newlines(link.inner_text()).strip()
                            except Exception:
                                pass

                        first_link = modal_soup.find('a', href=True, target='_blank')
                        if first_link:
                            record[ThreatDataFields.m_website.value] = first_link.get('href')

                        try:
                            self.page.click(f'#{modal_id} button.btn-close', timeout=2000)
                        except Exception:
                            try:
                                self.page.keyboard.press('Escape')
                            except Exception:
                                pass

                    except Exception as e:
                        print(f"[{idx}] Error handling button: {e}")
                        continue

                else:
                    company_div = container
                    main_link = company_div.find('a', href=True)

                    if not main_link:
                        print(f"[{idx}] No main link found (static); skipping")
                        continue

                    record[ThreatDataFields.m_company_name.value] = clean_newlines(main_link.get_text()).strip()
                    record[ThreatDataFields.m_website.value] = main_link.get('href')

                    data_btn = company_div.find('button', attrs={'data-company': True})
                    if not data_btn:
                        print(f"[{idx}] No data-company button; skipping")
                        continue

                    data_company = data_btn.get('data-company')
                    modal = soup.find(id=f"company_{data_company}")
                    if not modal:
                        print(f"[{idx}] Modal missing; skipping")
                        continue

                    modal_soup = modal

                if modal_soup:
                    # Correct extraction: find the div with class 'm-2' that contains the description, not the one with 'm-2 h4'
                    content_divs = modal_soup.find_all('div', class_='m-2')
                    content_found = False
                    for div in content_divs:
                        if not div.find('a') and div.get_text(strip=True):
                            text = clean_newlines(div.get_text(separator=' ')).strip()
                            record[ThreatDataFields.m_content.value] = text
                            print(f"  [DEBUG] m_content: '{text[:100]}...'")
                            content_found = True
                            break
                    if not content_found:
                        print(f"  [DEBUG] m_content div not found or has link")

                    dlinks = []
                    for a in modal_soup.find_all('a', href=True):
                        link_text = a.get_text(strip=True)
                        if 'Documents' in link_text or 'part' in link_text.lower() or '.onion' in a.get('href', ''):
                            dlinks.append(a.get('href'))
                    if dlinks:
                        record[ThreatDataFields.m_download_link.value] = ", ".join(dlinks)
                        print(f"  [DEBUG] m_download_link: {len(dlinks)} links")
                    else:
                        print(f"  [DEBUG] No download links found")

                    size_text = modal_soup.get_text()
                    m = re.search(r'Data Catalog:\s*(.+)', size_text, re.IGNORECASE)
                    if m:
                        try:
                            s = sum_sizes_in_text(m.group(1))
                            if s:
                                record[ThreatDataFields.m_leak_size.value] = s
                                print(f"  [DEBUG] m_leak_size: {s}")
                            else:
                                print(f"  [DEBUG] Leak size parsed to empty")
                        except Exception as e:
                            print(f"  [DEBUG] Leak size parsing error: {e}")
                    else:
                        print(f"  [DEBUG] Data Catalog not found in modal text")

                    images = []
                    for img in modal_soup.find_all('img', src=True):
                        images.append(urljoin(self.target_url, img.get('src')))
                    if images:
                        record[ThreatDataFields.m_image_url.value] = ", ".join(images)
                        print(f"  [DEBUG] m_image_url: {len(images)} images")
                    else:
                        print(f"  [DEBUG] No images found")

                    # --- NEW: Use helpers to extract departments (data_type) and industry ---
                    # Prefer m_content; if empty, use the whole modal text as fallback
                    content_text = record.get(ThreatDataFields.m_content.value, '')
                    if not content_text or not content_text.strip():
                        modal_text = modal_soup.get_text(separator=' ', strip=True)
                        content_text = modal_text
                        print(f"  [DEBUG] m_content empty — falling back to modal text for helpers: '{content_text[:120]}...'")
                    else:
                        print(f"  [DEBUG] Using m_content for helpers: '{content_text[:120]}...'")

                    # Populate data_type using SpacyDepartmentExtractor
                    try:
                        depts = self.dept_extractor.extract_departments(content_text)
                        print(f"  [DEBUG] SpacyDepartmentExtractor returned: {depts}")
                        if depts:
                            record[ThreatDataFields.m_data_type.value] = ', '.join(depts)
                            print(f"  [DEBUG] m_data_type set from breach_dept: {record[ThreatDataFields.m_data_type.value]}")
                        else:
                            record[ThreatDataFields.m_data_type.value] = 'Unknown'
                            print(f"  [DEBUG] m_data_type: Unknown (no departments found)")
                    except Exception as e:
                        print(f"  [DEBUG] Department extraction error: {e}")
                        record[ThreatDataFields.m_data_type.value] = 'Unknown'

                    # Populate industry using IndustryClassifier (default to Generic if empty)
                    try:
                        industry = self.industry_classifier.get_industry(content_text)
                        print(f"  [DEBUG] IndustryClassifier returned: '{industry}'")
                        if not industry or (isinstance(industry, str) and not industry.strip()):
                            industry = 'Generic'
                        record[ThreatDataFields.m_industry.value] = industry
                        print(f"  [DEBUG] m_industry set: {industry}")
                    except Exception as e:
                        print(f"  [DEBUG] Industry extraction error: {e}")
                        record[ThreatDataFields.m_industry.value] = 'Generic'

                    print(f"  [DEBUG] m_company_name: '{record.get(ThreatDataFields.m_company_name.value, 'N/A')}'")
                    print(f"  [DEBUG] m_website: '{record.get(ThreatDataFields.m_website.value, 'N/A')}'")
                    print(f"  [DEBUG] m_data_type: '{record.get(ThreatDataFields.m_data_type.value, 'N/A')}'")
                    print(f"  [DEBUG] m_industry: '{record.get(ThreatDataFields.m_industry.value, 'N/A')}'")
                else:
                    print(f"  [DEBUG] modal_soup is None, skipping extraction")

                record[ThreatDataFields.m_source_url.value] = self.target_url
                record[ThreatDataFields.m_category.value] = 'ransomware'
                record[ThreatDataFields.m_status.value] = 'active'
                record[ThreatDataFields.m_scraped_date.value] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                ok, missing = validate_record(record)
                if ok:
                    scraped.append(record)
                    if writer:
                        writer.write_row(record)
                    print(f"[{idx}] ✓ Extracted successfully")
                else:
                    print(f"[{idx}] ✗ Validation failed — missing: {missing}")

            except Exception as ex:
                print(f"[{idx}] ERROR: {ex}")
                continue

        return scraped


def main():
    scraper = RhysidaScraper(TARGET_URL)

    try:
        scraper.start_browser()

        soup = scraper.fetch_page()

        mode = 'a' if os.path.exists(OUTPUT_PATH) else 'w'
        with ThreatDataCSVWriter(OUTPUT_PATH, mode=mode) as writer:
            records = scraper.parse_leak_data(soup, writer)
            print(f"[SUCCESS] Processed {len(records)} records, appended instantly to {OUTPUT_PATH}")

    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
    finally:
        scraper.stop_browser()


if __name__ == '__main__':
    main()
