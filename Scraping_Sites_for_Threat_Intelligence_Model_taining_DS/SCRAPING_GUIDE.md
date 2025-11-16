# Threat Intelligence Scraping Guide

## Overview
This guide explains how to use the standardized scraping schema for extracting threat intelligence data from multiple sites.

## Files Created

1. **`scraping_schema.py`** - Core schema definition file
   - Contains all field definitions (enums)
   - Provides CSV writer helper class
   - Ensures consistency across all scraping scripts

2. **`example_scraper_template.py`** - Template for creating new scrapers
   - Copy this for each new site you want to scrape
   - Customize the selectors based on the site structure

## Standard Fields Available

### Primary Fields
- `company_name` - Name of the affected company/organization
- `victim_name` - Alternative name for victim
- `organization` - Organization name

### Date Fields
- `breach_date` - When the breach occurred
- `publish_date` - When the information was published
- `discovery_date` - When the breach was discovered
- `scraped_date` - When you scraped the data (auto-added)

### Location Fields
- `country` - Country of the affected organization
- `region` - Region/state
- `city` - City

### Industry Information
- `industry` - Industry sector (e.g., Healthcare, Finance)
- `sector` - Specific sector

### Threat Information
- `threat_actor` - Name of threat actor
- `threat_group` - Threat group name
- `ransomware_group` - Ransomware group name
- `attack_type` - Type of attack (e.g., ransomware, phishing)
- `malware_family` - Malware family used

### Data Details
- `data_type` - Type of data stolen/leaked
- `data_size` - Size of data
- `records_affected` - Number of records affected
- `leak_size` - Size of the leak
- `leak_url` - URL to leaked data
- `download_link` - Download link for data

### Content Fields
- `description` - Description of the incident
- `summary` - Brief summary
- `full_text` - Full text content

### Source Information
- `source_url` - URL of the source (required)
- `source_title` - Title of the source page

### Metadata
- `category` - Category (ransomware, data_breach, etc.)
- `severity` - Severity level (critical, high, medium, low)
- `status` - Status (active, resolved, investigating, etc.)
- `tags` - Tags/keywords
- `post_id` - Post identifier

### Financial
- `ransom_amount` - Ransom amount demanded
- `ransom_paid` - Whether ransom was paid

## How to Create a New Scraper

### Step 1: Copy the Template
```bash
cp example_scraper_template.py custom_scripts/site_name_scraper.py
```

### Step 2: Configure the Script
Edit the configuration section:
```python
TARGET_URL = "http://your-site.onion"  # Your target URL
OUTPUT_CSV = "site_name_output.csv"     # Output filename
```

### Step 3: Customize the Scraping Logic
Update the selector logic based on your target site's HTML structure:

```python
# Find posts/cards (adjust selector)
posts = soup.find_all('div', class_='your-post-class')

for post in posts:
    record = create_empty_record()
    
    # Extract company name (adjust selector)
    company_elem = post.find('h2', class_='company-class')
    if company_elem:
        record[ThreatDataFields.COMPANY_NAME.value] = clean_newlines(company_elem.get_text())
    
    # Add more fields as needed...
```

### Step 4: Run Your Scraper
```bash
python custom_scripts/site_name_scraper.py
```

## Usage Examples

### Example 1: Using the CSV Writer Directly
```python
from scraping_schema import ThreatDataFields, ThreatDataCSVWriter, DataCategory

with ThreatDataCSVWriter('output.csv') as writer:
    writer.write_row({
        ThreatDataFields.COMPANY_NAME: "Example Corp",
        ThreatDataFields.BREACH_DATE: "2025-01-15",
        ThreatDataFields.COUNTRY: "USA",
        ThreatDataFields.INDUSTRY: "Healthcare",
        ThreatDataFields.THREAT_ACTOR: "APT29",
        ThreatDataFields.CATEGORY: DataCategory.RANSOMWARE.value,
        ThreatDataFields.DESCRIPTION: "Ransomware attack on healthcare provider",
    })
```

### Example 2: Scraping Multiple Records
```python
from scraping_schema import ThreatDataFields, ThreatDataCSVWriter, create_empty_record

data = []

# Scrape multiple records
for post in posts:
    record = create_empty_record()
    record[ThreatDataFields.COMPANY_NAME.value] = "Company Name"
    record[ThreatDataFields.COUNTRY.value] = "USA"
    # ... add more fields
    data.append(record)

# Write all at once
with ThreatDataCSVWriter('output.csv') as writer:
    writer.write_rows(data)
```

### Example 3: Appending to Existing CSV
```python
# Use mode='a' to append instead of overwrite
with ThreatDataCSVWriter('output.csv', mode='a') as writer:
    writer.write_row({
        ThreatDataFields.COMPANY_NAME: "Another Company",
        ThreatDataFields.BREACH_DATE: "2025-02-20",
    })
```

## Categories Available

- `RANSOMWARE` - Ransomware attacks
- `DATA_BREACH` - Data breaches
- `VULNERABILITY` - Vulnerability disclosures
- `MALWARE` - Malware incidents
- `PHISHING` - Phishing campaigns
- `DDoS` - DDoS attacks
- `INSIDER_THREAT` - Insider threats
- `APT` - Advanced Persistent Threats
- `OTHER` - Other types

## Severity Levels

- `CRITICAL` - Critical severity
- `HIGH` - High severity
- `MEDIUM` - Medium severity
- `LOW` - Low severity
- `UNKNOWN` - Unknown severity

## Status Values

- `ACTIVE` - Currently active threat
- `RESOLVED` - Resolved incident
- `INVESTIGATING` - Under investigation
- `CONFIRMED` - Confirmed incident
- `UNCONFIRMED` - Unconfirmed report
- `ARCHIVED` - Archived incident

## Tips for Scraping .onion Sites

1. **Make sure Tor is running** on port 9050
2. **Use the proxies configuration** provided in the template
3. **Set appropriate timeout** (30 seconds is good for .onion sites)
4. **Handle connection errors** gracefully (Tor can be slow)

## Required Fields

Every record MUST have these fields:
- `company_name` (or victim_name/organization)
- `source_url`
- `scraped_date` (auto-added if not provided)

## Best Practices

1. **Always use the schema fields** - Don't create custom field names
2. **Use helper methods** - Use `clean_newlines()` and `normalize_date()` from helper_methods
3. **Validate records** - Use `validate_record()` before writing
4. **Handle errors** - Wrap scraping in try-except blocks
5. **Test incrementally** - Start with one page before scaling
6. **Log everything** - Use print statements to track progress
7. **Respect rate limits** - Add delays between requests if needed

## Troubleshooting

### "No module named 'scraping_schema'"
Make sure you're running the script from the correct directory or adjust the import path.

### "Connection timeout"
- Check if Tor is running (for .onion sites)
- Increase TIMEOUT value
- Verify the target site is accessible

### "Missing required fields"
Use `validate_record()` to check which fields are missing:
```python
is_valid, missing = validate_record(record)
if not is_valid:
    print(f"Missing fields: {missing}")
```

## Output Format

All scrapers will produce CSV files with consistent columns in this order:
1. company_name
2. breach_date
3. publish_date
4. country
5. industry
6. threat_actor
7. ransomware_group
8. attack_type
9. data_type
10. data_size
11. records_affected
12. description
13. source_url
14. source_title
15. category
16. severity
17. status
18. leak_url
19. ransom_amount
20. scraped_date
21. tags

This ensures all your data can be easily merged and analyzed together!

