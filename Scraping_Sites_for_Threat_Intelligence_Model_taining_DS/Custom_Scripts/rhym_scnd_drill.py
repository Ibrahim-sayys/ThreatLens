#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Playwright scraper that drills into the 229 Companies modal and extracts leak records."""

import os
import sys
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Ensure package modules resolve when running from Custom_Scripts
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
scraping_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if scraping_pkg not in sys.path:
    sys.path.insert(0, scraping_pkg)

from config import OUTPUT_PATH
from helper_methods._string_cleaner import clean_newlines
from helper_methods._data_size_normalizer import sum_sizes_in_text
from helper_methods._breach_dept import SpacyDepartmentExtractor
from helper_methods._industry_extractor import IndustryClassifier
from scraping_schema import (
    ThreatDataFields,
    ThreatDataCSVWriter,
    create_empty_record,
    validate_record,
)

TARGET_URL = "http://rhysidafohrhyy2aszi7bm32tnjat5xri65fopcxkdfxhi4tidsg7cad.onion/"
TOR_PROXY = {"server": "socks5://127.0.0.1:9050"}


class RhymSecondDrillScraper:
    """Scrapes the companies modal after clicking the big button and records every detail."""

    def __init__(self, target_url: str = TARGET_URL):
        self.target_url = target_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.dept_extractor = SpacyDepartmentExtractor()
        self.industry_classifier = IndustryClassifier()

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, proxy=TOR_PROXY)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        print("[INFO] Playwright browser launched with Tor proxy")

    def stop_browser(self):
        for resource in (self.page, self.context, self.browser, self.playwright):
            if resource:
                try:
                    resource.close()
                except Exception:
                    pass

    def fetch_companies_modal(self):
        print(f"[INFO] Navigating to {self.target_url}")
        self.page.goto(self.target_url, wait_until="domcontentloaded")
        print("[INFO] Waiting for companies button...")
        self.page.wait_for_selector("#companies_online")
        print("[INFO] Clicking companies button to open the window of companies...")
        self.page.click("#companies_online")
        print("[INFO] Waiting for companies modal to appear...")
        self.page.wait_for_selector(".modal.show")
        print("[INFO] Waiting for company list to render inside modal...")
        self.page.wait_for_selector(".modal.show div.border.m-2.p-2")
        # Add delay to ensure all content is loaded
        self.page.wait_for_timeout(3000)
        return self.page

    def _extract_modal_fields(self, modal_html, base_url):
        modal_soup = BeautifulSoup(modal_html, "html.parser")
        record = create_empty_record()

        header = modal_soup.find("h5", class_=lambda c: c and "modal-title" in c)
        if header and header.get_text(strip=True):
            record[ThreatDataFields.m_company_name.value] = clean_newlines(header.get_text()).strip()

        content = ""
        for div in modal_soup.find_all("div", class_="m-2"):
            if div.find("a"):
                continue
            text = div.get_text(separator=" ", strip=True)
            if text:
                content = clean_newlines(text)
                break
        if not content:
            body = modal_soup.get_text(separator=" ", strip=True)
            content = clean_newlines(body)
        record[ThreatDataFields.m_content.value] = content

        geo_match = re.search(r"GEO\s*[:\-]?\s*([A-Za-z .]+)", modal_soup.get_text(" ", strip=True), re.IGNORECASE)
        if geo_match:
            country = geo_match.group(1).strip()
            record[ThreatDataFields.m_country.value] = country

        download_links = []
        for a in modal_soup.find_all("a", href=True):
            href = a.get("href")
            text = a.get_text(strip=True)
            if ".onion" in href or "Documents" in text or "part" in text.lower():
                download_links.append(urljoin(base_url, href))
        if download_links:
            record[ThreatDataFields.m_download_link.value] = ", ".join(download_links)

        modal_text = modal_soup.get_text(" ", strip=True)
        size = self._parse_leak_size(modal_text)
        if size:
            record[ThreatDataFields.m_leak_size.value] = size

        images = []
        for img in modal_soup.find_all("img", src=True):
            images.append(urljoin(base_url, img.get("src")))
        if images:
            record[ThreatDataFields.m_image_url.value] = ", ".join(images)

        self._apply_helpers(record)

        record[ThreatDataFields.m_source_url.value] = self.target_url
        record[ThreatDataFields.m_category.value] = "ransomware"
        record[ThreatDataFields.m_status.value] = "active"
        record[ThreatDataFields.m_scraped_date.value] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return record

    def _parse_leak_size(self, text):
        catalog = re.search(r"Data Catalog\s*[:\-]?\s*([^\n]+)", text, re.IGNORECASE)
        fragment = catalog.group(1) if catalog else text
        try:
            return sum_sizes_in_text(fragment)
        except Exception as exc:
            print(f"  [WARNING] size normalization failed: {exc}")
            return ""

    def _apply_helpers(self, record):
        content_text = record.get(ThreatDataFields.m_content.value, "") or ""
        if content_text:
            print(f"  [DEBUG] Content fed to helpers: {content_text[:120]}...")
        else:
            print("  [DEBUG] No content available for helper extraction")

        try:
            departments = self.dept_extractor.extract_departments(content_text)
            if departments:
                record[ThreatDataFields.m_data_type.value] = ", ".join(departments)
                print(f"  [DEBUG] Departments: {departments}")
            else:
                record[ThreatDataFields.m_data_type.value] = "Unknown"
        except Exception as exc:
            print(f"  [WARNING] department helper failed: {exc}")
            record[ThreatDataFields.m_data_type.value] = "Unknown"

        try:
            industry = self.industry_classifier.get_industry(content_text)
            if industry:
                record[ThreatDataFields.m_industry.value] = industry
            else:
                record[ThreatDataFields.m_industry.value] = "Generic"
        except Exception as exc:
            print(f"  [WARNING] industry helper failed: {exc}")
            record[ThreatDataFields.m_industry.value] = "Generic"

    def parse_records(self, writer):
        records = []
        cards = self.page.query_selector_all(".modal.show div.border.m-2.p-2")
        print(f"[INFO] Found {len(cards)} company cards")
        for idx, card in enumerate(cards, 1):
            try:
                # Website link is in the first <a> with href and target="_blank"
                website_link = card.query_selector("a[href][target='_blank']")
                website = website_link.get_attribute("href") if website_link else ""

                # More button is nested deeper: div.row > div.col-10 > button[data-company]
                # So we query from card to find button with data-company attribute
                more_button = card.query_selector("button[data-company]")
                if not more_button:
                    print(f"[{idx}] no More button found in card; skipping")
                    # Debug: print card HTML to see what's inside
                    card_html = card.inner_html()
                    print(f"[{idx}] Card HTML snippet: {card_html[:1000]}...")
                    continue

                company_name = card.query_selector("a[href][target='_blank']")
                company_text = company_name.text_content().strip() if company_name else f"Company {idx}"
                print(f"[{idx}] Processing: {company_text}")

                more_button.click()
                self.page.wait_for_selector(".modal.show", timeout=10000)
                modal = self.page.query_selector(".modal.show")
                if not modal:
                    print(f"[{idx}] modal did not appear after clicking More")
                    continue

                modal_html = modal.inner_html()
                record = self._extract_modal_fields(modal_html, self.target_url)
                if website:
                    record[ThreatDataFields.m_website.value] = website
                # Set company name from the card's link text
                record[ThreatDataFields.m_company_name.value] = company_text

                ok, missing = validate_record(record)
                if ok:
                    records.append(record)
                    writer.write_row(record)  # Append immediately to CSV
                    print(f"[{idx}] ✓ Extracted and appended: {record.get(ThreatDataFields.m_company_name.value)}")
                else:
                    print(f"[{idx}] ✗ Record incomplete, missing: {missing}")
            except Exception as exc:
                print(f"[{idx}] ✗ Error: {exc}")
            finally:
                try:
                    close_btn = self.page.query_selector(".modal.show button.btn-close")
                    if close_btn:
                        close_btn.click()
                    else:
                        self.page.keyboard.press("Escape")
                except Exception:
                    pass
                self.page.wait_for_timeout(500)
        return records

    def run(self):
        self.start_browser()
        try:
            self.fetch_companies_modal()
            mode = "a" if os.path.exists(OUTPUT_PATH) else "w"
            with ThreatDataCSVWriter(OUTPUT_PATH, mode=mode) as writer:
                records = self.parse_records(writer)
                if not records:
                    print("[WARNING] No records extracted")
                    return
                print(f"[SUCCESS] Wrote {len(records)} records to {OUTPUT_PATH}")
        finally:
            self.stop_browser()


if __name__ == "__main__":
    scraper = RhymSecondDrillScraper()
    scraper.run()
