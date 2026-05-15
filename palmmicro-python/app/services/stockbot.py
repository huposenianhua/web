"""Stock bot query logic.

Translated from PHP stockbot.php.
Handles stock queries from bot users, including symbol lookup and text formatting.
"""

import re
from typing import List, Dict, Optional

from app.services.stocksymbol import StockSymbol
from app.services.stock import stock_get_reference, stock_get_fund_reference, stock_prefetch_extended_data
from app.services.mystockref import MyStockReference


MAX_BOT_STOCK = 32
MAX_BOT_MSG_LEN = 4096
BOT_EOL = '\n'


def _get_match_string(key: str) -> str:
    """Generate SQL LIKE pattern for fuzzy matching."""
    pattern = '%'
    key = key.strip()

    for char in key:
        pattern += char
        if len(char.encode('utf-8')) > 1:
            pattern += '%'

    if not pattern.endswith('%'):
        pattern += '%'

    return pattern


def _bot_get_stock_array(key: str) -> List[str]:
    """Get stock symbols matching the search key."""
    key = key.strip()
    if not key:
        return []

    symbols = []

    if key.isdigit():
        if len(key) == 6:
            key_int = int(key)
            if key_int < 1000:
                symbols.append(f'SH{key.zfill(6)}')
                symbols.append(f'SZ{key.zfill(6)}')
                return symbols[:2]
            else:
                symbol = key
                if len(symbol) == 6:
                    if symbol[0] == '6' or symbol[0] == '9':
                        symbols.append(f'SH{symbol}')
                    else:
                        symbols.append(f'SZ{symbol}')
                return symbols[:1]

    return [key]


def _bot_get_stock_text(symbol: str) -> str:
    """Get formatted text for a single stock symbol."""
    ref = stock_get_reference(symbol)

    if isinstance(ref, MyStockReference):
        ref.fetch()
        if ref.is_valid():
            return _format_stock_text(ref)

    return f"({symbol}:无数据){BOT_EOL}"


def _format_stock_text(ref: MyStockReference) -> str:
    """Format stock reference data as text.

    PHP: number_format($fPrice, $ref->GetPrecision())
    精度根据股票类型动态决定：基金3位，外汇4位，股票2位。
    """
    lines = []

    name = ref.name if ref.name else str(ref.symbol)
    price = ref.price
    change = ref.change
    change_percent = ref.change_percent

    if price > 0:
        # PHP: $iPrecision = $ref->GetPrecision()
        precision = ref.get_precision() if hasattr(ref, 'get_precision') else 2
        price_str = f"{price:.{precision}f}"
        if change != 0:
            change_str = f"{change:+.{precision}f} ({change_percent:+.2f}%)"
        else:
            change_str = ""

        lines.append(f"{name} {price_str} {change_str}")

    return ''.join(lines)


def _bot_get_stock_array_text(symbols: List[str], prefix: str = "") -> str:
    """Get combined text for multiple stock symbols."""
    result = prefix
    max_len = MAX_BOT_MSG_LEN

    stock_prefetch_extended_data(*symbols)

    for symbol in symbols:
        text = _bot_get_stock_text(symbol)
        if text:
            if len(result) + len(text) + len(BOT_EOL) < max_len:
                result += text + BOT_EOL
            else:
                break

    return result


def stock_bot_get_str(text: str) -> Optional[str]:
    """Process bot input and return stock information."""
    text = _clean_input(text)

    if not text:
        return None

    symbols = _bot_get_stock_array(text)

    if not symbols:
        return None

    if len(symbols) > 1:
        prefix = f"(至少发现{len(symbols)}个匹配：{' '.join(symbols)}){BOT_EOL}{BOT_EOL}"
    else:
        prefix = ""

    return _bot_get_stock_array_text(symbols, prefix)


def _clean_input(text: str) -> str:
    """Clean and normalize bot input text."""
    if not text:
        return ""

    text = text.replace('【', '').replace('】', '')
    text = text.replace('，', '').replace('。', '')
    text = text.replace('、', '').replace('"', '')
    text = text.replace('"', '').replace(''', '')
    text = text.replace(''', '').replace('：', '')
    text = text.replace('；', '')

    text = text.strip(" ,.:;~`{}[]'\"\n\r\t\v\x00")

    return text.strip()


def log_bot_visit(visit_type: str, message: str, source: str):
    """Log bot visit (placeholder)."""
    pass