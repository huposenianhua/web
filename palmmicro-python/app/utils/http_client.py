"""HTTP and URL utility module.

Translated from PHP url.php.
Provides HTTP request handling, IP extraction, URL parsing,
query string sanitization, and language detection.
"""

import hashlib
import ipaddress
from urllib.parse import urlparse

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
URL_PHP = ".php"
URL_CNPHP = "cn.php"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
}

# Tracking parameters to strip from query strings (from Facebook, WeChat, etc.)
_TRACKING_PARAMS = frozenset({
    "accessToken", "clicktime", "comment_from", "continueFlag", "enterid",
    "entryScene", "fbclid", "from", "ivk_sa", "isappinstalled", "jump_from",
    "key_name", "load_id", "scene", "share_token", "tdsourcetag", "tt_from",
    "wxshare_count", "xueqiu_comment_id", "xueqiu_private_from_source",
    "xueqiu_status_from_source", "xueqiu_status_id", "xueqiu_status_source",
})


# ---------------------------------------------------------------------------
# IP address utilities
# ---------------------------------------------------------------------------
def filter_valid_ip(str_ip: str | None) -> bool:
    """Validate an IPv4 address, rejecting private/reserved ranges.

    Translated from PHP filter_valid_ip().
    Equivalent to FILTER_VALIDATE_IP | FILTER_FLAG_IPV4 | FILTER_FLAG_NO_PRIV_RANGE.
    """
    if not str_ip:
        return False
    try:
        addr = ipaddress.IPv4Address(str_ip.strip())
        return not (
            addr.is_private or addr.is_reserved or addr.is_loopback
            or addr.is_link_local or addr.is_multicast
        )
    except (ipaddress.AddressValueError, ValueError):
        return False


def get_client_ip(
    x_forwarded_for: str | None = None,
    client_ip: str | None = None,
    remote_addr: str | None = None,
) -> str:
    """Extract client IP from request headers.

    Translated from PHP UrlGetIp().
    Priority: X-Forwarded-For > Client-IP > Remote-Addr.
    Raises ValueError if no valid IP found.
    """
    for candidate in (x_forwarded_for, client_ip, remote_addr):
        if candidate:
            ip = candidate.strip()
            if filter_valid_ip(ip):
                return ip
    raise ValueError("No valid client IP found")


# ---------------------------------------------------------------------------
# HTTP request utilities
# ---------------------------------------------------------------------------
def get_referer_header(referer: str) -> dict[str, str]:
    """Build a Referer HTTP header dict.

    Translated from PHP UrlGetRefererHeader().
    """
    return {"Referer": referer}


async def url_get_contents(
    url: str,
    extra_headers: dict[str, str] | None = None,
    timeout: float = 2.0,
    verify_ssl: bool = True,
) -> str | None:
    """Fetch URL content via HTTP GET (async).

    Translated from PHP url_get_contents().
    Uses httpx instead of cURL.

    Args:
        url: The URL to fetch.
        extra_headers: Additional HTTP headers merged with defaults.
        timeout: Connection/read timeout in seconds (default 2).
        verify_ssl: Whether to verify SSL certificates (default True).

    Returns:
        Response body as string, or None on failure.
    """
    headers = {**DEFAULT_HEADERS}
    if extra_headers:
        headers.update(extra_headers)

    # For https URLs, PHP disabled SSL verification
    actual_verify = verify_ssl
    if not actual_verify or url.startswith("https://"):
        pass  # keep caller's choice; original PHP always disabled SSL for https

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, verify=actual_verify,
        ) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPError as exc:
        import logging
        logging.getLogger(__name__).error("%s read error: %s", url, exc)
        return None


def url_get_contents_sync(
    url: str,
    extra_headers: dict[str, str] | None = None,
    timeout: float = 2.0,
    verify_ssl: bool = True,
) -> str | None:
    """Synchronous version of url_get_contents() for non-async contexts."""
    headers = {**DEFAULT_HEADERS}
    if extra_headers:
        headers.update(extra_headers)

    try:
        with httpx.Client(
            follow_redirects=True, timeout=timeout, verify=verify_ssl,
        ) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPError as exc:
        import logging
        logging.getLogger(__name__).error("%s read error: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# URL / path utilities (adapted from PHP $_SERVER equivalents)
# ---------------------------------------------------------------------------
def url_get_server(scheme: str = "http", host: str = "") -> str:
    """Build base server URL.

    Translated from PHP UrlGetServer().
    In FastAPI, use request.base_url instead.
    """
    return f"{scheme}://{host}"


def url_get_root_dir(root: str = "/") -> str:
    """Return document root with trailing slash.

    Translated from PHP UrlGetRootDir().
    """
    if root != "/":
        return root + "/"
    return root


def url_modify_root_filename(filename: str, root_dir: str = "/") -> str:
    """Prepend root directory if filename starts with '/'.

    Translated from PHP UrlModifyRootFileName().
    """
    if filename.startswith("/"):
        return url_get_root_dir(root_dir) + filename[1:]
    return filename


def url_get_path_name(path_name: str, root_dir: str = "/") -> str:
    """Convert absolute file path to web-relative path.

    Translated from PHP UrlGetPathName().
    """
    root = url_get_root_dir(root_dir)
    if path_name.startswith(root):
        return "/" + path_name[len(root):]
    return path_name


# ---------------------------------------------------------------------------
# String cleaning / query string sanitization
# ---------------------------------------------------------------------------
def url_clean_string(s: str) -> str:
    """Trim and strip backslashes from a string.

    Translated from PHP UrlCleanString().
    """
    return s.strip().replace("\\", "")


def sanitize_query_string(query_string: str) -> str | None:
    """Remove tracking parameters from a query string.

    Translated from PHP UrlGetQueryString().
    Returns cleaned query string, or None if empty.
    """
    if not query_string:
        return None

    parts = query_string.strip().split("&")
    clean_parts: list[str] = []
    for part in parts:
        param_name = part.split("=")[0]
        if param_name not in _TRACKING_PARAMS:
            clean_parts.append(part)

    result = "&".join(clean_parts)
    return result if result else None


def url_add_query(add: str, query_string: str | None = None) -> str:
    """Append a query parameter to an existing sanitized query string.

    Translated from PHP UrlAddQuery().
    """
    clean = sanitize_query_string(query_string) if query_string else None
    if clean:
        return f"{clean}&{add}"
    return add


def url_pass_query(query_string: str | None = None) -> str:
    """Return sanitized query string with '?' prefix, or empty string.

    Translated from PHP UrlPassQuery().
    """
    clean = sanitize_query_string(query_string) if query_string else None
    return f"?{clean}" if clean else ""


def url_get_query_value(params: dict, key: str) -> str | None:
    """Get a query parameter value, cleaned.

    Translated from PHP UrlGetQueryValue().
    """
    if key in params:
        val = str(params[key]).replace("=", "")
        return url_clean_string(val)
    return None


def url_get_query_display(params: dict, key: str, default: str = "") -> str:
    """Get a query parameter for display, with default fallback.

    Translated from PHP UrlGetQueryDisplay().
    """
    val = url_get_query_value(params, key)
    return val if val is not None else default


def url_get_query_int(params: dict, key: str, default: int = 0) -> int:
    """Get a query parameter as integer, with default fallback.

    Translated from PHP UrlGetQueryInt().
    """
    val = url_get_query_value(params, key)
    if val is not None:
        try:
            return int(val)
        except ValueError:
            return default
    return default


# ---------------------------------------------------------------------------
# URI validation and page type detection
# ---------------------------------------------------------------------------
def url_is_valid(url: str) -> bool:
    """Check if a URL is valid: not protocol-relative, no '..', contains .php.

    Translated from PHP UrlIsValid().
    """
    if url.startswith("//"):
        return False
    if ".." in url:
        return False
    if URL_PHP not in url:
        return False
    return True


def url_get_type(uri: str) -> str:
    """Detect URL type: 'cn.php' (Chinese) or '.php' (English).

    Translated from PHP UrlGetType().
    """
    if URL_CNPHP in uri:
        return URL_CNPHP
    if URL_PHP in uri:
        return URL_PHP
    if uri.endswith("cn"):
        return URL_CNPHP
    return URL_PHP


def _get_page(uri: str) -> str:
    """Extract page name from URI, stripping .php / cn.php suffix.

    Translated from PHP _getPage().
    """
    url_type = url_get_type(uri)
    pos = uri.lower().find(url_type)
    if pos > 0:
        return uri[:pos]
    if uri.endswith("cn"):
        return uri[:-2]
    return uri


def url_get_page(uri: str) -> str:
    """Extract page name from URI's basename.

    Translated from PHP UrlGetPage().
    """
    import os.path
    return _get_page(os.path.basename(uri))


def url_get_uri_page(uri: str) -> str:
    """Extract page name from full URI.

    Translated from PHP UrlGetUriPage().
    """
    return _get_page(uri)


def url_is_chinese(uri: str) -> bool:
    """Check if URI is Chinese version.

    Translated from PHP UrlIsChinese().
    """
    return url_get_type(uri) == URL_CNPHP


def url_is_english(uri: str) -> bool:
    """Check if URI is English version.

    Translated from PHP UrlIsEnglish().
    """
    return url_get_type(uri) == URL_PHP


def url_get_php(chinese: bool = True) -> str:
    """Return 'cn.php' for Chinese or '.php' for English.

    Translated from PHP UrlGetPhp().
    """
    return URL_CNPHP if chinese else URL_PHP


def url_get_unique_string(uri: str, query_string: str | None = None) -> str:
    """Generate unique string from page name and query string hash.

    Translated from PHP UrlGetUniqueString().
    """
    page = url_get_page(uri)
    clean_q = sanitize_query_string(query_string)
    if clean_q:
        return f"{page}{hashlib.md5(clean_q.encode()).hexdigest()}"
    return page


# ---------------------------------------------------------------------------
# HTTP Client class
# ---------------------------------------------------------------------------
class HttpClient:
    """Simple HTTP client wrapper for common requests."""
    
    def __init__(self):
        self._client = None
    
    def get(self, url: str, params: dict = None, timeout: float = 10.0, headers: dict = None) -> httpx.Response | None:
        """Make a synchronous GET request."""
        req_headers = {**DEFAULT_HEADERS}
        if headers:
            req_headers.update(headers)

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=timeout,
                verify=False,
            ) as client:
                resp = client.get(url, params=params, headers=req_headers)
                return resp
        except httpx.HTTPError:
            return None
    
    async def get_async(self, url: str, params: dict = None, timeout: float = 10.0, headers: dict = None) -> httpx.Response | None:
        """Make an asynchronous GET request."""
        req_headers = {**DEFAULT_HEADERS}
        if headers:
            req_headers.update(headers)

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=timeout,
                verify=False,
            ) as client:
                resp = await client.get(url, params=params, headers=req_headers)
                return resp
        except httpx.HTTPError:
            return None

    def post(self, url: str, data: dict = None, timeout: float = 10.0, headers: dict = None) -> httpx.Response | None:
        """Make a synchronous POST request."""
        req_headers = {**DEFAULT_HEADERS}
        if headers:
            req_headers.update(headers)

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=timeout,
                verify=False,
            ) as client:
                resp = client.post(url, data=data, headers=req_headers)
                return resp
        except httpx.HTTPError:
            return None
