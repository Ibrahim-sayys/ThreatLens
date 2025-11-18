"""Stopword filtering helper

Provides functions to remove English stopwords from a paragraph of text.

Functions:
- remove_stopwords(text, extra_stopwords=None, keep_case=False):
    Returns a cleaned string with punctuation removed and stopwords filtered out.

- remove_stopwords_preserve_punctuation(text, extra_stopwords=None):
    Returns the text with stopwords removed but preserves original punctuation and spacing
    as much as possible.

Both functions are safe on None/empty input and accept an iterable of extra stopwords
to remove.

Example:
>>> remove_stopwords("A cyberattack exposed customer credit card details and login credentials.")
'cyberattack exposed customer credit card details login credentials'
"""

from __future__ import annotations

import re
from typing import Iterable, Optional, Set

# A commonly used English stopword list (based on NLTK's stopwords)
DEFAULT_STOPWORDS: Set[str] = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but',
    'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
    'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've",
    'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't",
    'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
    'wouldn', "wouldn't"
}

# Word token pattern (alphanumeric + underscore). We'll use this to extract words.
_WORD_RE = re.compile(r"\b\w+\b")


def _build_stopwords(extra_stopwords: Optional[Iterable[str]] = None) -> Set[str]:
    """Return a normalized set of stopwords including any extras provided."""
    stopwords = set(DEFAULT_STOPWORDS)
    if extra_stopwords:
        stopwords.update({s.lower() for s in extra_stopwords if isinstance(s, str)})
    return stopwords


def remove_stopwords(text: Optional[str], extra_stopwords: Optional[Iterable[str]] = None, keep_case: bool = False) -> str:
    """Remove stopwords from `text` and return cleaned text.

    - Strips punctuation (non-word characters) and returns tokens joined by single spaces.
    - `extra_stopwords` can be provided to add additional words to remove.
    - If `keep_case` is True, original token casing is preserved for non-stopwords.

    Returns an empty string if input is None or not a string.
    """
    if not isinstance(text, str) or not text:
        return ""

    stopwords = _build_stopwords(extra_stopwords)

    # Extract word tokens
    tokens = _WORD_RE.findall(text)
    if not tokens:
        return ""

    cleaned_tokens = []
    if keep_case:
        for tok in tokens:
            if tok.lower() not in stopwords:
                cleaned_tokens.append(tok)
    else:
        for tok in tokens:
            tl = tok.lower()
            if tl not in stopwords:
                cleaned_tokens.append(tl)

    return " ".join(cleaned_tokens)


def remove_stopwords_preserve_punctuation(text: Optional[str], extra_stopwords: Optional[Iterable[str]] = None) -> str:
    """Remove stopwords from `text` but preserve punctuation and spacing.

    The function removes whole-word stopwords using a regex word-boundary replacement
    so punctuation adjacent to words is kept. It normalizes consecutive whitespace to a single
    space after removal.
    """
    if not isinstance(text, str) or not text:
        return ""

    stopwords = _build_stopwords(extra_stopwords)
    # Create an alternation group of stopwords, escaped for regex.
    # We sort by length descending to ensure longer matches (if any) are preferred.
    words = sorted(stopwords, key=lambda s: -len(s))
    if not words:
        return text

    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", flags=re.IGNORECASE)

    # Replace matches with a single space, then collapse whitespace
    without = pattern.sub(" ", text)
    collapsed = re.sub(r"\s+", " ", without).strip()
    return collapsed


# Small CLI/demo when run directly
if __name__ == "__main__":
    sample = "A cyberattack exposed customer credit card details and login credentials."
    print("Original:\n", sample)
    print("\nremove_stopwords:\n", remove_stopwords(sample))
    print("\nremove_stopwords (keep_case=True):\n", remove_stopwords(sample, keep_case=True))
    print("\nremove_stopwords_preserve_punctuation:\n", remove_stopwords_preserve_punctuation(sample))
