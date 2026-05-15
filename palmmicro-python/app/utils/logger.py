"""Logging, float formatting, date helpers, and debug utilities.

Translated from PHP debug.php.
Uses Python's logging module for debug output instead of PHP's file_put_contents.
"""

import json
import logging
import os
import re
import time as _time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Constants (translated from PHP defines)
# ---------------------------------------------------------------------------
DEBUG_TIME_ZONE = "PRC"

SECONDS_IN_MIN = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400

# From MySQL DOUBLE(13,6) column precision
MIN_FLOAT_VAL = 0.0000005
FLOAT_PRECISION = 6
NETVALUE_PRECISION = 4

# Python timezone for PRC (Asia/Shanghai)
_PRC = ZoneInfo("Asia/Shanghai")

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------
_logger = logging.getLogger("palmmicro.debug")

# Configurable debug base directory (replaces PHP UrlGetRootDir().'debug')
DEBUG_BASE_DIR = os.environ.get("PALMMICRO_DEBUG_DIR", "/tmp/palmmicro_debug")


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Module name (e.g., __name__). If None, returns the root logger.

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(name)
    return _logger


def set_debug_base_dir(path: str) -> None:
    """Change the base directory for debug files."""
    global DEBUG_BASE_DIR
    DEBUG_BASE_DIR = path


# ---------------------------------------------------------------------------
# Float / number utilities
# ---------------------------------------------------------------------------
def is_zero_string(s: str) -> bool:
    """Check if a numeric string is effectively zero.

    Translated from PHP IsZeroString().
    """
    try:
        return abs(float(s)) < MIN_FLOAT_VAL
    except (ValueError, TypeError):
        return False


def strval_round(val: float, precision: int | None = None) -> str:
    """Convert float to string with auto or explicit precision.

    Translated from PHP strval_round().
    Auto precision: >=10 → 2 decimals, >=2 → 3 decimals, else 4 decimals.
    """
    if precision is None:
        f = abs(val)
        if f > (10 - MIN_FLOAT_VAL):
            precision = 2
        elif f > (2 - MIN_FLOAT_VAL):
            precision = 3
        else:
            precision = 4
    return str(round(val, precision))


def mysql_round(s, precision: int = FLOAT_PRECISION) -> str:
    """Parse float from string/float and round to precision.

    PHP: function mysql_round($str, $iPrecision = FLOAT_PRECISION)
         return strval_round(floatval($str), $iPrecision);

    PHP的mysql_round接收任意类型（弱类型），返回字符串。
    Python版本同时支持 str 和 float 输入。
    """
    try:
        return strval_round(float(s), precision)
    except (ValueError, TypeError):
        return str(s)


def strval_round_join(values: list[float], sep: str = ", ") -> str:
    """Join float values as rounded strings.

    Translated from PHP strval_round_implode().
    """
    return sep.join(strval_round(v) for v in values)


def explode_float(s: str, sep: str = ",") -> list[float]:
    """Split a string by separator and convert each part to float.

    Translated from PHP explode_float().
    """
    parts = s.split(sep)
    result: list[float] = []
    for p in parts:
        p = p.strip()
        if p:
            try:
                result.append(float(p))
            except ValueError:
                pass
    return result


def rtrim0(s: str) -> str:
    """Remove trailing zeros by converting to float and back to string.

    Translated from PHP rtrim0().
    """
    try:
        return str(float(s))
    except (ValueError, TypeError):
        return s


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------
def filter_var_email(email: str) -> str | None:
    """Validate email format.

    Translated from PHP filter_var_email().
    Returns the email if valid, None otherwise.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return email if re.match(pattern, email) else None


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------
def unlink_empty_file(filename: str) -> None:
    """Delete a file if it exists; if deletion fails, truncate it.

    Translated from PHP unlinkEmptyFile().
    """
    try:
        os.remove(filename)
    except OSError:
        try:
            with open(filename, "w") as f:
                pass  # truncate
        except OSError:
            pass


# ---------------------------------------------------------------------------
# JSON encode/decode helpers
# ---------------------------------------------------------------------------
def debug_encode(data) -> str:
    """JSON-encode data, stripping the outer { and }.

    Translated from PHP DebugEncode().
    Useful for building partial JSON strings.
    """
    s = json.dumps(data, ensure_ascii=False)
    if len(s) >= 2 and s[0] == "{" and s[-1] == "}":
        return s[1:-1]
    return s


def debug_decode(s: str) -> dict | list | None:
    """JSON-decode a partial JSON string by wrapping in { }.

    Translated from PHP DebugDecode().
    """
    try:
        return json.loads("{" + s + "}")
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Date / time formatting
# ---------------------------------------------------------------------------
def debug_format_date(
    fmt: str,
    timestamp: float | None = None,
    tz: str | None = DEBUG_TIME_ZONE,
) -> str:
    """Format a timestamp using strftime format string.

    Translated from PHP DebugFormat_date().

    Args:
        fmt: strftime format string (PHP date() format converted).
        timestamp: Unix timestamp (default: current time).
        tz: Timezone name (default: 'PRC'). Pass None for system local timezone.
    """
    if timestamp is None:
        timestamp = _time.time()
    if tz is None:
        dt = datetime.fromtimestamp(timestamp)
    else:
        zone = ZoneInfo(tz)
        dt = datetime.fromtimestamp(timestamp, tz=zone)
    return dt.strftime(fmt)


def debug_get_date(timestamp: float | None = None, tz: str = DEBUG_TIME_ZONE) -> str:
    """Return date string 'YYYY-MM-DD'.

    Translated from PHP DebugGetDate().
    """
    return debug_format_date("%Y-%m-%d", timestamp, tz)


def debug_get_time(timestamp: float | None = None, tz: str = DEBUG_TIME_ZONE) -> str:
    """Return time string 'HH:MM:SS'.

    Translated from PHP DebugGetTime().
    """
    return debug_format_date("%H:%M:%S", timestamp, tz)


def debug_get_datetime(
    timestamp: float | None = None, tz: str = DEBUG_TIME_ZONE,
) -> str:
    """Return datetime string 'YYYY-MM-DD HH:MM:SS'.

    Translated from PHP DebugGetDateTime().
    """
    return debug_get_date(timestamp, tz) + " " + debug_get_time(timestamp, tz)


def get_hm(hms: str) -> str:
    """Extract 'HH:MM' from 'HH:MM:SS' string.

    Translated from PHP GetHM().
    """
    return hms[:5]


# ---------------------------------------------------------------------------
# Stopwatch / timing
# ---------------------------------------------------------------------------
def debug_stopwatch(start: float | None = None, precision: int = 2) -> str:
    """Return elapsed time display string.

    Translated from PHP DebugGetStopWatchDisplay().
    """
    if start is None:
        start = _time.time()
    elapsed = _time.time() - start
    return f" ({elapsed:.{precision}f}s)"


def debug_now(msg: str = "") -> None:
    """Log a message with elapsed time since request start.

    Translated from PHP DebugNow().
    """
    _logger.info("%s%s", msg, debug_stopwatch())


# ---------------------------------------------------------------------------
# Debug file path management
# ---------------------------------------------------------------------------
def _check_debug_path() -> str:
    """Ensure the debug base directory exists and return it."""
    os.makedirs(DEBUG_BASE_DIR, exist_ok=True)
    return DEBUG_BASE_DIR


def debug_get_pathname(filename: str) -> str:
    """Return full path for a debug file.

    Translated from PHP DebugGetPathName().
    """
    return os.path.join(_check_debug_path(), filename)


def debug_get_file() -> str:
    """Return path to main debug log file.

    Translated from PHP DebugGetFile().
    """
    return debug_get_pathname("debug.txt")


def debug_get_netvalue_file(symbol: str) -> str:
    """Return path to net value cache file for a symbol.

    Translated from PHP DebugGetNetValueFile().
    """
    return debug_get_pathname(f"netvalue_{symbol}.txt")


def debug_get_path(section: str) -> str:
    """Return path to a debug sub-directory, creating it if needed.

    Translated from PHP DebugGetPath().
    """
    path = os.path.join(_check_debug_path(), section)
    os.makedirs(path, exist_ok=True)
    return path


def debug_get_image_name(name: str) -> str:
    """Return path to a debug image file.

    Translated from PHP DebugGetImageName().
    """
    return os.path.join(debug_get_path("image"), f"{name}.jpg")


def debug_get_wechat_image_name(name: str) -> str:
    """Return path to a WeChat debug image file.

    Translated from PHP DebugGetWechatImageName().
    """
    return os.path.join(debug_get_path("wechat"), f"{name}.jpg")


def debug_get_font_name(name: str) -> str:
    """Return path to a debug font file.

    Translated from PHP DebugGetFontName().
    """
    return os.path.join(debug_get_path("font"), f"{name}.ttf")


def debug_get_chinamoney_file() -> str:
    """Return path to ChinaMoney JSON cache file.

    Translated from PHP DebugGetChinaMoneyFile().
    """
    return os.path.join(debug_get_path("chinamoney"), "json.txt")


def debug_get_symbol_file(section: str, symbol: str) -> str:
    """Return path to a symbol-specific cache file.

    Translated from PHP DebugGetSymbolFile().
    Special characters in symbol are replaced with '_'.
    """
    path = debug_get_path(section)
    safe = symbol.lower()
    for ch in "/+,.^:%":
        safe = safe.replace(ch, "_")
    return os.path.join(path, f"{safe}.txt")


def debug_get_sina_filename(symbol: str) -> str:
    """Return Sina data cache file path.

    Translated from PHP DebugGetSinaFileName().
    """
    return debug_get_symbol_file("sina", symbol)


def debug_get_yahoo_filename(symbol: str) -> str:
    """Return Yahoo data cache file path.

    Translated from PHP DebugGetYahooFileName().
    """
    return debug_get_symbol_file("yahoo", symbol)


def debug_get_config_filename(symbol: str) -> str:
    """Return config cache file path.

    Translated from PHP DebugGetConfigFileName().
    """
    return debug_get_symbol_file("config", symbol)


def unlink_config_file(symbol: str) -> None:
    """Delete or truncate the config file for a symbol.

    Translated from PHP unlinkConfigFile().
    """
    unlink_empty_file(debug_get_config_filename(symbol))


# ---------------------------------------------------------------------------
# Core logging functions (replacing PHP DebugString/DebugVal/DebugPrint)
# ---------------------------------------------------------------------------
def debug_string(msg: str, admin_only: bool = False) -> None:
    """Write a message to the debug log.

    Translated from PHP DebugString().
    In the FastAPI version, admin_only can be enforced via middleware.
    """
    if not msg:
        msg = "(false)"
    time_str = debug_get_time()
    # Strip HTML tags like PHP strip_tags()
    clean_msg = re.sub(r"<[^>]+>", "", str(msg))
    _logger.info("%s %s", time_str, clean_msg)


def debug_val(val, prefix: str | None = None, admin_only: bool = False) -> None:
    """Log a single value.

    Translated from PHP DebugVal().
    """
    s = str(val)
    if prefix:
        s = f"{prefix}: {s}"
    debug_string(s, admin_only)


def debug_print(data, prefix: str | None = None, admin_only: bool = False) -> None:
    """Log a data structure (dict, list, etc.).

    Translated from PHP DebugPrint().
    """
    import pprint
    header = prefix if prefix else "Debug print_r begin ..."
    body = pprint.pformat(data, width=120)
    debug_string(f"{header}\n{body}", admin_only)


# ---------------------------------------------------------------------------
# Role checking (stubs for future integration)
# ---------------------------------------------------------------------------
def debug_is_palmmicro() -> bool:
    """Check if current user is Palmmicro admin.

    Translated from PHP DebugIsPalmmicro().
    TODO: integrate with FastAPI authentication.
    """
    return False


def debug_is_admin() -> bool:
    """Check if current user has admin privileges.

    Translated from PHP DebugIsAdmin().
    TODO: integrate with FastAPI authentication.
    """
    return False
