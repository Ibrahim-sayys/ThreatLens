import re
from typing import Optional, List


def extract_urls(text: str) -> Optional[List[str]]:
    """
    Extract all URLs from the given text, including .onion addresses.
    Returns a list of URLs if found, else None.
    """
    if not text or not isinstance(text, str):
        return None
    # Regex pattern for URLs (http, https, www, common TLDs, .onion)
    url_pattern = (
        r'https?://\S+'  # http(s)://...
        r'|www\.\S+'    # www....
        r'|(?:[\w-]+\.)+(?:com|org|net|edu|gov|io|co|uk|de|jp|fr|au|us|ru|ch|it|nl|se|no|es|mil)\b(?:/\S*)?'  # common TLDs
        r'|(?:https?://)?[\w\d-]{16,56}\.onion\b(?:/\S*)?'  # .onion URLs (with or without protocol)
    )
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    return urls if urls else None
