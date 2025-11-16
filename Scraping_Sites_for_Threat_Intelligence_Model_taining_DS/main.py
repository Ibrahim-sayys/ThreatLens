#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main controller for running threat intelligence scrapers.
This script orchestrates running individual scrapers and manages the shared CSV output.
"""

import os
import sys
from datetime import datetime
import importlib.util
from pathlib import Path
from config import OUTPUT_PATH, CUSTOM_SCRIPTS_DIR
from scraping_schema import ThreatDataCSVWriter, STANDARD_CSV_FIELDS


def initialize_csv():
    """Initialize the shared CSV file with headers if it doesn't exist"""
    if not os.path.exists(OUTPUT_PATH):
        print(f"[INFO] Initializing new CSV file: {OUTPUT_PATH}")
        # Create empty CSV with headers
        with ThreatDataCSVWriter(OUTPUT_PATH, mode='w') as writer:
            pass  # Just create the file with headers
        print(f"[SUCCESS] CSV file created with standard headers")
    else:
        print(f"[INFO] Using existing CSV file: {OUTPUT_PATH}")


def get_available_scrapers():
    """
    Get list of available scraper scripts from Custom_Scripts folder.

    Returns:
        List of tuples (script_name, script_path)
    """
    scrapers = []
    scripts_dir = Path(CUSTOM_SCRIPTS_DIR)

    if not scripts_dir.exists():
        print(f"[WARNING] Custom_Scripts directory not found: {CUSTOM_SCRIPTS_DIR}")
        return scrapers

    for script_file in scripts_dir.glob("*.py"):
        # Skip __init__.py only
        if script_file.name == '__init__.py':
            continue

        scrapers.append((script_file.stem, str(script_file)))

    return sorted(scrapers)


def load_scraper_module(script_path):
    """
    Dynamically load a scraper module.

    Args:
        script_path: Path to the scraper script

    Returns:
        The loaded module
    """
    spec = importlib.util.spec_from_file_location("scraper_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_scraper(script_name, script_path):
    """
    Run a single scraper script.

    Args:
        script_name: Name of the scraper
        script_path: Path to the scraper script

    Returns:
        Number of records scraped
    """
    print(f"\n{'#'*70}")
    print(f"# Running Scraper: {script_name}")
    print(f"{'#'*70}\n")

    try:
        # Load the scraper module
        module = load_scraper_module(script_path)

        # Check if module has a main function
        if hasattr(module, 'main'):
            module.main()
            return True
        else:
            print(f"[WARNING] Scraper '{script_name}' has no main() function")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to run scraper '{script_name}': {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_scrapers():
    """Run all available scrapers sequentially"""
    scrapers = get_available_scrapers()

    if not scrapers:
        print("[WARNING] No scrapers found in Custom_Scripts folder")
        return

    print(f"[INFO] Found {len(scrapers)} scraper(s)")

    results = []
    for script_name, script_path in scrapers:
        success = run_scraper(script_name, script_path)
        results.append((script_name, success))

    # Print summary
    print(f"\n{'='*70}")
    print("SCRAPING SUMMARY")
    print(f"{'='*70}")
    for script_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {script_name}")
    print(f"{'='*70}\n")


def run_specific_scraper(scraper_name):
    """
    Run a specific scraper by name.

    Args:
        scraper_name: Name of the scraper (without .py extension)
    """
    scrapers = get_available_scrapers()
    scraper_dict = {name: path for name, path in scrapers}

    if scraper_name not in scraper_dict:
        print(f"[ERROR] Scraper '{scraper_name}' not found")
        print(f"Available scrapers: {', '.join(scraper_dict.keys())}")
        return

    run_scraper(scraper_name, scraper_dict[scraper_name])


def show_menu():
    """Display interactive menu"""
    scrapers = get_available_scrapers()

    print("\n" + "="*70)
    print("THREAT INTELLIGENCE SCRAPER - MAIN MENU")
    print("="*70)
    print(f"\nShared CSV Output: {OUTPUT_PATH}")
    print(f"\nAvailable Scrapers ({len(scrapers)}):")

    if not scrapers:
        print("  (No scrapers found in Custom_Scripts folder)")
    else:
        for idx, (name, _) in enumerate(scrapers, 1):
            print(f"  {idx}. {name}")

    print("\nOptions:")
    print("  [A] Run ALL scrapers")
    print("  [1-9] Run specific scraper by number")
    print("  [Q] Quit")
    print("="*70)


def interactive_mode():
    """Run in interactive mode with menu"""
    initialize_csv()

    while True:
        show_menu()
        choice = input("\nEnter your choice: ").strip().upper()

        if choice == 'Q':
            print("\n[INFO] Exiting...")
            break
        elif choice == 'A':
            run_all_scrapers()
            input("\nPress Enter to continue...")
        elif choice.isdigit():
            scrapers = get_available_scrapers()
            idx = int(choice) - 1
            if 0 <= idx < len(scrapers):
                script_name, script_path = scrapers[idx]
                run_scraper(script_name, script_path)
                input("\nPress Enter to continue...")
            else:
                print("[ERROR] Invalid scraper number")
                input("Press Enter to continue...")
        else:
            print("[ERROR] Invalid choice")
            input("Press Enter to continue...")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("THREAT INTELLIGENCE SCRAPER CONTROLLER")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Initialize CSV
    initialize_csv()

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'all':
            run_all_scrapers()
        elif command == 'list':
            scrapers = get_available_scrapers()
            print("\nAvailable scrapers:")
            for name, _ in scrapers:
                print(f"  - {name}")
        elif command == 'run' and len(sys.argv) > 2:
            scraper_name = sys.argv[2]
            run_specific_scraper(scraper_name)
        else:
            print("Usage:")
            print("  python main.py              # Interactive mode")
            print("  python main.py all          # Run all scrapers")
            print("  python main.py list         # List available scrapers")
            print("  python main.py run <name>   # Run specific scraper")
    else:
        # No arguments - run in interactive mode
        interactive_mode()

    print(f"\n[INFO] All data saved to: {OUTPUT_PATH}")
    print("[INFO] Done!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for threat intelligence scraping.
Contains shared settings like proxy, timeout, output file, etc.
"""

import os

# --- Output Configuration ---
# Single CSV file where ALL scraped data will be appended
OUTPUT_CSV = "threat_intelligence_data.csv"

# --- Network Configuration ---
TIMEOUT = 30  # Maximum wait time for a site to load (seconds)
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# --- Tor/SOCKS Proxy Configuration ---
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
USE_TOR_BY_DEFAULT = True  # Set to True to use Tor for all requests

# Proxy dictionary for requests
PROXIES = {
    "http": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
    "https": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
}

# --- Scraping Configuration ---
DELAY_BETWEEN_REQUESTS = 1  # Seconds to wait between requests (be nice to servers)
MAX_RETRIES = 3  # Number of times to retry failed requests

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_SCRIPTS_DIR = os.path.join(BASE_DIR, "Custom_Scripts")
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_CSV)

