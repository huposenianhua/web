"""Regular expression pattern utilities.

Translated from PHP regexp.php.
Provides pattern builder functions for consistent regex construction.
"""

import re


def regex_boundary() -> str:
    """Return regex boundary delimiter (# style)."""
    return "#"


def regex_space() -> str:
    """Pattern: zero or more whitespace."""
    return r"\s*"


def regex_none_space() -> str:
    """Pattern: zero or more non-whitespace."""
    return r"\S*"


def regex_all() -> str:
    """Pattern: any content (non-greedy)."""
    return r"[\S\s]*?"


def regex_digit() -> str:
    """Pattern: zero or more digits."""
    return r"[\d]*"


def regex_number() -> str:
    """Pattern: number with optional sign and decimal."""
    return r"[\d.-]*"


def regex_fmt_number() -> str:
    """Pattern: formatted number with commas, K/M/B/T suffixes."""
    return r"[\d,.-KMBT]*"


def regex_date() -> str:
    """Pattern: YYYY-MM-DD date."""
    return r"\d{4}-\d{2}-\d{2}"


def regex_parenthesis(left: str, mid: str, right: str) -> str:
    """Build a capturing group: left(mid)right."""
    return f"{left}({mid}){right}"


def regex_skip(pattern: str) -> str:
    """Wrap pattern as optional non-capturing group."""
    return f"(?:{pattern})?"


def regex_stock_symbol(symbol: str, is_index: bool = False) -> str:
    """Escape stock symbol for regex, escaping ^ if it's an index."""
    if is_index:
        return re.escape(symbol)
    return symbol


def regex_debug(match: re.Match, source: str = "", min_count: int = 0) -> int:
    """Debug helper: log match count and return it.

    Args:
        match: regex match result
        source: label for debug logging
        min_count: minimum match count to log

    Returns:
        Number of matched groups
    """
    count = len(match.groups())
    if count > min_count:
        from app.utils.logger import debug_val, debug_print
        debug_val(count, source)
        debug_print(list(match.groups()))
    return count


def preg_match_square_bracket(prefix: str, text: str) -> str | None:
    """Extract content between square brackets: prefix[content].

    Args:
        prefix: text before the bracket
        text: full string to search

    Returns:
        Content inside brackets, or None if not found
    """
    pattern = regex_parenthesis(re.escape(prefix) + r"\[", r"[^\]]*", r"\]")
    match = re.search(pattern, text)
    return match.group(1) if match else None
