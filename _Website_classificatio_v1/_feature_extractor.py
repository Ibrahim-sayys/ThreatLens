import csv
import requests
import re
import time
import logging
from collections import Counter
from bs4 import BeautifulSoup
import os
import argparse
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import NLTK stopwords; fall back to small builtin set if not available
try:
    from nltk.corpus import stopwords as nltk_stopwords
    _STOPWORDS = set(nltk_stopwords.words('english'))
except Exception:
    # Minimal fallback list (extend as needed)
    _STOPWORDS = {
        "the", "and", "for", "that", "with", "this", "from", "they", "have",
        "will", "your", "their", "what", "when", "were", "there", "which",
        "would", "could", "should", "about", "please", "other", "these"
    }

# Tor SOCKS proxy (requests[socks] must be installed)
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

DEFAULT_TIMEOUT = 30  # seconds

logger = logging.getLogger("feature_extractor")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
_handler.setFormatter(_formatter)
logger.addHandler(_handler)


def extract_text_from_html(html_content):
    """Return cleaned visible text from HTML (no scripts/styles)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style', 'noscript']):
        script_or_style.decompose()
    full_text = ' '.join(soup.stripped_strings)
    clean_text = ' '.join(full_text.split())
    return clean_text


_WORD_RE = re.compile(r'\b[a-zA-Z]{4,}\b')


def extract_keywords_with_frequency(text, num_keywords=10, stop_words=_STOPWORDS):
    """Return list of (keyword, freq) sorted by freq descending."""
    if not text:
        return []
    words = _WORD_RE.findall(text.lower())
    filtered_words = [w for w in words if w not in stop_words]
    if not filtered_words:
        return []
    word_counts = Counter(filtered_words)
    return word_counts.most_common(num_keywords)


def create_session(user_agent=None, retries=3, backoff_factor=0.3):
    """Create a requests.Session with retries and optional User-Agent."""
    session = requests.Session()
    ua = user_agent or "ThreatLensFeatureExtractor/0.1 (+https://example.edu/contact)"
    session.headers.update({"User-Agent": ua})
    session.proxies.update(PROXIES)
    retry = Retry(total=retries, backoff_factor=backoff_factor,
                  status_forcelist=(500, 502, 503, 504), allowed_methods=frozenset(['GET', 'POST']))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def normalize_url(url):
    """Basic normalization: add scheme if missing and validate."""
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        # assume http if no scheme provided (user should ideally include it)
        url = "http://" + url
        parsed = urlparse(url)
    if not parsed.netloc:
        return None
    return url


def process_urls(input_csv, output_csv, top_n_keywords=10, delay=0.0, user_agent=None, timeout=DEFAULT_TIMEOUT):
    """Read URLs from input_csv and write original rows plus keyword/freq columns to output_csv."""
    if not os.path.exists(input_csv):
        logger.error("Input file '%s' not found!", input_csv)
        return

    session = create_session(user_agent=user_agent)

    # read input
    with open(input_csv, 'r', encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    if not rows:
        logger.error("Input file '%s' is empty.", input_csv)
        return

    header = rows[0]
    data_rows = rows[1:]

    keyword_headers = []
    for i in range(1, top_n_keywords + 1):
        keyword_headers.append(f'keyword{i}')
        keyword_headers.append(f'freq{i}')
    extended_header = header + keyword_headers

    # write output incrementally to avoid data loss on crash
    with open(output_csv, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(extended_header)

        for index, row in enumerate(data_rows, start=1):
            # assume URL is first column; change if your CSV uses different layout
            url_raw = row[0] if len(row) > 0 else ""
            url = normalize_url(url_raw)
            logger.info("Processing link #%d: %s", index, url_raw)
            keyword_freq_pairs = ["" for _ in range(top_n_keywords * 2)]

            if url:
                try:
                    resp = session.get(url, timeout=timeout)
                    if resp.status_code == 200 and 'html' in (resp.headers.get('Content-Type') or '').lower():
                        clean_text = extract_text_from_html(resp.text)
                        top_keywords = extract_keywords_with_frequency(clean_text, top_n_keywords)
                        for i, (keyword, freq) in enumerate(top_keywords):
                            keyword_freq_pairs[i * 2] = keyword
                            keyword_freq_pairs[i * 2 + 1] = str(freq)
                    else:
                        logger.warning("Non-HTML or bad status for %s: status=%s, content-type=%s", url, resp.status_code, resp.headers.get('Content-Type'))
                except requests.exceptions.RequestException as e:
                    logger.warning("Error fetching %s: %s", url, str(e))
                # small politeness delay between requests (configurable)
                if delay and delay > 0:
                    time.sleep(delay)

            complete_row = row + keyword_freq_pairs
            writer.writerow(complete_row)

    logger.info("Keyword extraction completed. Results saved to '%s'.", output_csv)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default=os.path.join(os.path.dirname(__file__), 'input_data.csv'),
                   help="Path to input CSV (default is input_data.csv next to this script)")
    p.add_argument('--output', default=os.path.join(os.path.dirname(__file__), 'features_output_data.csv'),
                   help="Path to output CSV")
    p.add_argument('--topk', type=int, default=10, help="Number of keywords to extract")
    p.add_argument('--delay', type=float, default=1.0, help="Delay between requests (seconds)")
    p.add_argument('--user-agent', type=str, default=None, help="User-Agent header")
    p.add_argument('--timeout', type=int, default=30, help="Request timeout in seconds")
    args = p.parse_args()

    process_urls(args.input, args.output, top_n_keywords=args.topk, delay=args.delay, user_agent=args.user_agent, timeout=args.timeout)


if __name__ == "__main__":
    main()