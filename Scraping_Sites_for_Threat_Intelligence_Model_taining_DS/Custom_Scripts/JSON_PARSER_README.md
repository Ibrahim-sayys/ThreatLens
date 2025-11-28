# JSON Data Parser for Threat Intelligence

This script parses JSON file data with `leak_model` format and extracts threat intelligence information into standardized CSV format.

## Features

- Parses `leak_model` string format from JSON files
- Extracts company name, dates, revenue, download links, and more
- Uses helper methods to automatically extract:
  - **Departments/Data Types** (using SpacyDepartmentExtractor)
  - **Industry** (using IndustryClassifier)
  - **Country** (using country extractor)
- Validates records before writing
- Appends to existing CSV or creates new one
- Supports multiple JSON formats: single object, array, or JSONL

## Field Mapping

| Source Field | Target CSV Field | Extraction Method |
|-------------|------------------|-------------------|
| `m_title` | `company_name` | Direct |
| `m_content` | `content` | Direct (cleaned) |
| `m_leak_date` | `date` | Date parsing |
| `m_weblink[0]` | `website` | First item from list |
| `m_revenue` | `revenue` | Direct |
| `m_dumplink` | `download_link` | Join list with commas |
| `m_data_size` | `leak_size` | Direct (if not "Unknown") |
| `m_url` | `source_url` | Direct |
| `m_content` | `data_type` | Extracted via breach_dept |
| `m_content` | `industry` | Extracted via industry classifier |
| `m_content` | `country` | Extracted via country extractor |

## Usage

### Command Line

```bash
# Parse a JSON file and output to default CSV
python _json_data_parser.py path/to/your_data.json

# Parse and specify custom output file
python _json_data_parser.py path/to/your_data.json -o custom_output.csv

# Example with sample data
python _json_data_parser.py ../sample_leak_data.json
```

### As a Module

```python
from _json_data_parser import JSONDataParser
from scraping_schema import ThreatDataCSVWriter

# Initialize parser
parser = JSONDataParser("your_data.json")

# Parse and write to CSV
with ThreatDataCSVWriter("output.csv", mode='w') as writer:
    records = parser.parse_leak_data(writer)
    print(f"Processed {len(records)} records")
```

## Input Format

The script supports multiple JSON formats:

### 1. Array of leak_model strings
```json
[
  "leak_model(m_title='Company A', m_content='...', ...)",
  "leak_model(m_title='Company B', m_content='...', ...)"
]
```

### 2. JSONL (one leak_model per line)
```
leak_model(m_title='Company A', m_content='...', ...)
leak_model(m_title='Company B', m_content='...', ...)
```

### 3. Dictionary format (if already parsed)
```json
{
  "m_title": "Company Name",
  "m_content": "Description...",
  "m_leak_date": "2025-10-31",
  "m_weblink": ["https://example.com"],
  "m_revenue": "21.7 M$"
}
```

## Example leak_model Format

```
leak_model(
  m_ref_html=None, 
  m_title='Swedish Arts Council', 
  m_url='http://example.onion/r/abc123', 
  m_base_url='http://example.onion', 
  m_content='Company description with employee count: 150', 
  m_important_content='Same or additional content', 
  m_network='onion', 
  m_section=[], 
  m_content_type=['leaks'], 
  m_screenshot='', 
  m_weblink=['https://www.example.com/'], 
  m_dumplink=['http://dump.onion/file.zip'], 
  m_websites=[], 
  m_logo_or_images=[], 
  m_leak_date=datetime.date(2025, 10, 31), 
  m_data_size='Unknown', 
  m_revenue='21.7 M$'
)
```

## Output

The script outputs to CSV with the following standardized fields:
- company_name
- date (from m_leak_date)
- country (extracted from content)
- industry (extracted from content)
- data_type (extracted departments from content)
- content
- website (from m_weblink)
- revenue
- download_link (from m_dumplink)
- leak_size (from m_data_size)
- source_url
- category (set to 'ransomware')
- status (set to 'active')
- scraped_date (current timestamp)
- ...and other standard fields

## Requirements

The script requires the following helper methods (already in the project):
- `SpacyDepartmentExtractor` - Extracts departments/data types from text
- `IndustryClassifier` - Classifies text into industry categories
- `extract_countries` - Extracts country names from text
- `clean_newlines` - Cleans up text formatting

## Notes

- The script automatically appends to existing CSV files (or creates new ones)
- All records are validated before being written
- Debug output shows extraction progress and results
- If extraction fails for optional fields, defaults are used:
  - data_type: 'Unknown'
  - industry: 'Generic'
  - country: 'Unknown'

## Troubleshooting

If you encounter errors:

1. **Import errors**: Ensure helper_methods modules are in the Python path
2. **Parsing errors**: Check JSON format - the script handles multiple formats
3. **Missing fields**: Check validation output - only company_name, source_url, and scraped_date are required
4. **spaCy model missing**: The script will auto-download `en_core_web_sm` if needed

## Example Output

```
[INFO] Reading JSON file: sample_leak_data.json
[INFO] Found 1 leak model entries

[1/1] Processing entry...
  [DEBUG] Extracted departments: ['Finance', 'HR']
  [DEBUG] Extracted industry: 'Government'
  [DEBUG] Extracted countries: ['Sweden']
[1] ✓ Extracted successfully
  Company: Swedish Arts Council
  Date: 2025-10-31
  Industry: Government
  Country: Sweden

[SUCCESS] Processed 1 records
[SUCCESS] Data written to threat_intelligence_data.csv
```

