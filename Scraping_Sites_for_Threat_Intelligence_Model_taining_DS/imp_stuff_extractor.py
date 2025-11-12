#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional

# -------- NLP setup (spaCy) --------
import spacy
from spacy.matcher import PhraseMatcher
from spacy.pipeline import EntityRuler
from spacy.tokens import Doc

# --------------- Config ---------------

# Common company/org suffixes and cues
ORG_SUFFIXES = [
    "inc", "inc.", "llc", "l.l.c.", "ltd", "ltd.", "co", "co.", "corp", "corp.",
    "corporation", "company", "gmbh", "ag", "s.a.", "s.a", "s.p.a.", "spa", "bv",
    "nv", "oy", "ab", "plc", "pt", "pte", "pte.", "k.k.", "kk", "oyj", "sarl",
    "s.r.l.", "srl", "llp", "l.l.p.", "lp", "l.p.", "pc", "p.c.", "psc", "sa",
    "sas", "spa", "as", "aps", "oy", "oyj", "kft", "zt", "z.o.o.", "sp. z o.o.",
    "limited", "pte ltd", "pty ltd", "co., ltd.", "co ltd", "co.,ltd.", "holdings",
    "group", "partners", "associates", "consulting", "solutions", "services",
    "university", "college", "foundation", "institute", "bank", "ministries",
    "ministry", "department"
]

# Tokens that are *too generic* to be a company name by themselves
ORG_BLACKLIST = set("""
information data document page section party parties exhibit tenant landlord
broker letter intent loi amendment agreement schedule attachment appendix form
table report budget income expense profile privacy terms cookies contact home
""".split())

# Sector / Department / Attack keyword taxonomies (non-exhaustive, extend as needed)
SECTOR_KEYWORDS = {
    "healthcare": [
        "hospital", "clinic", "surgical", "patient", "hipaa", "ehr", "medical",
        "healthcare", "physician", "urology", "gastroenterology", "otolaryngology"
    ],
    "finance": [
        "bank", "credit", "financial", "loan", "mortgage", "fintech", "payment",
        "brokerage", "investment", "ledger"
    ],
    "education": [
        "university", "college", "school", "campus", "academic", "students", "faculty"
    ],
    "government": [
        "ministry", "department", "municipal", "agency", "public sector", "govt", "government"
    ],
    "retail": [
        "retail", "store", "franchise", "ecommerce", "shopping", "merchandise"
    ],
    "manufacturing": [
        "factory", "manufacturing", "industrial", "assembly", "plant", "supply chain"
    ],
    "real_estate": [
        "lease", "sublease", "broker", "real estate", "commercial property", "ladera ranch",
        "rent", "tenant", "landlord"
    ],
    "it_technology": [
        "cybersecurity", "software", "cloud", "data center", "database", "it", "devops", "cve"
    ],
    "telecom": [
        "telecom", "telecommunications", "carrier", "mobile operator", "fiber"
    ],
    "transportation": [
        "logistics", "shipping", "transport", "airline", "railway", "fleet", "route"
    ],
}

DEPARTMENT_KEYWORDS = {
    "accounts": ["account", "accounts", "ledger", "bookkeeping", "invoices", "billing"],
    "finance": ["finance", "financial", "budget", "treasury", "audit"],
    "hr": ["hr", "human resources", "recruitment", "payroll", "benefits"],
    "sales": ["sales", "pipeline", "crm", "leads", "quotas"],
    "marketing": ["marketing", "campaign", "branding", "advertising"],
    "it": ["it", "information technology", "sysadmin", "helpdesk", "infra"],
    "legal": ["legal", "compliance", "contract", "litigation", "arbitration"],
    "operations": ["operations", "ops", "sop", "workflow", "facility"],
    "procurement": ["procurement", "purchasing", "vendor", "sourcing"],
    "logistics": ["logistics", "fulfillment", "warehouse", "inventory"],
    "engineering": ["engineering", "r&d", "research", "development", "dev", "qa", "devops"],
    "medical": ["patient", "clinical", "medical", "nursing", "physician"],
}

ATTACK_KEYWORDS = {
    "ransomware": ["ransomware", "encrypt", "ransom note", "double extortion"],
    "data_leak": ["leak", "dump", "data leak", "exfiltration", "data theft"],
    "breach": ["breach", "compromise", "breached"],
    "credentials": ["credential", "password", "login", "auth", "account takeover"],
    "phishing": ["phish", "phishing", "social engineering"],
    "malware": ["malware", "trojan", "spyware", "keylogger"],
    "ddos": ["ddos", "denial of service"],
    "vulnerability": ["cve", "exploit", "zero-day", "vulnerability", "remote code execution"],
}

# ----------------- Utilities -----------------

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return data

def save_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def best_spacy_model() -> spacy.Language:
    for name in ["en_core_web_trf", "en_core_web_lg", "en_core_web_md", "en_core_web_sm"]:
        try:
            nlp = spacy.load(name)
            print(f"[NLP] Loaded spaCy model: {name}")
            return nlp
        except Exception:
            continue
    print("[NLP] Falling back to blank 'en' model.")
    nlp = spacy.blank("en")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    return nlp

def save_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def best_spacy_model() -> spacy.Language:
    """
    Try larger English models first, then fall back.
    """
    tried = []
    for name in ["en_core_web_trf", "en_core_web_lg", "en_core_web_md", "en_core_web_sm"]:
        try:
            nlp = spacy.load(name)
            print(f"[NLP] Loaded spaCy model: {name}")
            return nlp
        except Exception as e:
            tried.append((name, str(e)))
    # As a last resort, load a blank English pipeline and add a simple sentencizer.
    print("[NLP] Could not load any prebuilt English model. Falling back to blank 'en'.")
    nlp = spacy.blank("en")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    return nlp

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def titlecase_ratio(s: str) -> float:
    """
    Ratio of Title/Upper tokens among alpha tokens.
    """
    tokens = re.findall(r"[A-Za-z][\w&\-.]*", s)
    if not tokens:
        return 0.0
    good = 0
    for t in tokens:
        if t.isupper() or (t[0].isupper() and t[1:].islower()):
            good += 1
    return good / len(tokens)

def has_org_suffix(s: str) -> bool:
    s_low = s.lower()
    for suf in ORG_SUFFIXES:
        if re.search(rf"\b{re.escape(suf)}\b", s_low):
            return True
    return False

def token_count(s: str) -> int:
    return len(re.findall(r"[A-Za-z0-9&\-.]+", s))

def clean_candidate(s: str) -> str:
    s = normalize_space(s)
    # trim leading/trailing punctuation/quotes
    s = re.sub(r'^[\s\W_]+|[\s\W_]+$', "", s)
    return s

def is_blacklisted_single_word(s: str) -> bool:
    tokens = re.findall(r"[A-Za-z]+", s.lower())
    return len(tokens) == 1 and tokens[0] in ORG_BLACKLIST

def score_company_candidate(s: str, came_from_ner: bool) -> float:
    """
    Heuristic scoring for org strings.
    """
    s_clean = clean_candidate(s)
    if not s_clean:
        return 0.0
    if is_blacklisted_single_word(s_clean):
        return 0.0

    score = 0.0
    # token length bonus
    tc = token_count(s_clean)
    if tc >= 2:
        score += 0.6
    elif tc == 1:
        score += 0.2

    # suffix bonus
    if has_org_suffix(s_clean):
        score += 0.9

    # titlecase/uppercase pattern bonus
    score += min(0.8, titlecase_ratio(s_clean))  # 0..0.8

    # contains separators often seen in orgs
    if any(ch in s_clean for ch in ["&", "-", ","]):
        score += 0.2

    # if from NER, grant base credibility
    if came_from_ner:
        score += 0.6

    # small penalty if extremely short (like 2–3 characters)
    if len(s_clean) <= 3:
        score -= 0.3

    return max(score, 0.0)

def dedupe_keep_longest(items: List[str]) -> List[str]:
    """
    Case-insensitive dedupe; if one item is substring of another, keep the longer one.
    """
    # Normalize by lowercase
    uniq = {}
    for it in items:
        key = it.lower()
        if key not in uniq or len(it) > len(uniq[key]):
            uniq[key] = it
    # Remove items that are fully contained in longer ones (case-insensitive)
    vals = list(uniq.values())
    vals_sorted = sorted(vals, key=len, reverse=True)
    kept = []
    for v in vals_sorted:
        if not any(v.lower() != u.lower() and v.lower() in u.lower() for u in kept):
            kept.append(v)
    # Keep original order as much as possible
    kept.reverse()
    return list(reversed(kept))

# ----------------- Matchers -----------------

def build_phrase_matcher(nlp, taxonomy: Dict[str, List[str]]) -> PhraseMatcher:
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for label, phrases in taxonomy.items():
        patterns = [nlp.make_doc(p) for p in phrases]
        matcher.add(label.upper(), patterns)
    return matcher

def add_entity_ruler(nlp) -> None:
    """
    Add rule patterns that nudge spaCy to recognize org-like entities
    even in small models. These patterns are conservative.
    """
    try:
        ruler = nlp.add_pipe("entity_ruler", before="ner") if "ner" in nlp.pipe_names else nlp.add_pipe("entity_ruler")
    except ValueError:
        # already added
        return

    patterns = []
    # Proper noun sequences ending with an org suffix word
    # (Very light pattern to avoid over-triggering)
    suffix_regex = "(" + "|".join(re.escape(s) for s in ORG_SUFFIXES) + ")"
    patterns.append({
        "label": "ORG",
        "pattern": [{"IS_TITLE": True, "OP": "+"}, {"TEXT": {"REGEX": rf"(?i)^{suffix_regex}$"}}]
    })
    # Words like "University of X", "Bank of Y", "Ministry of Z"
    patterns.extend([
        {"label": "ORG", "pattern": [{"LOWER": {"IN": ["university", "college", "bank", "ministry", "department"]}},
                                     {"LOWER": "of", "OP": "?"}, {"IS_TITLE": True, "OP": "+"}]},
    ])
    ruler.add_patterns(patterns)

# ----------------- Extraction -----------------

def extract_companies(text: str, nlp) -> List[str]:
    """
    Use spaCy NER + heuristics to get company names; apply scoring to reduce false positives.
    """
    text = normalize_space(text)
    if not text:
        return []

    doc = nlp(text)

    # Gather spaCy ORG entities
    ner_orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    # Heuristic candidates:
    # - Proper noun sequences containing org suffixes
    # - Phrases with & or commas followed by suffix words
    # - Titlecased sequences adjacent to org cue words
    cand = set(ner_orgs)

    # Regex heuristic: capture segments ending with an org suffix (up to ~10 words)
    suffix_union = "|".join(re.escape(s) for s in ORG_SUFFIXES)
    regex = re.compile(
        rf"\b([A-Z][\w&\-.']+(?:\s+[A-Z][\w&\-.']+){{0,9}}\s+(?:{suffix_union}))\b",
        flags=re.IGNORECASE
    )
    for m in regex.finditer(text):
        cand.add(m.group(1))

    # Another heuristic: 'University of X', 'Bank of Y', 'Ministry of ...'
    cue_regex = re.compile(r"\b(University|College|Bank|Ministry|Department)\s+of\s+[A-Z][\w\-.']+(?:\s+[A-Z][\w\-.']+){0,6}\b")
    for m in cue_regex.finditer(text):
        cand.add(m.group(0))

    # Clean, score, filter
    scored: List[Tuple[str, float]] = []
    ner_set = set(ner_orgs)
    for c in cand:
        c2 = clean_candidate(c)
        if not c2 or any(tok.lower() in ORG_BLACKLIST for tok in c2.split()):
            continue
        s = score_company_candidate(c2, came_from_ner=(c in ner_set))
        if s >= 1.0:  # threshold tuned to be conservative
            scored.append((c2, s))

    # Sort by score desc, then length desc
    scored.sort(key=lambda x: (x[1], len(x[0])), reverse=True)

    # Keep unique, prefer longer
    ordered = [name for name, _ in scored]
    deduped = dedupe_keep_longest(ordered)

    # Optional: cap to reasonable number to avoid noise
    return deduped[:20]

def extract_taxonomy(text: str, nlp) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Detect sectors, departments, attack types and raw keyword hits using PhraseMatcher.
    """
    text = text or ""
    doc = nlp.make_doc(text)

    sector_matcher = build_phrase_matcher(nlp, SECTOR_KEYWORDS)
    dept_matcher = build_phrase_matcher(nlp, DEPARTMENT_KEYWORDS)
    attack_matcher = build_phrase_matcher(nlp, ATTACK_KEYWORDS)

    sectors = set()
    departments = set()
    attacks = set()
    raw_keywords = []

    for mid, start, end in sector_matcher(doc):
        label = nlp.vocab.strings[mid]
        sectors.add(label.lower())
        raw_keywords.append(doc[start:end].text)

    for mid, start, end in dept_matcher(doc):
        label = nlp.vocab.strings[mid]
        departments.add(label.lower())
        raw_keywords.append(doc[start:end].text)

    for mid, start, end in attack_matcher(doc):
        label = nlp.vocab.strings[mid]
        attacks.add(label.lower())
        raw_keywords.append(doc[start:end].text)

    # Also add a few simple regex-y cues (e.g., CVE-xxxx-xxxxx)
    if re.search(r"\bCVE-\d{4}-\d{3,7}\b", text, flags=re.IGNORECASE):
        attacks.add("vulnerability")
        raw_keywords.append("CVE-*")

    # Deduplicate keywords but keep stable order
    seen = set()
    dedup_keywords = []
    for k in raw_keywords:
        kl = k.lower()
        if kl not in seen:
            seen.add(kl)
            dedup_keywords.append(k)

    return sorted(sectors), sorted(departments), sorted(attacks), dedup_keywords

# ----------------- Pipeline -----------------

def process_record(rec: Dict[str, Any], nlp) -> Dict[str, Any]:
    """
    Process a single JSONL record:
    expects keys like 'content', 'date', 'post_url', 'base_url'
    """
    content = rec.get("content") or rec.get("text") or ""
    content = normalize_space(content)

    companies = extract_companies(content, nlp)
    sectors, departments, attacks, keywords = extract_taxonomy(content, nlp)

    # prefer post_url, else base_url
    url = rec.get("post_url") or rec.get("url") or rec.get("base_url") or None

    return {
        "date": rec.get("date"),
        "url": url,
        "companies": companies,
        "sectors": sectors,
        "departments": departments,
        "attack_types": attacks,
        "keywords": keywords
    }

# ----------------- Main -----------------

def main():
    # <-- Hardcoded input/output -->
    input_file = "output.jsonl"     # change to your input file
    output_file = "output_of_spacy.jsonl"   # change to your desired output file

    nlp = best_spacy_model()
    add_entity_ruler(nlp)

    data = load_jsonl(input_file)
    if not data:
        print("[IO] No valid JSONL records found in input.")
        save_jsonl(output_file, [])
        return

    results = []
    for rec in data:
        try:
            out = process_record(rec, nlp)
            results.append(out)
        except Exception as e:
            url = rec.get("post_url") or rec.get("url") or rec.get("base_url")
            results.append({
                "date": rec.get("date"),
                "url": url,
                "companies": [],
                "sectors": [],
                "departments": [],
                "attack_types": [],
                "keywords": [],
                "error": f"{type(e).__name__}: {e}"
            })

    save_jsonl(output_file, results)
    print(f"[OK] Wrote {len(results)} records to {output_file}")

if __name__ == "__main__":
    main()