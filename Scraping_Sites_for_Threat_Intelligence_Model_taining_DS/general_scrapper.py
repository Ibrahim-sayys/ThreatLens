#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, UTC
from urllib.parse import urljoin, urlparse
import requests

# import helper_methods
from helper_methods._string_cleaner import clean_newlines
from helper_methods._date_Normalizer import normalize_date

# --- Tor integration ---
try:
    from stem.process import launch_tor_with_config
    STEM_AVAILABLE = True
except Exception:
    STEM_AVAILABLE = False

TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
PROXIES = {
    "http": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
    "https": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
}
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
INPUT_CSV = "testing_input_urls.csv"
OUTPUT_JSONL = "output.jsonl"

# --- File extensions to ignore ---
SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff", ".jfif", ".pjpeg", ".pjp", ".avif",
    ".pdf", ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp4", ".mp3", ".wav", ".ogg", ".avi", ".mov"
)

# --- Common post path words and button classes ---
POST_PATH_WORDS = ['post', 'posts', 'card', 'cards', 'news', 'article', 'articles', 'blog', 'entry', 'item', 'coos', 'more-info']
POST_LINK_CLASSES = ['more-info-link', 'read-more', 'btn', 'article-link', 'card-link']

DATE_REGEX = re.compile(
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|"
    r"\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{2,4})",
    flags=re.IGNORECASE
)

def start_tor_if_needed():
    print("[STEP] Checking Tor availability...")
    sess = requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    sess.proxies.update(PROXIES)
    try:
        resp = sess.get("http://httpbin.org/ip", timeout=5)
        print("[TOR] Detected running Tor proxy:", resp.text)
        return None
    except Exception:
        pass
    if not STEM_AVAILABLE:
        print("[TOR] Tor not running and stem unavailable.")
        return None
    print("[TOR] Launching Tor via stem...")
    try:
        tor_process = launch_tor_with_config(
            config={"SOCKSPort": str(TOR_SOCKS_PORT), "Log": "notice stdout"},
            take_ownership=True,
            timeout=60
        )
        print("[TOR] Tor started successfully.")
        return tor_process
    except Exception as e:
        print(f"[TOR] Could not start Tor: {e}", file=sys.stderr)
        return None

def read_urls(csv_path):
    print(f"[STEP] Reading URLs from {csv_path}...")
    urls = []
    if not os.path.exists(csv_path):
        print(f"[IO] Input CSV not found: {csv_path}", file=sys.stderr)
        return urls
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                url = row[0].strip()
                if url.lower().startswith(("http://", "https://")) or url.endswith(".onion"):
                    urls.append(url)
                    print(f"[CSV] Found URL: {url}")
    return urls

def clean_soup(soup):
    for tag in soup(["script", "style", "noscript", "iframe", "canvas", "svg"]):
        tag.decompose()
    return soup

def is_internal_link(url, base_url):
    parsed_abs = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_abs.netloc == parsed_base.netloc or (parsed_abs.netloc == '' and parsed_base.netloc != '')

def is_post_like_path(path):
    return any(word in path.lower() for word in POST_PATH_WORDS)

def is_skip_ext(url):
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTENSIONS)

def url_equivalent(u1, u2):
    # Remove trailing slashes for comparison
    return u1.rstrip('/') == u2.rstrip('/')

def is_post_like_path(path, query):
    # Match classic post/card/news/article/etc. in path
    if any(word in path.lower() for word in POST_PATH_WORDS):
        return True
    # Match URLs with uuid/id as query param (for detail pages)
    if re.search(r"(uuid=|id=|post=|item=)[a-zA-Z0-9\-]+", query):
        return True
    return False

def extract_post_links(soup, base_url):
    print(f"[STEP] Extracting post links from {base_url}...")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if is_skip_ext(abs_url):
            continue
        if not is_internal_link(abs_url, base_url):
            continue
        if is_post_like_path(parsed.path, parsed.query):
            if not url_equivalent(abs_url, base_url):
                print(f"[LINK] Found post-like path or query: {abs_url}")
                links.add(abs_url)
            else:
                print(f"[SKIP] Ignoring base_url: {abs_url}")
    for cls in POST_LINK_CLASSES:
        for a in soup.find_all("a", href=True, class_=re.compile(cls)):
            abs_url = urljoin(base_url, a["href"].strip())
            if not url_equivalent(abs_url, base_url):
                print(f"[LINK] Found by class {cls}: {abs_url}")
                links.add(abs_url)
            else:
                print(f"[SKIP] Ignoring base_url (by class): {abs_url}")
    return list(links)

def fetch_url(session, url, timeout=30):
    print(f"[FETCH] Fetching: {url}")
    tries = 3
    for attempt in range(tries):
        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            resp.encoding = resp.encoding or resp.apparent_encoding
            print(f"[FETCH] Success {url} (status {resp.status_code})")
            return resp.status_code, resp.text
        except Exception as e:
            print(f"[HTTP] {url} attempt {attempt+1}/{tries} failed: {e}")
            time.sleep(2)
    print(f"[ERROR] Giving up on {url}")
    return None, None

def scrape_site_posts(session, base_url):
    status_code, html = fetch_url(session, base_url)
    if status_code != 200 or not html:
        print(f"[ERROR] Could not fetch main page: {base_url} (status {status_code})")
        return []
    soup = BeautifulSoup(html, "lxml")
    clean_soup(soup)
    post_links = extract_post_links(soup, base_url)
    print(f"[INFO] {len(post_links)} post-like links found for {base_url}")
    results = []
    scraped_urls = set()
    for idx, post_url in enumerate(post_links):
        norm_url = post_url.rstrip('/')
        if url_equivalent(norm_url, base_url):
            print(f"[SKIP] Ignoring same as base_url: {norm_url}")
            continue
        if norm_url in scraped_urls:
            continue
        scraped_urls.add(norm_url)
        post_status, post_html = fetch_url(session, norm_url)
        if post_status != 200 or not post_html:
            continue
        main_text, date_found, company_url = extract_content_and_date(post_html, norm_url)
        if not main_text or len(main_text.strip()) < 50:
            print(f"[WARN] Post {norm_url} had no real content.")
            continue
        record = {
            "post_url": norm_url,
            "base_url": base_url,
            "scraped_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            "date": date_found,
            "company_url": company_url,
            "content": main_text,
        }
        print(f"[OK] Scraped post: {norm_url}")
        results.append(record)
        time.sleep(1.0)
    return results
from bs4 import BeautifulSoup, Tag

def extract_content_and_date(html, url):
    soup = BeautifulSoup(html, "lxml")
    clean_soup(soup)
    post_container = soup.find("div", class_="col-md-8 col-xl-6")
    main_text = ""
    date_found = ""
    company_url = ""

    if post_container:
        paragraphs = []
        for child in post_container.children:
            # If child is a Tag, check its class
            if isinstance(child, Tag):
                if not (child.has_attr("class") and "item_box-info" in child.get("class", [])):
                    text = child.get_text(" ", strip=True)
                    if text and len(text) > 40:
                        paragraphs.append(text)
            # If it's NavigableString, just add text
            elif isinstance(child, str):
                text = child.strip()
                if text and len(text) > 40:
                    paragraphs.append(text)
        if paragraphs:
            main_text = " ".join(paragraphs)

        # Find date in the clock icon row
        for info in post_container.find_all("div", class_="item_box-info__item"):
            img = info.find("img", class_="item_box__icon")
            if img and "clock.png" in img.get("src", ""):
                date_found = info.get_text(" ", strip=True).replace('\n', '').replace('\r', '')
            link = info.find("a", class_="item_box-info__link")
            if link:
                company_url = link.get("href", "")
    else:
        # Fallback: old method
        main_text, date_found = extract_content_and_date_old(html, url)
        company_url = ""

    main_text = main_text.strip()
    main_text= clean_newlines(main_text)
    date_found = date_found.strip()
    date_found = normalize_date(date_found)
    company_url = company_url.strip()
    print(f"[SPECIAL] Date: {date_found}, Company URL: {company_url}")
    print(f"[SPECIAL] Text preview: {main_text[:200]}...")
    return main_text, date_found, company_url

# Fallback method for pages without this structure
def extract_content_and_date_old(html, url):
    soup = BeautifulSoup(html, "lxml")
    clean_soup(soup)
    text_candidates = []
    for sel in ["article", "main", ".post", ".card", ".entry-content", ".content", ".news", ".article"]:
        for node in soup.select(sel):
            txt = node.get_text(" ", strip=True)
            if txt and len(txt) > 80:
                text_candidates.append(txt)
    if not text_candidates:
        text_candidates = [" ".join([p.get_text(' ', strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40])]
    date_found = ""
    for t in soup.find_all("time"):
        dt = (t.get("datetime") or "").strip()
        txt = t.get_text(" ", strip=True)
        if dt:
            date_found = dt
            break
        if txt:
            date_found = txt
            break
    main_text = text_candidates[0] if text_candidates else ""
    return main_text, date_found

def main():
    tor_process = start_tor_if_needed()
    try:
        urls = read_urls(INPUT_CSV)
        if not urls:
            print("[ERROR] No URLs to process. Check your CSV.")
            return
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        if any(u.endswith(".onion") for u in urls):
            print("[INFO] Onion site detected — using Tor proxy.")
            session.proxies.update(PROXIES)
        with open(OUTPUT_JSONL, "w", encoding="utf-8") as out_f:
            for base_url in urls:
                print(f"\n[INFO] Scraping base_url: {base_url}")
                posts = scrape_site_posts(session, base_url)
                for rec in posts:
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"[OK] {len(posts)} posts written for {base_url}")
                time.sleep(1.0)
        print(f"\n[COMPLETE] All results written to {OUTPUT_JSONL}")
    finally:
        if tor_process is not None:
            print("[TOR] Shutting down Tor...")
            try:
                tor_process.terminate()
            except Exception:
                pass

if __name__ == "__main__":
    main()