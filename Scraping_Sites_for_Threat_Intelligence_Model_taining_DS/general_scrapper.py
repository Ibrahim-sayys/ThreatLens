#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import re
import sys
import time
import signal
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Optional: start Tor automatically
try:
    from stem.process import launch_tor_with_config
    STEM_AVAILABLE = True
except Exception:
    STEM_AVAILABLE = False

TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9050
PROXIES = {
    "http": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
    "https": f"socks5h://{TOR_SOCKS_PORT}:{TOR_SOCKS_PORT}",
}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

OUTPUT_JSON = "scrape_output.json"
INPUT_CSV = "testing_input_urls.csv"

# Regex for date-like strings (covers many common formats)
DATE_REGEX = re.compile(
    r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{2,4})\b",
    flags=re.IGNORECASE,
)

# --- Filtering image/file URLs ---
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff", ".jfif", ".pjpeg", ".pjp", ".avif"}

OTHER_FILE_EXTENSIONS = {".pdf", ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp4", ".mp3", ".wav", ".ogg", ".avi", ".mov"}

def is_image_url(url):
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)

def is_other_file_url(url):
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in OTHER_FILE_EXTENSIONS)

def is_html_or_no_ext(url):
    path = urlparse(url).path.lower()
    _, ext = os.path.splitext(path)
    return (not ext) or ext in (".html", ".htm")

# ---------- Tor bootstrap ----------
def start_tor_if_needed():
    sess = requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    sess.proxies.update(PROXIES)
    try:
        sess.get("http://httpbin.org/ip", timeout=5)
        print("[TOR] Detected a running Tor SOCKS proxy on 9050 — using it.")
        return None
    except Exception:
        pass

    if not STEM_AVAILABLE:
        print(
            "[TOR] Tor is not running and `stem` is not installed. "
            "Install Tor and/or run it manually on port 9050, "
            "or `pip install stem` to allow auto-launch.",
            file=sys.stderr,
        )
        return None

    print("[TOR] Attempting to launch Tor on 9050 via stem...")
    try:
        tor_process = launch_tor_with_config(
            config={
                "SOCKSPort": str(TOR_SOCKS_PORT),
                "Log": "notice stdout",
            },
            take_ownership=True,
            timeout=60,
        )
        print("[TOR] Tor started.")
        return tor_process
    except Exception as e:
        print(f"[TOR] Failed to start Tor automatically: {e}", file=sys.stderr)
        return None

# ---------- IO helpers ----------
def read_urls(csv_path: str):
    urls = []
    if not os.path.exists(csv_path):
        print(f"[IO] Input CSV not found: {csv_path}", file=sys.stderr)
        return urls

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            candidate = row[0].strip()
            if not candidate:
                continue
            if i == 0 and not candidate.lower().startswith(("http://", "https://")) and not candidate.endswith(".onion"):
                continue
            urls.append(candidate)
    return urls

# ---------- Parsing & extraction ----------
def clean_soup(soup: BeautifulSoup):
    for tag in soup(["script", "style", "noscript", "iframe", "canvas", "svg"]):
        tag.decompose()
    for selector in [
        "header", "footer", "nav", "form", "aside",
        "[role='navigation']", "[role='search']",
        ".header", ".footer", ".nav", ".navbar", ".menu", ".sidebar",
        ".ads", ".advertisement", ".promo", ".cookie", "#cookie", ".subscribe",
    ]:
        for tag in soup.select(selector):
            tag.decompose()
    return soup

def extract_headings(soup: BeautifulSoup):
    heads = []
    for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        for h in soup.find_all(level):
            text = h.get_text(separator=" ", strip=True)
            if text:
                heads.append({"tag": level, "text": text})
    return heads

def extract_links(soup: BeautifulSoup, base_url: str, same_domain_only=True):
    base = urlparse(base_url)
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            continue
        if same_domain_only and parsed.netloc and parsed.netloc != base.netloc:
            continue
        # --- skip image/file hrefs ---
        if is_image_url(abs_url):
            continue
        if is_other_file_url(abs_url):
            continue
        # Optionally: only allow HTML or no extension
        # if not is_html_or_no_ext(abs_url):
        #     continue
        links.append({"text": a.get_text(strip=True), "url": abs_url})
    # Deduplicate by URL
    seen = set()
    uniq = []
    for item in links:
        if item["url"] not in seen:
            seen.add(item["url"])
            uniq.append(item)
    return uniq

def extract_timestamps(soup: BeautifulSoup, text_blob: str):
    stamps = set()
    for t in soup.find_all("time"):
        dt = (t.get("datetime") or "").strip()
        txt = t.get_text(" ", strip=True)
        if dt:
            stamps.add(dt)
        if txt and DATE_REGEX.search(txt):
            stamps.add(txt)
    for selector, attr in [
        ('meta[property="article:published_time"]', "content"),
        ('meta[name="pubdate"]', "content"),
        ('meta[name="date"]', "content"),
        ('meta[name="dc.date"]', "content"),
        ('meta[itemprop="datePublished"]', "content"),
        ('meta[itemprop="dateModified"]', "content"),
    ]:
        for m in soup.select(selector):
            val = (m.get(attr) or "").strip()
            if val:
                stamps.add(val)
    for match in DATE_REGEX.findall(text_blob or ""):
        stamps.add(match.strip())
    return sorted(stamps)

def extract_main_text(soup: BeautifulSoup):
    candidates = []
    for sel in ["article", "main", "#content", ".content", ".post", ".article", ".entry-content"]:
        for node in soup.select(sel):
            txt = node.get_text(" ", strip=True)
            if txt and len(txt) > 120:
                candidates.append(txt)
    if candidates:
        chunks = []
        for block in candidates:
            parts = [p.strip() for p in re.split(r"\n{2,}|\r{2,}", block) if p.strip()]
            chunks.extend(parts)
        paragraphs = []
        for c in chunks:
            if len(c) > 2000:
                paragraphs.extend([p.strip() for p in re.split(r"(?<=[.!?])\s+", c) if len(p.strip()) > 40])
            else:
                paragraphs.append(c)
        return [p for p in paragraphs if len(p) > 40]
    paras = []
    for p in soup.find_all(["p", "div", "span"]):
        txt = p.get_text(" ", strip=True)
        if txt and len(txt) > 40:
            paras.append(txt)
    seen = set()
    out = []
    for p in paras:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:500]

# ---------- HTTP ----------
def fetch_url(session: requests.Session, url: str, timeout: int = 30):
    tries = 3
    for attempt in range(1, tries + 1):
        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            resp.encoding = resp.encoding or resp.apparent_encoding
            return resp.status_code, resp.text
        except requests.RequestException as e:
            print(f"[HTTP] Attempt {attempt}/{tries} failed for {url}: {e}")
            if attempt < tries:
                time.sleep(2 * attempt)
            else:
                raise
    raise requests.RequestException("Max retries exceeded")

# ---------- Post-detection heuristics ----------
NUMERIC_OR_SLUGGY = re.compile(r"^(\d{2,}|[a-f0-9]{6,}|page|p|post|article|news|blog)s?$", re.IGNORECASE)

def _parent_key_from_path(path: str, depth: int = 2) -> str:
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "/"
    keep = segs[: min(len(segs), depth)]
    return "/" + "/".join(keep) + "/"

def _loose_parent_key(path: str) -> str:
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "/"
    if len(segs) == 1:
        return "/"
    if NUMERIC_OR_SLUGGY.match(segs[-1]):
        segs = segs[:-1]
    return "/" + "/".join(segs[:2]) + "/"

def detect_post_buckets(links, base_url):
    base_netloc = urlparse(base_url).netloc
    by_bucket = {}
    def add(bucket, url):
        by_bucket.setdefault(bucket, set()).add(url)
    for item in links:
        url = item["url"]
        parsed = urlparse(url)
        if parsed.netloc != base_netloc:
            continue
        path = parsed.path or "/"
        for d in (1, 2, 3):
            add(f"strict:{d}:{_parent_key_from_path(path, d)}", url)
        add(f"loose:{_loose_parent_key(path)}", url)
    MIN_POSTS = 6
    big_buckets = {k: sorted(v) for k, v in by_bucket.items() if len(v) >= MIN_POSTS}
    big_buckets = dict(sorted(big_buckets.items(), key=lambda kv: len(kv[1]), reverse=True))
    return big_buckets

# ---------- Scraping orchestration ----------
def scrape_page(session, url):
    record = {
        "url": url,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "status": "ok",
        "http_status": None,
        "headings": [],
        "content": [],
        "links": [],
        "timestamps": [],
        "error": None,
    }
    try:
        status_code, html = fetch_url(session, url)
        record["http_status"] = status_code
        if status_code != 200 or not html:
            record["status"] = "http_error"
            return record
        soup = BeautifulSoup(html, "lxml")
        soup = clean_soup(soup)
        headings = extract_headings(soup)
        content_paras = extract_main_text(soup)
        links = extract_links(soup, base_url=url, same_domain_only=True)
        text_blob = " ".join(content_paras[:100])
        timestamps = extract_timestamps(soup, text_blob)
        record["headings"] = headings
        record["content"] = content_paras
        record["links"] = links
        record["timestamps"] = timestamps
    except requests.RequestException as e:
        record["status"] = "network_error"
        record["error"] = str(e)
    except Exception as e:
        record["status"] = "parse_error"
        record["error"] = f"{type(e).__name__}: {e}"
    return record

def scrape_urls(urls):
    results = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.proxies.update(PROXIES)
    for idx, url in enumerate(urls, start=1):
        print(f"\n[{idx}/{len(urls)}] Scanning index page: {url}")
        try:
            status_code, html = fetch_url(session, url)
        except Exception as e:
            print(f"[SCAN] Failed to open {url}: {e}")
            error_rec = {
                "url": url,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "status": "network_error",
                "http_status": None,
                "headings": [],
                "content": [],
                "links": [],
                "timestamps": [],
                "error": str(e),
            }
            results.append(error_rec)
            continue
        if status_code != 200 or not html:
            print(f"[SCAN] Non-200 or empty response for {url}: HTTP {status_code}")
            results.append({
                "url": url,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "status": "http_error",
                "http_status": status_code,
                "headings": [],
                "content": [],
                "links": [],
                "timestamps": [],
                "error": f"HTTP {status_code}",
            })
            continue
        soup = BeautifulSoup(html, "lxml")
        soup = clean_soup(soup)
        internal_links = extract_links(soup, base_url=url, same_domain_only=True)
        buckets = detect_post_buckets(internal_links, base_url=url)
        if buckets:
            print(f"[SCAN] Detected {len(buckets)} post-bucket(s). Scraping posts…")
            post_urls = []
            for bucket_key, urls_in_bucket in buckets.items():
                print(f"  - Bucket {bucket_key} -> {len(urls_in_bucket)} links")
                # --- filter out image/file URLs (redundant but safest) ---
                filtered_urls = [
                    u for u in urls_in_bucket
                    if not is_image_url(u) and not is_other_file_url(u) and is_html_or_no_ext(u)
                ]
                post_urls.extend(filtered_urls)
            seen = set()
            post_urls = [u for u in post_urls if not (u in seen or seen.add(u))]
            for j, post_url in enumerate(post_urls, start=1):
                print(f"   [post {j}/{len(post_urls)}] {post_url}")
                rec = scrape_page(session, post_url)
                rec["source_index_url"] = url
                results.append(rec)
                time.sleep(1.0)
        else:
            print("[SCAN] No repeating post-like links found. Scraping the page itself (fallback).")
            rec = scrape_page(session, url)
            results.append(rec)
            time.sleep(1.0)
    return results

# ---------- Main ----------
def main():
    tor_process = start_tor_if_needed()
    try:
        urls = read_urls(INPUT_CSV)
        if not urls:
            print("[IO] No URLs to process. Check your CSV.")
            return
        data = scrape_urls(urls)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved {len(data)} records to {OUTPUT_JSON}")
    finally:
        if tor_process is not None:
            print("[TOR] Shutting down Tor...")
            try:
                tor_process.terminate()
            except Exception:
                try:
                    os.kill(tor_process.pid, signal.SIGKILL)
                except Exception:
                    pass

if __name__ == "__main__":
    main()