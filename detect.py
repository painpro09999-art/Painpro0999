"""
detect.py — checks a transcript chunk against configured keywords and
regex patterns, and returns any matches found.
"""

import re
from typing import List


def find_hits(text: str, keywords: List[str], regex_patterns: List[str]) -> List[str]:
    """
    Returns a list of matched keywords/patterns found in `text`.
    Empty list means no hit. Matching is case-insensitive.
    """
    if not text:
        return []

    hits = []
    lower_text = text.lower()

    for kw in keywords:
        if kw.lower() in lower_text:
            hits.append(kw)

    for pattern in regex_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(f"regex:{pattern}")

    return hits
