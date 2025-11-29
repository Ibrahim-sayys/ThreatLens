#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Data Parser for Threat Intelligence
Parses JSON file data with leak_model format and extracts fields into standardized CSV schema.
Uses helper methods for department, industry, and country extraction.
"""

import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List
import importlib.util

# Ensure project root on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
scraping_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if scraping_pkg not in sys.path:
    sys.path.insert(0, scraping_pkg)

# --- Robust imports: scraping_schema and config ---
try:
    from scraping_schema import ThreatDataFields, create_empty_record, validate_record, ThreatDataCSVWriter
except Exception:
    # Fallback: load scraping_schema from file path
    spec_path = os.path.join(scraping_pkg, 'scraping_schema.py')
    spec = importlib.util.spec_from_file_location('scraping_schema', spec_path)
    scraping_schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scraping_schema)
    ThreatDataFields = scraping_schema.ThreatDataFields
    create_empty_record = scraping_schema.create_empty_record
    validate_record = scraping_schema.validate_record
    ThreatDataCSVWriter = scraping_schema.ThreatDataCSVWriter

try:
    from config import OUTPUT_PATH
except Exception:
    spec_conf = importlib.util.spec_from_file_location('config', os.path.join(scraping_pkg, 'config.py'))
    config_mod = importlib.util.module_from_spec(spec_conf)
    spec_conf.loader.exec_module(config_mod)
    OUTPUT_PATH = getattr(config_mod, 'OUTPUT_PATH', getattr(config_mod, 'OUTPUT_CSV', 'threat_intelligence_data.csv'))

from helper_methods._string_cleaner import clean_newlines
from helper_methods._breach_dept import SpacyDepartmentExtractor
from helper_methods._industry_extractor import IndustryClassifier
from helper_methods._country_extractor import extract_countries
from helper_methods._date_Normalizer import smart_date_parse


class JSONDataParser:
    """Parser that extracts threat intelligence data from JSON files with leak_model format."""

    # Available source fields from leak_model
    AVAILABLE_FIELDS = {
        1: ('m_title', 'Company/Title name'),
        2: ('m_ref_html', 'Reference HTML'),
        3: ('m_url', 'Source URL'),
        4: ('m_base_url', 'Base URL'),
        5: ('m_content', 'Main content/description'),
        6: ('m_screenshot', 'Screenshot URL'),
        7: ('m_network', 'Network type (e.g., onion)'),
        8: ('m_important_content', 'Important content'),
        9: ('m_weblink', 'Website links'),
        10: ('m_dumplink', 'Download/dump links'),
        11: ('m_content_type', 'Content type'),
        12: ('m_leak_date', 'Leak date'),
        13: ('m_revenue', 'Company revenue'),
        14: ('m_data_size', 'Data size'),
        15: ('m_logo_or_images', 'Logo or images associated with the data'),
    }

    def __init__(self, json_file_path: str, selected_fields: List[str] = None):
        self.json_file_path = json_file_path
        self.selected_fields = selected_fields or []  # List of field names to extract
        self.dept_extractor = SpacyDepartmentExtractor()
        self.industry_classifier = IndustryClassifier()

    @classmethod
    def display_available_fields(cls):
        """Display available fields for user selection."""
        print("\n" + "="*60)
        print("Available leak_model fields:")
        print("="*60)
        for num, (field_name, description) in sorted(cls.AVAILABLE_FIELDS.items()):
            print(f"  {num:2d}. {field_name:20s} - {description}")
        print("="*60)

    def parse_leak_model_string(self, leak_model_str: str) -> Dict[str, Any]:
        """
        Parse a leak_model string representation into a dictionary.
        
        Example input:
        "leak_model(m_ref_html=None, m_title='Swedish Arts Council', ...)"
        
        Returns:
            Dictionary with parsed fields
        """
        parsed = {}
        
        # Remove 'leak_model(' prefix and trailing ')'
        content = leak_model_str.strip()
        if content.startswith('leak_model('):
            content = content[11:]  # Remove 'leak_model('
        if content.endswith(')'):
            content = content[:-1]  # Remove trailing ')'
        
        # Parse key=value pairs
        # Handle different value types: None, strings with quotes, lists, dates, etc.
        pattern = r"(\w+)=([^,]+(?:\([^)]*\))?(?:\[[^\]]*\])?)"
        
        # More robust parsing - split by ', m_' to handle field boundaries
        fields = content.split(', m_')
        
        for i, field in enumerate(fields):
            if i == 0:
                # First field doesn't have 'm_' prefix stripped
                if field.startswith('m_'):
                    field = field[2:]
            else:
                # Add back 'm_' prefix for consistency
                field = 'm_' + field
            
            # Split on first '='
            if '=' not in field:
                continue
                
            key, value = field.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Parse value based on type
            if value == 'None':
                parsed[key] = None
            elif value.startswith('[') and value.endswith(']'):
                # List value
                list_content = value[1:-1]
                if not list_content.strip():
                    parsed[key] = []
                else:
                    # Parse list items (strings)
                    items = []
                    for item in re.findall(r"'([^']*)'", list_content):
                        items.append(item)
                    parsed[key] = items
            elif value.startswith('datetime.date('):
                # Date value
                date_match = re.search(r'datetime\.date\((\d+),\s*(\d+),\s*(\d+)\)', value)
                if date_match:
                    year, month, day = date_match.groups()
                    parsed[key] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif value.startswith("'") and value.endswith("'"):
                # String value with single quotes
                parsed[key] = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                # String value with double quotes
                parsed[key] = value[1:-1]
            else:
                # Plain value (number or other)
                parsed[key] = value
        
        return parsed

    def parse_json_file(self, json_data: Any) -> List[Dict[str, Any]]:
        """
        Parse JSON data into list of parsed leak models.
        
        Args:
            json_data: Can be a single object, list of objects, or JSONL format
            
        Returns:
            List of parsed leak model dictionaries
        """
        parsed_models = []
        
        # Handle different JSON formats
        if isinstance(json_data, str):
            # Single leak_model string
            parsed = self.parse_leak_model_string(json_data)
            parsed_models.append(parsed)
        elif isinstance(json_data, list):
            # List of leak_model strings or objects
            for item in json_data:
                if isinstance(item, str):
                    parsed = self.parse_leak_model_string(item)
                    parsed_models.append(parsed)
                elif isinstance(item, dict):
                    parsed_models.append(item)
        elif isinstance(json_data, dict):
            # Single object
            parsed_models.append(json_data)
        
        return parsed_models

    @staticmethod
    def find_leak_models_in_text(text: str) -> List[str]:
        """
        Find all occurrences of leak_model(...) blocks in a text using balanced parentheses parsing.
        Returns list of full leak_model(...) strings.
        """
        blocks = []
        if not text or 'leak_model(' not in text:
            return blocks

        i = 0
        L = len(text)
        while True:
            start = text.find('leak_model(', i)
            if start == -1:
                break
            # position at the opening parenthesis
            pos = start + len('leak_model(')
            depth = 1
            in_single = False
            in_double = False
            esc = False
            while pos < L and depth > 0:
                ch = text[pos]
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == "'" and not in_double:
                    in_single = not in_single
                elif ch == '"' and not in_single:
                    in_double = not in_double
                elif not in_single and not in_double:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                pos += 1

            # Extract full block (from start to pos)
            block = text[start:pos]
            blocks.append(block)
            i = pos

        return blocks

    def extract_from_leak_model(self, leak_model: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract standardized threat intelligence record from parsed leak_model.
        Only extracts fields that were selected by the user.

        Args:
            leak_model: Parsed leak_model dictionary
            
        Returns:
            Standardized record dictionary
        """
        record = create_empty_record()
        content_text = ''

        # Helper function to check if field is selected
        def is_selected(field_name: str) -> bool:
            return not self.selected_fields or field_name in self.selected_fields

        # Extract company name from m_title (if selected)
        if is_selected('m_title') and 'm_title' in leak_model and leak_model['m_title']:
            record[ThreatDataFields.m_company_name.value] = clean_newlines(leak_model['m_title']).strip()

        # Extract content from m_content (if selected)
        if is_selected('m_content') and 'm_content' in leak_model and leak_model['m_content']:
            content_text = clean_newlines(leak_model['m_content']).strip()
            record[ThreatDataFields.m_content.value] = content_text

        # Fallback to m_important_content (if selected and m_content not available)
        if not content_text and is_selected('m_important_content'):
            if 'm_important_content' in leak_model and leak_model['m_important_content']:
                content_text = clean_newlines(leak_model['m_important_content']).strip()
                record[ThreatDataFields.m_content.value] = content_text

        # Extract date from m_leak_date (if selected)
        if is_selected('m_leak_date') and 'm_leak_date' in leak_model and leak_model['m_leak_date']:
            date_value = leak_model['m_leak_date']
            if isinstance(date_value, str):
                record[ThreatDataFields.m_date.value] = date_value
            else:
                record[ThreatDataFields.m_date.value] = str(date_value)

            # Normalize date using date normalizer if present
            if record.get(ThreatDataFields.m_date.value):
                normalized = smart_date_parse(record[ThreatDataFields.m_date.value])
                if normalized:
                    record[ThreatDataFields.m_date.value] = normalized

        # Extract website URL from m_weblink (if selected)
        if is_selected('m_weblink') and 'm_weblink' in leak_model and leak_model['m_weblink']:
            weblinks = leak_model['m_weblink']
            if isinstance(weblinks, list) and weblinks:
                record[ThreatDataFields.m_website.value] = weblinks[0]
            elif isinstance(weblinks, str):
                record[ThreatDataFields.m_website.value] = weblinks
        
        # Extract revenue from m_revenue (if selected)
        if is_selected('m_revenue') and 'm_revenue' in leak_model and leak_model['m_revenue']:
            record[ThreatDataFields.m_revenue.value] = str(leak_model['m_revenue'])
        
        # Extract download links from m_dumplink (if selected)
        if is_selected('m_dumplink') and 'm_dumplink' in leak_model and leak_model['m_dumplink']:
            dumplinks = leak_model['m_dumplink']
            if isinstance(dumplinks, list) and dumplinks:
                record[ThreatDataFields.m_download_link.value] = ", ".join(dumplinks)
            elif isinstance(dumplinks, str):
                record[ThreatDataFields.m_download_link.value] = dumplinks
        
        # Extract data size from m_data_size (if selected)
        if is_selected('m_data_size') and 'm_data_size' in leak_model and leak_model['m_data_size']:
            data_size = str(leak_model['m_data_size'])
            if data_size.lower() != 'unknown':
                record[ThreatDataFields.m_leak_size.value] = data_size
        
        # Extract source URL from m_url or m_base_url (if selected)
        if is_selected('m_url') and 'm_url' in leak_model and leak_model['m_url']:
            record[ThreatDataFields.m_source_url.value] = leak_model['m_url']
        elif is_selected('m_base_url') and 'm_base_url' in leak_model and leak_model['m_base_url']:
            record[ThreatDataFields.m_source_url.value] = leak_model['m_base_url']
        
        # Extract screenshot (if selected)
        if is_selected('m_screenshot') and 'm_screenshot' in leak_model and leak_model['m_screenshot']:
            record[ThreatDataFields.m_image_url.value] = leak_model['m_screenshot']

        # Extract network type (if selected) - store in tags or category
        if is_selected('m_network') and 'm_network' in leak_model and leak_model['m_network']:
            # Could add to tags field
            record[ThreatDataFields.m_tags.value] = f"network:{leak_model['m_network']}"

        # Extract employee count if available
        if content_text:
            # Try to find employee count in content
            employee_match = re.search(r'employee count:\s*(\d+)', content_text, re.IGNORECASE)
            if employee_match:
                record[ThreatDataFields.m_employee_count.value] = employee_match.group(1)
        
        # Use helper methods to extract additional information from content
        if content_text:
            # Extract departments/data types using SpacyDepartmentExtractor
            try:
                depts = self.dept_extractor.extract_departments(content_text)
                print(f"  [DEBUG] Extracted departments: {depts}")
                if depts:
                    record[ThreatDataFields.m_data_type.value] = ', '.join(depts)
                else:
                    record[ThreatDataFields.m_data_type.value] = 'Unknown'
            except Exception as e:
                print(f"  [DEBUG] Department extraction error: {e}")
                record[ThreatDataFields.m_data_type.value] = 'Unknown'
            
            # Extract industry using IndustryClassifier
            try:
                industry = self.industry_classifier.get_industry(content_text)
                print(f"  [DEBUG] Extracted industry: '{industry}'")
                if not industry or (isinstance(industry, str) and not industry.strip()):
                    industry = 'Generic'
                record[ThreatDataFields.m_industry.value] = industry
            except Exception as e:
                print(f"  [DEBUG] Industry extraction error: {e}")
                record[ThreatDataFields.m_industry.value] = 'Generic'
            
            # Extract country using country extractor
            try:
                countries = extract_countries(content_text, max_countries=2)
                print(f"  [DEBUG] Extracted countries: {countries}")
                if countries and isinstance(countries, list):
                    record[ThreatDataFields.m_country.value] = ', '.join(countries)
                elif countries:
                    record[ThreatDataFields.m_country.value] = str(countries)
                else:
                    record[ThreatDataFields.m_country.value] = 'Unknown'
            except Exception as e:
                print(f"  [DEBUG] Country extraction error: {e}")
                record[ThreatDataFields.m_country.value] = 'Unknown'
        
        # Set metadata
        record[ThreatDataFields.m_category.value] = 'ransomware'
        record[ThreatDataFields.m_status.value] = 'active'
        record[ThreatDataFields.m_scraped_date.value] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return record

    def parse_leak_data(self, writer=None) -> List[Dict[str, str]]:
        """
        Parse JSON file and extract all leak data records.
        
        Args:
            writer: Optional ThreatDataCSVWriter to write records immediately
            
        Returns:
            List of extracted and validated records
        """
        scraped = []

        print(f"[INFO] Reading JSON file: {self.json_file_path}")
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
        except Exception as e:
            print(f"[ERROR] Failed to read JSON file: {e}")
            return scraped

        # First, try to extract explicit leak_model(...) blocks from raw text
        blocks = self.find_leak_models_in_text(raw)
        leak_models: List[Dict[str, Any]] = []

        if blocks:
            print(f"[INFO] Found {len(blocks)} leak_model(...) blocks in raw file")
            for block in blocks:
                parsed = self.parse_leak_model_string(block)
                leak_models.append(parsed)
        else:
            # Fallback to JSON parsing / JSONL
            try:
                json_data = json.loads(raw)
            except json.JSONDecodeError:
                json_data = []
                for line in raw.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        json_data.append(obj)
                    except json.JSONDecodeError:
                        # treat as raw leak_model string
                        json_data.append(line)

            leak_models = self.parse_json_file(json_data)
            print(f"[INFO] Parsed {len(leak_models)} leak model entries via JSON/JSONL fallback")

        # Process each leak model
        for idx, leak_model in enumerate(leak_models, 1):
            try:
                print(f"\n[{idx}/{len(leak_models)}] Processing entry...")

                # Extract standardized record
                record = self.extract_from_leak_model(leak_model)

                # Validate record
                ok, missing = validate_record(record)
                if ok:
                    scraped.append(record)
                    if writer:
                        writer.write_row(record)
                    print(f"[{idx}] ✓ Extracted successfully")
                    print(f"  Company: {record.get(ThreatDataFields.m_company_name.value, 'N/A')}")
                    print(f"  Date: {record.get(ThreatDataFields.m_date.value, 'N/A')}")
                    print(f"  Industry: {record.get(ThreatDataFields.m_industry.value, 'N/A')}")
                    print(f"  Country: {record.get(ThreatDataFields.m_country.value, 'N/A')}")
                else:
                    print(f"[{idx}] ✗ Validation failed — missing: {missing}")

            except Exception as ex:
                print(f"[{idx}] ERROR: {ex}")
                import traceback
                traceback.print_exc()
                continue

        return scraped


def main():
    """Main function to run the JSON parser."""
    import argparse
    import tempfile

    # >>> Edit this variable to the full path of your JSON file if you want the script
    # to always use a specific file when run. Leave as empty string to use CLI/stdin.
    JSON_FILE_PATH = '/home/ibrahim-sayys/Projects/ThreatLens/Scraping_Sites_for_Threat_Intelligence_Model_taining_DS/sample_leak_data.json'
    # <<<

    parser = argparse.ArgumentParser(description='Parse JSON threat intelligence data with interactive field selection')
    parser.add_argument('json_file', nargs='?', help='Path to JSON file containing leak_model data')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: from config)',
                        default=OUTPUT_PATH)
    parser.add_argument('--no-interactive', action='store_true',
                        help='Skip interactive field selection and extract all fields')
    parser.add_argument('--fields', type=str,
                        help='Comma-separated field numbers (e.g., "1,2,5,9") to skip interactive prompt')

    args = parser.parse_args()

    # Determine JSON file path
    if JSON_FILE_PATH:
        json_file_path = JSON_FILE_PATH
    else:
        if not args.json_file or args.json_file == '-':
            print("[INFO] No json_file provided; reading JSON data from stdin...")
            try:
                stdin_bytes = sys.stdin.buffer.read()
                if not stdin_bytes:
                    print("[ERROR] No data received on stdin. Provide a file path or pipe JSON data into the script.")
                    return
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                tmp.write(stdin_bytes)
                tmp.close()
                json_file_path = tmp.name
            except Exception as e:
                print(f"[ERROR] Failed to read from stdin: {e}")
                return
        else:
            json_file_path = args.json_file

    if not os.path.exists(json_file_path):
        print(f"[ERROR] JSON file not found: {json_file_path}")
        return

    # Interactive field selection
    selected_field_names = []

    if args.fields:
        # Use fields from command line argument
        try:
            field_numbers = [int(x.strip()) for x in args.fields.split(',')]
            selected_field_names = [
                JSONDataParser.AVAILABLE_FIELDS[num][0]
                for num in field_numbers
                if num in JSONDataParser.AVAILABLE_FIELDS
            ]
            print(f"[INFO] Using fields from command line: {', '.join(selected_field_names)}")
        except Exception as e:
            print(f"[ERROR] Invalid field numbers: {e}")
            return
    elif not args.no_interactive:
        # Interactive mode - ask user to select fields
        JSONDataParser.display_available_fields()
        print("\nSelect which fields to extract from leak_model:")
        print("Enter field numbers separated by commas (e.g., 1,2,5,9)")
        print("Or press ENTER to extract ALL fields")

        user_input = input("\nYour selection: ").strip()

        if user_input:
            try:
                field_numbers = [int(x.strip()) for x in user_input.split(',')]
                selected_field_names = [
                    JSONDataParser.AVAILABLE_FIELDS[num][0]
                    for num in field_numbers
                    if num in JSONDataParser.AVAILABLE_FIELDS
                ]

                if not selected_field_names:
                    print("[ERROR] No valid field numbers provided")
                    return

                print(f"\n[INFO] Selected fields: {', '.join(selected_field_names)}")
            except ValueError:
                print("[ERROR] Invalid input. Please enter numbers separated by commas.")
                return
        else:
            print("[INFO] No selection made - extracting ALL fields")
    else:
        print("[INFO] Non-interactive mode - extracting ALL fields")

    # Create parser with selected fields
    json_parser = JSONDataParser(json_file_path, selected_fields=selected_field_names)

    try:
        # Determine write mode
        mode = 'a' if os.path.exists(args.output) else 'w'
        
        with ThreatDataCSVWriter(args.output, mode=mode) as writer:
            records = json_parser.parse_leak_data(writer)
            print(f"\n[SUCCESS] Processed {len(records)} records")
            print(f"[SUCCESS] Data {'appended to' if mode == 'a' else 'written to'} {args.output}")
    
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
