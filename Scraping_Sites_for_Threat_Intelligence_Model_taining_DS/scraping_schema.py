#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraping Schema - Standardized field definitions for threat intelligence data scraping.
This module provides enums and constants to ensure consistency across all custom scraping scripts.
"""

from enum import Enum
from typing import List, Dict, Any
import csv
from datetime import datetime



class ThreatDataFields(Enum):
    """
    Standard fields for threat intelligence data.
    Use these field names consistently across all scraping scripts.
    """
    # Primary identification fields
    m_company_name = "company_name"
    m_organization = "organization"
    m_victim_name = "victim_name"

    # Breach/Incident information
    m_breach_date = "breach_date"
    m_publish_date = "publish_date"
    m_discovery_date = "discovery_date"

    # Location information
    m_country = "country"
    m_region = "region"
    m_city = "city"

    # Industry/Sector
    m_industry = "industry"
    m_sector = "sector"

    # Data details
    m_data_type = "data_type"
    m_data_size = "data_size"
    m_records_affected = "records_affected"

    # Threat actor information
    m_threat_actor = "threat_actor"
    m_threat_group = "threat_group"
    m_ransomware_group = "ransomware_group"

    # Technical details
    m_attack_type = "attack_type"
    m_vulnerability = "vulnerability"
    m_malware_family = "malware_family"

    # Description and content
    m_description = "description"
    m_summary = "summary"
    m_full_text = "full_text"
    m_content = "content"

    # Source information
    m_source_url = "source_url"
    m_source_title = "source_title"

    # Additional metadata
    m_post_id = "post_id"
    m_scraped_date = "scraped_date"
    m_tags = "tags"
    m_category = "category"  # e.g., "ransomware", "data_breach", "malware", "phishing", etc.
    m_severity = "severity"  # e.g., "critical", "high", "medium", "low"
    m_status = "status"  # e.g., "active", "resolved", "investigating"

    # Contact/Leak information
    m_leak_size = "leak_size"
    m_leak_url = "leak_url"
    m_download_link = "download_link"

    # Financial information
    m_ransom_amount = "ransom_amount"
    m_ransom_paid = "ransom_paid"

    # Additional useful fields
    m_revenue = "revenue"  # Company revenue
    m_employee_count = "employee_count"  # Number of employees
    m_website = "website"  # Company website
    m_impact = "impact"  # Impact description
    m_mitigation = "mitigation"  # Mitigation steps taken
    m_ioc = "ioc"  # Indicators of Compromise
    m_cve = "cve"  # CVE identifier if applicable

    # New fields
    m_date = "date"  # General date field
    m_image_url = "image_url"  # URL of an image related to the threat
    m_views_count = "views_count"  # Number of views or hits


# Standard CSV field order - Use this for consistent CSV output
STANDARD_CSV_FIELDS = [
    ThreatDataFields.m_company_name.value,
    ThreatDataFields.m_date.value,
    ThreatDataFields.m_breach_date.value,
    ThreatDataFields.m_publish_date.value,
    ThreatDataFields.m_country.value,
    ThreatDataFields.m_industry.value,
    ThreatDataFields.m_threat_actor.value,
    ThreatDataFields.m_ransomware_group.value,
    ThreatDataFields.m_attack_type.value,
    ThreatDataFields.m_data_type.value,
    ThreatDataFields.m_data_size.value,
    ThreatDataFields.m_records_affected.value,
    ThreatDataFields.m_content.value,
    ThreatDataFields.m_description.value,
    ThreatDataFields.m_source_url.value,
    ThreatDataFields.m_source_title.value,
    ThreatDataFields.m_category.value,
    ThreatDataFields.m_severity.value,
    ThreatDataFields.m_status.value,
    ThreatDataFields.m_leak_url.value,
    ThreatDataFields.m_download_link.value,
    ThreatDataFields.m_image_url.value,
    ThreatDataFields.m_views_count.value,
    ThreatDataFields.m_ransom_amount.value,
    ThreatDataFields.m_website.value,
    ThreatDataFields.m_revenue.value,
    ThreatDataFields.m_employee_count.value,
    ThreatDataFields.m_impact.value,
    ThreatDataFields.m_cve.value,
    ThreatDataFields.m_scraped_date.value,
    ThreatDataFields.m_tags.value,
]

# Minimal required fields - These should always be present
REQUIRED_FIELDS = [
    ThreatDataFields.m_company_name.value,
    ThreatDataFields.m_source_url.value,
    ThreatDataFields.m_scraped_date.value,
]


class ThreatDataCSVWriter:
    """
    Helper class to write threat intelligence data to CSV files consistently.

    Usage:
        writer = ThreatDataCSVWriter('output.csv')
        writer.write_row({
            ThreatDataFields.COMPANY_NAME: "Example Corp",
            ThreatDataFields.BREACH_DATE: "2025-01-15",
            ThreatDataFields.COUNTRY: "USA",
        })
        writer.close()
    """

    def __init__(self, filename: str, fields: List[str] = None, mode: str = 'w'):
        """
        Initialize CSV writer.

        Args:
            filename: Output CSV file path
            fields: List of field names (uses STANDARD_CSV_FIELDS if None)
            mode: File mode ('w' for write/overwrite, 'a' for append)
        """
        self.filename = filename
        self.fields = fields if fields else STANDARD_CSV_FIELDS
        self.mode = mode
        self.file = None
        self.writer = None
        self._initialize_file()

    def _initialize_file(self):
        """Initialize the CSV file and writer"""
        self.file = open(self.filename, self.mode, encoding='utf-8', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fields, extrasaction='ignore')

        # Write header only if creating new file
        if self.mode == 'w':
            self.writer.writeheader()

    def write_row(self, data: Dict[Any, Any]):
        """
        Write a single row to CSV.

        Args:
            data: Dictionary with field names as keys (can use ThreatDataFields enum or strings)
        """
        # Convert enum keys to string values
        processed_data = {}
        for key, value in data.items():
            field_name = key.value if isinstance(key, ThreatDataFields) else key
            processed_data[field_name] = value

        # Add scraped date if not present
        if ThreatDataFields.m_scraped_date.value not in processed_data:
            processed_data[ThreatDataFields.m_scraped_date.value] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.writer.writerow(processed_data)
        self.file.flush()  # Ensure data is written immediately

    def write_rows(self, data_list: List[Dict[Any, Any]]):
        """
        Write multiple rows to CSV.

        Args:
            data_list: List of dictionaries with field names as keys
        """
        for data in data_list:
            self.write_row(data)

    def close(self):
        """Close the CSV file"""
        if self.file:
            self.file.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def create_empty_record() -> Dict[str, str]:
    """
    Create an empty record with all standard fields initialized to empty strings.
    Useful as a template when scraping.

    Returns:
        Dictionary with all STANDARD_CSV_FIELDS as keys and empty strings as values
    """
    return {field: "" for field in STANDARD_CSV_FIELDS}


def validate_record(record: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate that a record contains all required fields.

    Args:
        record: Dictionary to validate

    Returns:
        Tuple of (is_valid: bool, missing_fields: List[str])
    """
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if field not in record or not record[field]:
            missing_fields.append(field)

    return len(missing_fields) == 0, missing_fields


# Example usage and documentation
if __name__ == "__main__":
    print("=== Threat Intelligence Scraping Schema ===\n")

    print("Available Fields:")
    for field in ThreatDataFields:
        print(f"  - {field.value}")

    print("\n\nStandard CSV Field Order:")
    for i, field in enumerate(STANDARD_CSV_FIELDS, 1):
        print(f"  {i}. {field}")

    print("\n\nExample Usage:")
    print("""
    from scraping_schema import ThreatDataFields, ThreatDataCSVWriter
    
    # Method 1: Using context manager (recommended)
    with ThreatDataCSVWriter('output.csv') as writer:
        writer.write_row({
            ThreatDataFields.m_company_name: "Example Corp",
            ThreatDataFields.m_breach_date: "2025-01-15",
            ThreatDataFields.m_country: "USA",
            ThreatDataFields.m_category: "ransomware",
        })
    
    # Method 2: Manual close
    writer = ThreatDataCSVWriter('output.csv')
    writer.write_row({
        ThreatDataFields.m_company_name: "Another Company",
        ThreatDataFields.m_threat_actor: "APT29",
    })
    writer.close()
    """)
