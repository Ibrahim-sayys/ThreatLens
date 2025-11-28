# JSON Data Parser - Quick Start Guide

## What Was Fixed

### Issue 1: Only Processing Last Entry
**Problem**: The original parser was only extracting the last entry from JSON files with multiple leak_model entries.

**Solution**: Added `find_leak_models_in_text()` method that uses balanced parentheses parsing to extract ALL `leak_model(...)` blocks from the input file, regardless of JSON structure.

### Issue 2: Date Not Normalized
**Problem**: Dates were stored in raw format (e.g., "2025-10-31") instead of normalized DD/MM/YYYY format.

**Solution**: Integrated `smart_date_parse()` from `helper_methods/_date_Normalizer.py` to normalize all dates to DD/MM/YYYY format.

## How to Use

### Method 1: Set JSON Path in Code (Recommended for Repeated Use)

1. Open `Custom_Scripts/_json_data_parser.py`
2. Find line ~424 with `JSON_FILE_PATH = ''`
3. Set your JSON file path:
   ```python
   JSON_FILE_PATH = '/path/to/your/leak_data.json'
   ```
4. Run the script:
   ```bash
   python Custom_Scripts/_json_data_parser.py
   ```

**Currently configured path**:
```python
JSON_FILE_PATH = '/home/ibrahim-sayys/Projects/ThreatLens/Scraping_Sites_for_Threat_Intelligence_Model_taining_DS/sample_leak_data.json'
```

### Method 2: Command Line Arguments

```bash
# Parse specific JSON file
python Custom_Scripts/_json_data_parser.py /path/to/leak_data.json

# Parse and specify custom output
python Custom_Scripts/_json_data_parser.py /path/to/leak_data.json -o custom_output.csv

# Read from stdin
cat leak_data.json | python Custom_Scripts/_json_data_parser.py -o output.csv
```

## What the Script Does

1. **Reads JSON file** containing leak_model entries
2. **Extracts all entries** using balanced parentheses parsing (not just the last one!)
3. **Parses each leak_model** and extracts:
   - Company name (from `m_title`)
   - Date (from `m_leak_date`) - **normalized to DD/MM/YYYY**
   - Content (from `m_content`)
   - Website (from `m_weblink[0]`)
   - Revenue (from `m_revenue`)
   - Download links (from `m_dumplink`)
   - Employee count (extracted from content)
   
4. **Uses helper methods** to extract:
   - **Departments/Data Types** (via `SpacyDepartmentExtractor`)
   - **Industry** (via `IndustryClassifier`)
   - **Country** (via `extract_countries`)

5. **Writes to CSV** with all standardized fields

## Example Input

```json
[
  "leak_model(m_title='Swedish Arts Council', m_leak_date=datetime.date(2025, 10, 31), m_content='Government agency...', m_weblink=['https://www.kulturradet.se/'], m_dumplink=['http://dump.onion/'], m_revenue='21.7 M$')",
  "leak_model(m_title='Another Company', m_leak_date=datetime.date(2025, 11, 15), ...)"
]
```

## Example Output

CSV with fields:
- company_name: "Swedish Arts Council"
- date: "31/10/2025" (normalized!)
- country: "Sweden" (extracted)
- industry: "Government and Public Sector" (extracted)
- data_type: "Finance, HR" (extracted)
- content: "Government agency that promotes..."
- website: "https://www.kulturradet.se/"
- revenue: "21.7 M$"
- download_link: "http://dump.onion/"
- source_url: "http://zohlm7ahjwegcedoz7lrdrti7bvpofymcayotp744qhx6gjmxbuo2yid.onion/r/..."
- category: "ransomware"
- status: "active"
- scraped_date: "27/11/2025 15:30:45"

## Output File

By default, output goes to: `threat_intelligence_data.csv` (from config)

**Output mode**:
- If CSV exists: **APPEND** mode (adds new records)
- If CSV doesn't exist: **WRITE** mode (creates new file)

## Debug Output

The script prints detailed debug information:
```
[INFO] Reading JSON file: /path/to/file.json
[INFO] Found 2 leak_model(...) blocks in raw file

[1/2] Processing entry...
  [DEBUG] Extracted departments: ['Finance', 'HR']
  [DEBUG] Extracted industry: 'Government and Public Sector'
  [DEBUG] Extracted countries: ['Sweden']
[1] ✓ Extracted successfully
  Company: Swedish Arts Council
  Date: 31/10/2025
  Industry: Government and Public Sector
  Country: Sweden

[2/2] Processing entry...
...

[SUCCESS] Processed 2 records
[SUCCESS] Data written to threat_intelligence_data.csv
```

## Supported Input Formats

1. **JSON array of leak_model strings** (most common)
2. **JSONL** (one leak_model per line)
3. **Dictionary objects** (if already parsed)
4. **Raw text** with embedded `leak_model(...)` blocks

## Notes

- The script now extracts **ALL** leak_model entries from the file, not just the last one
- Dates are automatically normalized using the date normalizer helper
- Helper methods (SpaCy, Industry Classifier) may download models on first run
- Static import warnings in IDE are normal - handled by runtime fallback code

## Troubleshooting

**"Only processing last entry"**: Fixed! The new `find_leak_models_in_text()` extracts all entries.

**"Date not normalized"**: Fixed! Now uses `smart_date_parse()` for all dates.

**"AI/ML dependencies found"**: Normal message from industry classifier - not an error.

**"Downloading spaCy model"**: First-run only - SpaCy downloads `en_core_web_sm` model.

**Import errors**: The script has fallback imports - it will work at runtime even if IDE shows warnings.

