# Interactive Field Selection - Quick Guide

## ✨ New Feature: Dynamic Field Selection

The JSON parser now supports **interactive field selection**! When you run it, the script will:
1. Show you all available fields from leak_model
2. Ask which fields you want to extract
3. Only process the fields you selected

## 🎯 How to Use

### Method 1: Interactive Mode (Recommended)

Just run the script:

```bash
python Custom_Scripts/_json_data_parser.py
```

You'll see this menu:

```
============================================================
Available leak_model fields:
============================================================
   1. m_title              - Company/Title name
   2. m_ref_html           - Reference HTML
   3. m_url                - Source URL
   4. m_base_url           - Base URL
   5. m_content            - Main content/description
   6. m_screenshot         - Screenshot URL
   7. m_network            - Network type (e.g., onion)
   8. m_important_content  - Important content
   9. m_weblink            - Website links
  10. m_dumplink           - Download/dump links
  11. m_content_type       - Content type
  12. m_leak_date          - Leak date
  13. m_revenue            - Company revenue
  14. m_data_size          - Data size
============================================================

Select which fields to extract from leak_model:
Enter field numbers separated by commas (e.g., 1,2,5,9)
Or press ENTER to extract ALL fields

Your selection: 
```

**Example inputs:**

- Type `1,5,9,10,12` to extract only: title, content, weblink, dumplink, and leak_date
- Type `1,2,3,4,5` to extract first 5 fields
- Press ENTER to extract ALL fields

### Method 2: Command Line with Field Numbers

Skip the interactive prompt by specifying fields directly:

```bash
# Extract only fields 1, 5, 9, 10, 12
python Custom_Scripts/_json_data_parser.py --fields "1,5,9,10,12"

# With custom output file
python Custom_Scripts/_json_data_parser.py --fields "1,5,9,12" -o my_output.csv
```

### Method 3: Non-Interactive (Extract All Fields)

```bash
python Custom_Scripts/_json_data_parser.py --no-interactive
```

## 📋 Field Mapping Reference

| # | leak_model Field | CSV Output Field | Description |
|---|------------------|------------------|-------------|
| 1 | `m_title` | company_name | Company/victim name |
| 2 | `m_ref_html` | (internal) | Reference HTML |
| 3 | `m_url` | source_url | Source URL of the leak post |
| 4 | `m_base_url` | source_url | Base URL (fallback) |
| 5 | `m_content` | content | Main description/details |
| 6 | `m_screenshot` | image_url | Screenshot URL |
| 7 | `m_network` | tags | Network type (e.g., onion) |
| 8 | `m_important_content` | content | Important content (fallback) |
| 9 | `m_weblink` | website | Company website |
| 10 | `m_dumplink` | download_link | Download/dump links |
| 11 | `m_content_type` | (internal) | Content type |
| 12 | `m_leak_date` | date | Leak date (auto-normalized) |
| 13 | `m_revenue` | revenue | Company revenue |
| 14 | `m_data_size` | leak_size | Size of leaked data |

## 🎬 Example Session

```bash
$ python Custom_Scripts/_json_data_parser.py

============================================================
Available leak_model fields:
============================================================
   1. m_title              - Company/Title name
   2. m_ref_html           - Reference HTML
   3. m_url                - Source URL
   4. m_base_url           - Base URL
   5. m_content            - Main content/description
   6. m_screenshot         - Screenshot URL
   7. m_network            - Network type (e.g., onion)
   8. m_important_content  - Important content
   9. m_weblink            - Website links
  10. m_dumplink           - Download/dump links
  11. m_content_type       - Content type
  12. m_leak_date          - Leak date
  13. m_revenue            - Company revenue
  14. m_data_size          - Data size
============================================================

Select which fields to extract from leak_model:
Enter field numbers separated by commas (e.g., 1,2,5,9)
Or press ENTER to extract ALL fields

Your selection: 1,5,9,10,12,13

[INFO] Selected fields: m_title, m_content, m_weblink, m_dumplink, m_leak_date, m_revenue
[INFO] Reading JSON file: .../sample_leak_data.json
[INFO] Found 1 leak_model(...) blocks in raw file

[1/1] Processing entry...
  [DEBUG] Extracted departments: ['Finance', 'HR']
  [DEBUG] Extracted industry: 'Government and Public Sector'
  [DEBUG] Extracted countries: ['Sweden']
[1] ✓ Extracted successfully
  Company: Swedish Arts Council
  Date: 31/10/2025
  Industry: Government and Public Sector
  Country: Sweden

[SUCCESS] Processed 1 records
[SUCCESS] Data written to threat_intelligence_data.csv
```

## 🔧 Common Use Cases

### Case 1: Extract Only Basic Info
```bash
# Fields: title, content, date
python Custom_Scripts/_json_data_parser.py --fields "1,5,12"
```

### Case 2: Extract Financial Data
```bash
# Fields: title, revenue, data_size, date
python Custom_Scripts/_json_data_parser.py --fields "1,13,14,12"
```

### Case 3: Extract Technical Details
```bash
# Fields: title, url, content, weblink, dumplink
python Custom_Scripts/_json_data_parser.py --fields "1,3,5,9,10"
```

### Case 4: Extract Everything
```bash
# Press ENTER when prompted, or use:
python Custom_Scripts/_json_data_parser.py --no-interactive
```

## 💡 Tips

1. **Always include field 1 (m_title)** - It's mapped to company_name which is required
2. **Field 5 (m_content)** is important - It's used by helper extractors for industry/country/departments
3. **Field 12 (m_leak_date)** is auto-normalized to DD/MM/YYYY format
4. **If you select neither field 3 nor 4**, source_url might be empty (validation might fail)

## 🚀 Advanced: Programmatic Usage

```python
from Custom_Scripts._json_data_parser import JSONDataParser
from scraping_schema import ThreatDataCSVWriter

# Select specific fields
selected = ['m_title', 'm_content', 'm_weblink', 'm_leak_date']
parser = JSONDataParser('data.json', selected_fields=selected)

with ThreatDataCSVWriter('output.csv', mode='w') as writer:
    records = parser.parse_leak_data(writer)
    print(f"Processed {len(records)} records")
```

## 📝 Notes

- If you don't select any fields (press ENTER), ALL fields will be extracted
- The script will always extract helper-derived fields (industry, country, data_type) if content is available
- Dates are always normalized even if not explicitly selected
- The interactive prompt only appears if you don't use `--fields` or `--no-interactive`

---

**Now you have full control over what data gets extracted!** 🎉

