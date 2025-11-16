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

