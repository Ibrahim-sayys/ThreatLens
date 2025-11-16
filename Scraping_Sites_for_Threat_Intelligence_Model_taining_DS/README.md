# Threat Intelligence Scraper System

## 🎯 Overview
This is a modular threat intelligence scraping system with:
- **Single shared CSV** for all scraped data
- **Centralized configuration** for proxy/network settings
- **Simple scraper creation** - just define TARGET_URL and parsing logic
- **Main controller** to run scrapers individually or all at once

## 📁 Project Structure

```
Scraping_Sites_for_Threat_Intelligence_Model_taining_DS/
├── main.py                      # Main controller - run this!
├── config.py                    # Shared configuration (proxy, timeout, CSV path)
├── scraper_base.py              # Base scraper class with HTTP/CSV handling
├── scraping_schema.py           # Field definitions and enums
├── threat_intelligence_data.csv # OUTPUT: Single CSV with all data
└── Custom_Scripts/              # Your individual site scrapers go here
    ├── example_site_scraper.py  # Template to copy for new sites
    └── [your_scrapers].py       # Add more scrapers here
```

## 🚀 Quick Start

### 1. Run the Main Controller

**Interactive Mode:**
```bash
python main.py
```

**Run All Scrapers:**
```bash
python main.py all
```

**List Available Scrapers:**
```bash
python main.py list
```

**Run Specific Scraper:**
```bash
python main.py run example_site_scraper
```

### 2. Create a New Scraper

Copy the template:
```bash
cp Custom_Scripts/example_site_scraper.py Custom_Scripts/my_new_site_scraper.py
```

Edit `my_new_site_scraper.py`:

```python
# 1. Set the target URL
TARGET_URL = "http://your-site.onion"

# 2. Customize the parse_leak_data() method
class MySiteScraper(BaseScraper):
    def parse_leak_data(self, soup):
        scraped_data = []
        
        # Find posts based on your site's HTML structure
        posts = soup.find_all('div', class_='your-class')
        
        for post in posts:
            record = create_empty_record()
            
            # Extract fields
            record[ThreatDataFields.COMPANY_NAME.value] = post.find('h2').get_text()
            record[ThreatDataFields.COUNTRY.value] = post.find('span', class_='country').get_text()
            # ... add more fields
            
            record[ThreatDataFields.SOURCE_URL.value] = self.target_url
            
            scraped_data.append(record)
        
        return scraped_data

# 3. Done! The rest is handled automatically
```

That's it! The framework handles:
- ✅ HTTP requests with Tor proxy
- ✅ Retries and timeouts
- ✅ CSV writing and appending
- ✅ Field validation

## 📝 Configuration

Edit `config.py` to change settings:

```python
# Output file (single CSV for all data)
OUTPUT_CSV = "threat_intelligence_data.csv"

# Network settings
TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Tor/SOCKS proxy
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
USE_TOR_BY_DEFAULT = True  # Use Tor for all requests
```

## 🔧 How It Works

### 1. Main Controller (`main.py`)
- Initializes the shared CSV file
- Discovers all scrapers in `Custom_Scripts/`
- Runs scrapers individually or all at once
- Provides interactive menu

### 2. Base Scraper (`scraper_base.py`)
- Handles HTTP requests (with Tor proxy support)
- Manages retries and timeouts
- Writes to shared CSV (append mode)
- Provides `parse_leak_data()` method for you to implement

### 3. Individual Scrapers (`Custom_Scripts/*.py`)
- Inherit from `BaseScraper`
- Define `TARGET_URL`
- Implement `parse_leak_data(soup)` with site-specific parsing
- That's all!

## 📊 Available Fields

Use these standardized fields in your scrapers:

### Core Fields
```python
ThreatDataFields.COMPANY_NAME       # Victim company name
ThreatDataFields.BREACH_DATE        # When breach occurred
ThreatDataFields.COUNTRY            # Country
ThreatDataFields.INDUSTRY           # Industry/sector
ThreatDataFields.THREAT_ACTOR       # Threat actor name
ThreatDataFields.RANSOMWARE_GROUP   # Ransomware group
ThreatDataFields.DESCRIPTION        # Description
ThreatDataFields.SOURCE_URL         # Source URL (required)
# ... and many more (see scraping_schema.py)
```

### Categories & Status
```python
DataCategory.RANSOMWARE      # Ransomware
DataCategory.DATA_BREACH     # Data breach
DataCategory.MALWARE         # Malware

SeverityLevel.CRITICAL       # Critical
SeverityLevel.HIGH           # High

IncidentStatus.ACTIVE        # Active
IncidentStatus.RESOLVED      # Resolved
```

## 💡 Example Scraper

```python
#!/usr/bin/env python3
import sys
sys.path.append('..')

from scraper_base import BaseScraper, ThreatDataFields, create_empty_record
from scraping_schema import DataCategory

TARGET_URL = "http://ransomware-site.onion"

class RansomSiteScraper(BaseScraper):
    def parse_leak_data(self, soup):
        scraped_data = []
        
        # Find all victim posts
        posts = soup.find_all('div', class_='victim-card')
        
        for post in posts:
            record = create_empty_record()
            
            # Extract data based on site structure
            record[ThreatDataFields.COMPANY_NAME.value] = post.find('h3').get_text().strip()
            record[ThreatDataFields.COUNTRY.value] = post.find('span', class_='country').get_text()
            record[ThreatDataFields.DESCRIPTION.value] = post.find('p').get_text().strip()
            record[ThreatDataFields.SOURCE_URL.value] = self.target_url
            record[ThreatDataFields.CATEGORY.value] = DataCategory.RANSOMWARE.value
            
            scraped_data.append(record)
        
        return scraped_data

def main():
    scraper = RansomSiteScraper(TARGET_URL)
    scraper.run()

if __name__ == "__main__":
    main()
```

## 🎯 Benefits of This Structure

1. **Single CSV Output** - All data in one place: `threat_intelligence_data.csv`
2. **No Proxy Config in Scrapers** - All in `config.py`
3. **Simple Scrapers** - Just URL + parsing logic
4. **Automatic Handling** - HTTP, retries, CSV writing all done for you
5. **Easy to Extend** - Copy template, customize parsing, done!
6. **Centralized Control** - Run all scrapers from one command

## 🔍 Helper Functions Available

```python
# Clean text
clean_newlines(text)  # Remove extra whitespace/newlines

# Normalize dates
normalize_date("Jan 15, 2025")  # Returns: "2025-01-15"

# Create empty record
record = create_empty_record()

# Validate record
is_valid, missing = validate_record(record)
```

## 📌 Important Notes

1. **Tor Required for .onion Sites** - Make sure Tor is running on port 9050
2. **All Data Appends** - The CSV grows with each scraper run
3. **Required Fields** - Every record must have `company_name` and `source_url`
4. **Scraper Naming** - Name files descriptively: `lockbit_scraper.py`, `conti_scraper.py`, etc.

## 🐛 Troubleshooting

**"No module named 'config'"**
- Make sure you're running from the correct directory
- Or add `sys.path.append('..')` to your scraper

**"Timeout after 30 seconds"**
- Check if Tor is running: `curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org`
- Increase TIMEOUT in `config.py`

**"No data scraped"**
- Check your CSS selectors match the site structure
- Print `soup` to debug: `print(soup.prettify())`

## 📚 Next Steps

1. Copy `Custom_Scripts/example_site_scraper.py` for each new site
2. Update `TARGET_URL` and parsing logic
3. Run with `python main.py`
4. All data accumulates in `threat_intelligence_data.csv`

Happy scraping! 🚀

