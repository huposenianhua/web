"""File-based request cache.

Translated from PHP _stock.php functions:
  - StockSaveDebugFile() → save_debug_file()
  - StockDebugJson()     → debug_json()
  - StockDebugXml()      → debug_xml()
  - StockNeedFile()      → need_file()
  - StockSaveDebugCsv()  → save_debug_csv()

PHP原版的缓存机制:
1. 每次API请求的结果保存为本地文件
2. 默认60秒内不重复请求同一个URL（通过文件修改时间判断）
3. 请求失败时写入 'failed' 标记，也会阻止后续60秒内的请求
4. CSV缓存间隔为5分钟

缓存文件存储在 debug/ 目录下，按数据源分子目录:
  - debug/yahoo/XOP.txt          — Yahoo Finance JSON
  - debug/chinamoney/json.txt    — 中国货币网 JSON
  - debug/sina/sz162411.txt      — 新浪财经数据
  - debug/szse/SZ162411.txt      — 深交所数据
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# PHP: define('SECONDS_IN_MIN', 60);
SECONDS_IN_MIN = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400

# 缓存根目录
# PHP: _checkDebugPath() → UrlGetRootDir().'debug'
CACHE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'debug')


def _ensure_cache_dir(section: str) -> str:
    """确保缓存子目录存在，返回目录路径。

    PHP: DebugGetPath($strSection)
    """
    dir_path = os.path.join(CACHE_ROOT, section)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def _get_cache_file_path(section: str, symbol: str, suffix: str = '.txt') -> str:
    """获取缓存文件路径。

    PHP: DebugGetSymbolFile($strSection, $strSymbol)
    """
    dir_path = _ensure_cache_dir(section)
    # PHP: $str = str_replace(array('/', '+', ',', '^', '.', ':', '%'), '_', $str);
    safe_name = symbol.lower()
    for ch in ['/', '+', ',', '^', '.', ':', '%']:
        safe_name = safe_name.replace(ch, '_')
    return os.path.join(dir_path, safe_name + suffix)


def _get_cache_file_path_direct(path_name: str) -> str:
    """获取缓存文件路径（直接指定文件名）。

    PHP: DebugGetPathName($strFileName)
    """
    dir_path = os.path.dirname(path_name)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    return path_name


def need_file(file_path: str, interval: int = SECONDS_IN_MIN) -> bool:
    """检查缓存文件是否需要更新。

    PHP: StockNeedFile($strFileName, $iInterval)
      → $now_ymd->NeedFile($strFileName, $iInterval)

    PHP逻辑:
      clearstatcache(true, $strFileName);
      $iFileTime = file_exists($strFileName) ? filemtime($strFileName) : 1;
      return ($this->GetTick() < ($iFileTime + $iInterval)) ? false : $iFileTime;

    Returns:
        True  — 需要更新（文件不存在或已过期）
        False — 不需要更新（文件在间隔时间内）
    """
    now = time.time()

    if os.path.exists(file_path):
        file_mtime = os.path.getmtime(file_path)
        # PHP: 当前时间 < 文件修改时间 + 间隔 → 不需要更新
        if now < (file_mtime + interval):
            return False
        return True  # 文件存在但已过期

    return True  # 文件不存在


def save_debug_file(
    file_path: str,
    url: str,
    content_fetcher,
    interval: int = SECONDS_IN_MIN
):
    """请求URL并缓存结果到文件（核心函数）。

    PHP: StockSaveDebugFile($strPathName, $strUrl, $iInterval, $arExtraHeaders, $strFileName)

    PHP逻辑:
      if (StockNeedFile($strPathName, $iInterval) == false) return false;
      if ($str = url_get_contents($strUrl)) {
          file_put_contents($strPathName, $str);
          return $str;
      }
      file_put_contents($strPathName, 'failed');
      return false;

    Returns:
        False  — 缓存未过期（与PHP一致：不更新）
        str    — 请求成功，返回响应内容
        None   — 请求失败（PHP中也是返回false，但这里用None区分"未过期"和"失败"）
    """
    # PHP: if (StockNeedFile(...) == false) return false;
    if not need_file(file_path, interval):
        logger.debug(f"Cache fresh, skip request: {os.path.basename(file_path)}")
        return False  # PHP: return false; — 缓存未过期

    # PHP: if ($str = url_get_contents($strUrl))
    try:
        content = content_fetcher(url)
        if content:
            _ensure_cache_dir('')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Saved to {os.path.basename(file_path)}: {url}")
            return content  # PHP: return $str;
    except Exception as e:
        logger.error(f"Request failed for {url}: {e}")

    # PHP: DebugString('mark failed'); file_put_contents($strPathName, 'failed');
    try:
        _ensure_cache_dir('')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('failed')
        logger.debug(f"Marked failed: {os.path.basename(file_path)}")
    except Exception:
        pass

    return None  # PHP: return false; — 请求失败（用None区分"未过期"的False）


def read_cached_file(file_path: str) -> Optional[str]:
    """读取缓存文件内容。

    如果文件内容是 'failed'，返回None。

    Args:
        file_path: 缓存文件路径

    Returns:
        文件内容字符串，或None
    """
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if content == 'failed':
            return None
        return content
    except Exception:
        return None


def debug_json(
    file_path: str,
    url: str,
    content_fetcher,
    interval: int = SECONDS_IN_MIN
) -> Optional[Dict[str, Any]]:
    """请求JSON URL并缓存结果。

    PHP: StockDebugJson($strPathName, $strUrl, $iInterval, $arExtraHeaders, $strFileName)

    PHP逻辑（严格一致）:
      1. 调用 StockSaveDebugFile()
      2. StockSaveDebugFile() 内部检查 StockNeedFile()
      3. 如果缓存未过期 → StockNeedFile() 返回 false → StockSaveDebugFile() 返回 false → StockDebugJson() 返回 false
      4. 如果缓存过期 → 请求URL → 成功则保存文件并返回json_decode → 失败则写'failed'并返回false

    ⚠️ 重要：PHP在缓存未过期时返回 false，而不是返回缓存数据！
    缓存文件的作用是防止重复请求，不是用来读取旧数据的。
    调用方（如 _getYahooChartData）在收到 false 时应直接返回 false。

    Args:
        file_path: 缓存文件路径
        url: 要请求的URL
        content_fetcher: callable(url) -> str
        interval: 缓存间隔（秒）

    Returns:
        解析后的字典，失败返回None
    """
    # PHP: StockDebugJson 直接调用 StockSaveDebugFile，不单独读取缓存
    content = save_debug_file(file_path, url, content_fetcher, interval)

    if content is False:
        # PHP: StockSaveDebugFile 返回 false（缓存未过期）
        return None

    if content is not None:
        # PHP: json_decode($str, true)
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"JSON parse failed for {url}: {e}")

    return None


# ============================================================
# 便捷函数（按数据源分类）
# ============================================================

def get_yahoo_cache_path(symbol: str) -> str:
    """获取Yahoo Finance缓存文件路径。

    PHP: DebugGetYahooFileName($strSymbol) → DebugGetSymbolFile('yahoo', $strSymbol)
    """
    return _get_cache_file_path('yahoo', symbol)


def get_sina_cache_path(symbol: str) -> str:
    """获取新浪财经缓存文件路径。

    PHP: DebugGetSinaFileName($strSymbol) → DebugGetSymbolFile('sina', $strSymbol)
    """
    return _get_cache_file_path('sina', symbol)


def get_chinamoney_cache_path() -> str:
    """获取中国货币网缓存文件路径。

    PHP: DebugGetChinaMoneyFile() → DebugGetPath('chinamoney').'/json.txt'
    """
    dir_path = _ensure_cache_dir('chinamoney')
    return os.path.join(dir_path, 'json.txt')


def get_szse_cache_path(symbol: str) -> str:
    """获取深交所缓存文件路径。

    PHP: DebugGetSymbolFile('szse', $strSymbol)
    """
    return _get_cache_file_path('szse', symbol)


def get_config_cache_path(symbol: str) -> str:
    """获取配置缓存文件路径。

    PHP: DebugGetConfigFileName($strSymbol)
    """
    return _get_cache_file_path('config', symbol)


def unlink_config_file(symbol: str):
    """删除配置缓存文件。

    PHP: unlinkConfigFile($strSymbol) → unlinkEmptyFile(DebugGetConfigFileName($strSymbol))
    """
    path = get_config_cache_path(symbol)
    if os.path.exists(path):
        try:
            os.unlink(path)
        except Exception:
            pass
