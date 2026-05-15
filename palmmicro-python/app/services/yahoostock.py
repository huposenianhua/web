"""Yahoo Finance data fetcher.

Translated from PHP stock/yahoostock.php.
Uses Yahoo Finance v7 chart JSON API (consistent with PHP original).
Historical data is stored in database (stockhistory table) and queried first.

PHP对应:
  - _getYahooChartData()   → _get_yahoo_chart_data()
  - _yahooStockGetData()   → _yahoo_stock_get_data()
  - YahooGetNetValue()     → get_net_value()
  - YahooUpdateNetValue()  → update_net_value()
  - UpdateYahooHistoryChart() → update_history_chart()
"""

import json
import math
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.services.stocksymbol import StockSymbol
from app.utils.http_client import HttpClient, DEFAULT_HEADERS
from app.utils.logger import get_logger, MIN_FLOAT_VAL, FLOAT_PRECISION, mysql_round
from app.utils.file_cache import (
    debug_json, get_yahoo_cache_path, SECONDS_IN_MIN,
)

logger = get_logger(__name__)

_yahoo_crumb = ''
_yahoo_cookies_file = ''


def _ensure_yahoo_auth() -> bool:
    """Get Yahoo crumb and cookies via curl.

    Uses subprocess+curl because httpx SSL cannot reach Yahoo from this network.
    Falls back silently if Yahoo is unreachable.
    """
    global _yahoo_crumb, _yahoo_cookies_file

    if _yahoo_crumb:
        return True

    import subprocess, tempfile, os

    try:
        fd, _yahoo_cookies_file = tempfile.mkstemp(suffix='.txt', prefix='yahoo_')
        os.close(fd)

        r = subprocess.run(
            ['curl', '-sk', '-c', _yahoo_cookies_file, 'https://fc.yahoo.com/'],
            capture_output=True, text=True, timeout=15,
        )

        r2 = subprocess.run(
            ['curl', '-sk', '-b', _yahoo_cookies_file,
             'https://query1.finance.yahoo.com/v1/test/getcrumb'],
            capture_output=True, text=True, timeout=15,
        )

        crumb = r2.stdout.strip()
        if crumb and 'Edge' not in crumb and 'Too Many' not in crumb and len(crumb) > 5:
            _yahoo_crumb = crumb
            logger.info(f"Yahoo auth OK: crumb={_yahoo_crumb[:20]}...")
            return True
    except Exception as e:
        logger.warning(f"Yahoo auth failed: {e}")

    return False


# ============================================================
# Constants (matching PHP)
# ============================================================

# Yahoo Finance v7 base URL
# PHP: GetYahooDataUrl('7') → 'https://query1.finance.yahoo.com/v7/finance'
YAHOO_DATA_URL = 'https://query1.finance.yahoo.com/v7/finance'

# PHP: YAHOO_INDEX_CHAR = '^'
YAHOO_INDEX_CHAR = '^'

# PHP: MIN_FLOAT_VAL — 最小有效浮点值（统一定义在 utils/logger.py）
# PHP: MIN_FLOAT_VAL = 0.0000005 (对应MySQL DOUBLE(13,6))
# PHP: mysql_round — 统一定义在 utils/logger.py，返回字符串（与PHP一致）


# ============================================================
# Yahoo symbol helpers (matching PHP)
# ============================================================

def build_yahoo_net_value_symbol(symbol: str, suffix: str = 'IV') -> Optional[str]:
    """Build Yahoo net value symbol.

    PHP: BuildYahooNetValueSymbol($strSymbol, 'IV')
    Example: XOP → ^XOP-IV
    """
    if not symbol:
        return None
    return f"{YAHOO_INDEX_CHAR}{symbol}-{suffix}"


# ============================================================
# Core: Yahoo chart JSON API
# ============================================================

def _get_yahoo_chart_data(
    yahoo_symbol: str,
    range_str: str = '2y',
    interval: str = '1d'
) -> Optional[Dict[str, Any]]:
    """Fetch and parse Yahoo Finance chart JSON data (with file cache).

    PHP对应: _getYahooChartData($strYahooSymbol, $strFileName, $strRange)
      → StockDebugJson($strFileName, $strUrl)

    缓存机制（与PHP一致）:
      1. 首次请求：调用Yahoo API，结果保存到 debug/yahoo/XOP.txt
      2. 60秒内再次请求：直接读取缓存文件，不调用API
      3. 请求失败：写入 'failed' 标记，60秒内不再重试
      4. 60秒后：缓存过期，重新请求

    URL格式: https://query1.finance.yahoo.com/v7/finance/chart/XOP?range=2y&interval=1d&indicators=quote&includeTimestamps=true

    Args:
        yahoo_symbol: Yahoo格式代码，如 'XOP', '^XOP-IV'
        range_str: 时间范围，如 '1d', '5d', '1mo', '2y'
        interval: 数据间隔，如 '1d', '1wk', '1mo'

    Returns:
        解析后的 result 数组（arResult），包含 timestamp, indicators 等
        失败返回 None
    """
    url = f"{YAHOO_DATA_URL}/chart/{yahoo_symbol}"
    params = {
        'range': range_str,
        'interval': interval,
        'indicators': 'quote',
        'includeTimestamps': 'true'
    }

    # 构建带参数的缓存文件名（不同range/interval使用不同缓存）
    cache_key = f"{yahoo_symbol}_{range_str}_{interval}"
    cache_path = get_yahoo_cache_path(cache_key)

    # PHP: StockDebugJson($strFileName, $strUrl, SECONDS_IN_MIN)
    # 使用文件缓存：60秒内不重复请求
    http_client = HttpClient()

    def _fetch_content(url_str: str) -> Optional[str]:
        """实际执行HTTP请求（传给debug_json的回调），使用curl"""
        try:
            _ensure_yahoo_auth()
            import subprocess

            cmd = ['curl', '-sk', '-H', f"User-Agent: {DEFAULT_HEADERS['User-Agent']}"]
            if _yahoo_crumb:
                url_str = f"{url_str}&crumb={_yahoo_crumb}" if '?' in url_str else f"{url_str}?crumb={_yahoo_crumb}"
            if _yahoo_cookies_file:
                cmd.extend(['-b', _yahoo_cookies_file])
            cmd.append(url_str)

            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.stdout and r.stdout.strip():
                return r.stdout
            logger.warning(f"Yahoo chart empty response for {yahoo_symbol}")
        except Exception as e:
            logger.error(f"Yahoo chart request failed for {yahoo_symbol}: {e}")
        return None

    ar = debug_json(cache_path, url, _fetch_content, interval=SECONDS_IN_MIN)
    if ar is None:
        return None

    # PHP: if (!isset($ar['chart']))
    if 'chart' not in ar:
        logger.warning(f"Yahoo chart: no 'chart' key for {yahoo_symbol}")
        return None

    ar_chart = ar['chart']
    # PHP: if (!isset($arChart['result']))
    if 'result' not in ar_chart or not ar_chart['result']:
        logger.warning(f"Yahoo chart: no 'result' key for {yahoo_symbol}")
        return None

    ar_result = ar_chart['result'][0]

    # PHP: if (!isset($arResult['timestamp']))
    if 'timestamp' not in ar_result or not ar_result['timestamp']:
        logger.warning(f"Yahoo chart: no 'timestamp' for {yahoo_symbol}")
        return None

    ar_indicators = ar_result.get('indicators', {})
    # PHP: if (!isset($arIndicators['quote']))
    if 'quote' not in ar_indicators or not ar_indicators['quote']:
        logger.warning(f"Yahoo chart: no 'quote' indicator for {yahoo_symbol}")
        return None
    # PHP: if (!isset($arIndicators['adjclose']))
    if 'adjclose' not in ar_indicators or not ar_indicators['adjclose']:
        logger.warning(f"Yahoo chart: no 'adjclose' indicator for {yahoo_symbol}")
        return None

    return ar_result


def _parse_chart_result(ar_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Yahoo chart result into list of daily records.

    PHP对应: UpdateYahooHistoryChart() 中的循环解析逻辑

    Returns:
        [{'date': '2024-01-15', 'open': 100.0, 'high': 102.0, 'low': 99.0,
          'close': 101.0, 'volume': 1000000, 'adjclose': 100.5}, ...]
    """
    ar_timestamp = ar_result['timestamp']
    ar_indicators = ar_result['indicators']

    ar_quote = ar_indicators['quote'][0]
    ar_low = ar_quote.get('low', [])
    ar_volume = ar_quote.get('volume', [])
    ar_open = ar_quote.get('open', [])
    ar_high = ar_quote.get('high', [])
    ar_close = ar_quote.get('close', [])
    ar_adjclose = ar_indicators['adjclose'][0].get('adjclose', [])

    records = []
    last_date = ''

    for i in range(len(ar_timestamp)):
        # PHP: $ymd = new TickYMD(intval($arTimeStamp[$i]));
        #     $strDate = $ymd->GetYMD();
        ts = int(ar_timestamp[i])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        str_date = dt.strftime('%Y-%m-%d')

        # PHP: if ($strDate == $strLastDate) continue; // future has continuous data 23h/day
        if str_date == last_date:
            continue
        last_date = str_date

        str_open = ar_open[i] if i < len(ar_open) else None
        str_high = ar_high[i] if i < len(ar_high) else None
        str_low = ar_low[i] if i < len(ar_low) else None
        str_close = ar_close[i] if i < len(ar_close) else None
        str_volume = ar_volume[i] if i < len(ar_volume) else None
        str_adjclose = ar_adjclose[i] if i < len(ar_adjclose) else None

        # PHP: if ($strClose == '-' || $strClose == 'null' || IsZeroString($strClose))
        if str_close is None or str_close == '-' or str_close == 'null':
            logger.debug(f"Empty close data: {str_date}")
            continue

        # PHP: if (IsZeroString($strVolume)) → skip zero volume (holiday check)
        if str_volume is not None and int(str_volume) == 0:
            logger.debug(f"Zero volume, holiday? {str_date}")
            continue

        records.append({
            'date': str_date,
            'open': mysql_round(str_open) if str_open is not None else 0.0,
            'high': mysql_round(str_high) if str_high is not None else 0.0,
            'low': mysql_round(str_low) if str_low is not None else 0.0,
            'close': mysql_round(str_close),
            'volume': int(str_volume) if str_volume is not None else 0,
            'adjclose': mysql_round(str_adjclose) if str_adjclose is not None else mysql_round(str_close),
        })

    return records


# ============================================================
# Database operations (matching PHP SQL layer)
# ============================================================

class YahooStockDB:
    """Database operations for Yahoo stock data.

    Encapsulates all DB read/write for stockhistory and netvaluehistory tables.
    PHP对应: StockHistorySql, NetValueHistorySql (DailyCloseSql family)
    """

    def __init__(self, db: Session):
        self.db = db

    # ------ stockhistory 表操作 ------

    def get_stock_id(self, symbol: str) -> Optional[int]:
        """Get stock_id from stock table by symbol.

        PHP对应: SqlGetStockId($strSymbol)
        """
        from app.models.stock import Stock
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            from app.services.stocksymbol import StockSymbol
            sym = StockSymbol(symbol)
            if sym.is_symbol_a():
                stock = self.db.query(Stock).filter(Stock.symbol == sym.get_digit_a()).first()
            if not stock:
                bare = symbol.lstrip('SH').lstrip('SZ')
                if bare != symbol:
                    stock = self.db.query(Stock).filter(Stock.symbol == bare).first()
        return stock.id if stock else None

    def ensure_stock_id(self, symbol: str, chinese_name: str = '') -> Optional[int]:
        """Get or create stock_id.

        PHP对应: $sql->InsertSymbol($strSymbol, $chineseName) + $sql->GetId($strSymbol)
        """
        from app.models.stock import Stock
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            stock = Stock(symbol=symbol, name=chinese_name or symbol)
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        return stock.id

    def write_history(
        self, stock_id: int, date_str: str,
        close, volume: int, adjclose,
        open_price=0.0, high=0.0, low=0.0
    ) -> bool:
        """Write daily history record (INSERT or UPDATE).

        PHP对应: $his_sql->WriteHistory($strStockId, $strDate, $strClose, $strVolume, $strAdjClose)
        PHP中参数都是字符串（mysql_round返回值），SQL驱动自动转换。
        Python版本同时支持 str 和 float（与PHP弱类型一致）。
        Returns True if a new record was inserted, False if already existed.
        """
        from app.models.market_data import StockHistory
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        dt = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Use MySQL INSERT ... ON DUPLICATE KEY UPDATE (matching PHP WriteDaily behavior)
        stmt = mysql_insert(StockHistory).values(
            stock_id=stock_id,
            date=dt,
            close=close,
            volume=volume,
            adjclose=adjclose,
        )
        stmt = stmt.on_duplicate_key_update(
            close=stmt.inserted.close,
            volume=stmt.inserted.volume,
            adjclose=stmt.inserted.adjclose,
        )
        self.db.execute(stmt)
        self.db.commit()

        # Check if it was an insert or update by querying
        existing = self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.date == dt
        ).first()
        return existing is not None

    def get_history_by_date(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get close price from stockhistory by date.

        PHP对应: SqlGetHistoryByDate($strStockId, $strDate)
        """
        from app.models.market_data import StockHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.date == dt
        ).first()
        return record.close if record else None

    def get_adjclose_by_date(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get adjclose from stockhistory by date.

        PHP对应: SqlGetAdjCloseByDate($strStockId, $strDate)
        """
        from app.models.market_data import StockHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.date == dt
        ).first()
        return record.adjclose if record else None

    def get_close_prev(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get previous day's close price.

        PHP对应: $his_sql->GetClosePrev($strStockId, $strDate)
        """
        from app.models.market_data import StockHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.date < dt
        ).order_by(StockHistory.date.desc()).first()
        return record.close if record else None

    def count_history(self, stock_id: int) -> int:
        """Count total history records.

        PHP对应: $his_sql->Count($strStockId)
        """
        from app.models.market_data import StockHistory
        return self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id
        ).count()

    def delete_by_zero_volume(self, stock_id: int):
        """Delete records with zero volume (holiday cleanup).

        PHP对应: $his_sql->DeleteByZeroVolume($strStockId)
        """
        from app.models.market_data import StockHistory
        self.db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.volume == 0
        ).delete()
        self.db.commit()

    # ------ netvaluehistory 表操作 ------

    def write_net_value(self, stock_id: int, date_str: str, net_value) -> bool:
        """Write daily net value record.

        PHP对应: $net_sql->WriteDaily($strStockId, $strDate, $strNetValue)
        PHP中$strNetValue是字符串（mysql_round返回值）。
        Returns True if a new record was inserted.
        """
        from app.models.market_data import NetValueHistory
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        dt = datetime.strptime(date_str, '%Y-%m-%d').date()

        stmt = mysql_insert(NetValueHistory).values(
            stock_id=stock_id,
            date=dt,
            close=net_value,
        )
        stmt = stmt.on_duplicate_key_update(
            close=stmt.inserted.close,
        )
        self.db.execute(stmt)
        self.db.commit()
        return True

    def get_net_value_by_date(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get net value by date.

        PHP对应: SqlGetNetValueByDate($strStockId, $strDate)
        """
        from app.models.market_data import NetValueHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id,
            NetValueHistory.date == dt
        ).first()
        return record.close if record else None

    def get_latest_net_value_before(self, stock_id: int, date_str: str) -> Optional[Tuple[float, str]]:
        """Get most recent net value on or before given date.

        Returns (price, actual_date) or None.
        """
        from app.models.market_data import NetValueHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id,
            NetValueHistory.date <= dt
        ).order_by(NetValueHistory.date.desc()).first()
        if record:
            return record.close, record.date.strftime('%Y-%m-%d')
        return None

    def get_net_value_prev(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get previous day's net value.

        PHP对应: $net_sql->GetClosePrev($strStockId, $strDate)
        """
        from app.models.market_data import NetValueHistory
        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = self.db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id,
            NetValueHistory.date < dt
        ).order_by(NetValueHistory.date.desc()).first()
        return record.close if record else None

    def get_net_value_record_now(self, stock_id: int) -> Optional[Dict]:
        """Get the latest net value record.

        PHP对应: $net_sql->GetRecordNow($strStockId)
        """
        from app.models.market_data import NetValueHistory
        record = self.db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id
        ).order_by(NetValueHistory.date.desc()).first()
        if record:
            return {'date': record.date.strftime('%Y-%m-%d'), 'close': record.close}
        return None

    def count_net_value(self, stock_id: int) -> int:
        """Count net value records.

        PHP对应: $net_sql->Count($strStockId)
        """
        from app.models.market_data import NetValueHistory
        return self.db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id
        ).count()

    # ------ stockhistorydate 表操作 ------

    def get_history_date(self, stock_id: int) -> Optional[str]:
        """Get the recorded earliest date for stock history.

        PHP对应: $date_sql->ReadDate($strStockId)
        """
        from app.models.market_data import StockHistoryDate
        record = self.db.query(StockHistoryDate).filter(
            StockHistoryDate.id == stock_id
        ).first()
        return record.date.strftime('%Y-%m-%d') if record else None

    def write_history_date(self, stock_id: int, date_str: str):
        """Record the current date for stock history update.

        PHP对应: $date_sql->WriteDate($strStockId, $strCurDate)
        """
        from app.models.market_data import StockHistoryDate
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        stmt = mysql_insert(StockHistoryDate).values(
            id=stock_id,
            date=dt,
        )
        stmt = stmt.on_duplicate_key_update(date=dt)
        self.db.execute(stmt)
        self.db.commit()


# ============================================================
# Yahoo update functions (matching PHP yahoostock.php)
# ============================================================

# PHP: YahooUpdateNetValue — 美股收盘检查时间（16:55 = 1655）
YAHOO_MARKET_CLOSE_HOUR_MINUTE = 1655


def yahoo_update_net_value(ref, db: Session) -> bool:
    """Update net value from Yahoo Finance, with dedup and time checks.

    PHP: function YahooUpdateNetValue($ref)
      1. if ($ref->HasData() == false) return;
      2. if (($strNetValueSymbol = _yahooGetNetValueSymbol($ref, $strSymbol)) === false) return;
      3. if ($net_sql->GetRecord($strStockId, $strDate)) return;  // already have today's data
      4. if ($now_ymd->GetYMD() == $strDate && $iHourMinute < 1655) return;  // market not closed
      5. return _yahooStockGetData($strNetValueSymbol, $strStockId);

    Args:
        ref: YahooStock instance (must have sql_id, date, symbol)
        db: SQLAlchemy session

    Returns:
        True if data was updated, False otherwise
    """
    from app.models.market_data import NetValueHistory

    # PHP: if ($ref->HasData() == false) return;
    if not ref.has_data():
        return False

    symbol = ref.symbol
    sym = StockSymbol(symbol)

    # PHP: _yahooGetNetValueSymbol — 指数/期货/A股不处理
    if sym.is_index():
        return False
    if hasattr(sym, 'is_sina_future') and sym.is_sina_future():
        return False
    if sym.is_symbol_a() or sym.is_symbol_h():
        return False

    # PHP: 特殊symbol不处理
    if symbol in ('IBB', 'QQQ', 'USO'):
        return False

    stock_id = ref.sql_id
    if not stock_id:
        return False

    ref_date = ref.date
    if not ref_date:
        return False

    prev_close = getattr(ref, '_prev_close', 0)
    prev_date = getattr(ref, '_prev_date', '')
    if not prev_close or not prev_date:
        price, date_str, pc, pd = ref._fetch_sina_us_price()
        if pc > 0 and pd:
            prev_close = pc
            prev_date = pd
    if prev_close > 0 and prev_date:
        db_ops = YahooStockDB(db)
        prev_existing = db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == stock_id,
            NetValueHistory.date == datetime.strptime(prev_date, '%Y-%m-%d').date()
        ).first()
        if not prev_existing:
            prev_written = db_ops.write_net_value(stock_id, prev_date, prev_close)
            if prev_written:
                logger.info(f"Fallback: wrote {symbol} prev_close {prev_date} {prev_close} from Sina data")

    # PHP: if ($net_sql->GetRecord($strStockId, $strDate)) return;
    dt = datetime.strptime(ref_date, '%Y-%m-%d').date()
    existing = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id,
        NetValueHistory.date == dt
    ).first()
    if existing:
        logger.debug(f"YahooUpdateNetValue: already have {symbol} {ref_date}")
        return False

    # PHP: if ($now_ymd->GetYMD() == $strDate && $iHourMinute < 1655) return;
    tz_sh = timezone(timedelta(hours=8))
    now_sh = datetime.now(tz_sh)
    today_str = now_sh.strftime('%Y-%m-%d')
    hour_minute = now_sh.hour * 100 + now_sh.minute

    if today_str == ref_date and hour_minute < YAHOO_MARKET_CLOSE_HOUR_MINUTE:
        logger.debug(f"YahooUpdateNetValue: market not closed yet {hour_minute}")
        return False

    # PHP: return _yahooStockGetData($strNetValueSymbol, $strStockId);
    net_value_symbol = build_yahoo_net_value_symbol(symbol)
    if not net_value_symbol:
        return False

    try:
        result = _yahoo_stock_get_data(net_value_symbol, stock_id, db)
        if result:
            return True
    except Exception as e:
        logger.warning(f"yahoo_update_net_value: _yahoo_stock_get_data failed for {symbol}: {e}")

    if ref._price > 0 and ref._date:
        db_ops = YahooStockDB(db)
        written = db_ops.write_net_value(stock_id, ref._date, ref._price)
        if written:
            logger.info(f"Fallback: wrote {symbol} {ref._date} {ref._price} from Sina data")
        prev_close = getattr(ref, '_prev_close', 0)
        prev_date = getattr(ref, '_prev_date', '')
        if prev_close > 0 and prev_date:
            prev_written = db_ops.write_net_value(stock_id, prev_date, prev_close)
            if prev_written:
                logger.info(f"Fallback: wrote {symbol} prev_close {prev_date} {prev_close} from Sina data")
            return True
        if written:
            return True

    return False


def _yahoo_stock_get_data(yahoo_symbol: str, stock_id: int, db: Session) -> bool:
    """Fetch Yahoo chart data and write to netvaluehistory.

    PHP: function _yahooStockGetData($strSymbol, $strStockId)
      if ($arResult = _getYahooChartData($strSymbol, ..., '1d')) {
          for each timestamp:
              $net_sql->WriteDaily($strStockId, $strDate, $strNetValue);
      }
    """
    ar_result = _get_yahoo_chart_data(yahoo_symbol, range_str='1d', interval='1d')

    if not ar_result:
        return False

    records = _parse_chart_result(ar_result)
    if not records:
        return False

    db_writer = YahooStockDB(db)
    inserted = False
    for rec in records:
        if db_writer.write_net_value(stock_id, rec['date'], rec['adjclose']):
            inserted = True

    return inserted


# ============================================================
# Main class: YahooStock
# ============================================================

class YahooStock:
    """Yahoo Finance data fetcher with database persistence.

    与PHP原版一致的行为:
    1. 使用 Yahoo Finance v7 chart JSON API
    2. 历史数据存入数据库（stockhistory / netvaluehistory 表）
    3. 优先从数据库查询，没有再从Yahoo拉取
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        self._symbol = StockSymbol(symbol)
        self._db = db
        self._http_client = HttpClient()
        self._error = ""
        self._date: str = ""
        self._price: float = 0.0
        self._sql_id: Optional[int] = None

        if db:
            try:
                db_ops = YahooStockDB(db)
                self._sql_id = db_ops.ensure_stock_id(self.symbol)
            except Exception:
                pass

    @property
    def error(self) -> str:
        return self._error

    @property
    def symbol(self) -> str:
        return self._symbol.symbol

    @property
    def yahoo_symbol(self) -> str:
        return self._symbol.get_yahoo_symbol()

    @property
    def is_index(self) -> bool:
        return self._symbol.is_index()

    @property
    def date(self) -> str:
        return self._date

    @property
    def price(self) -> float:
        return self._price

    @property
    def sql_id(self) -> Optional[int]:
        return self._sql_id

    def get_price_at_or_before_date(self, date_str: str) -> Optional[Tuple[float, str]]:
        """Get most recent price on or before target date from DB.

        Returns (price, actual_date) or None.
        """
        if self._db:
            db_ops = YahooStockDB(self._db)
            stock_id = db_ops.get_stock_id(self.symbol)
            if stock_id:
                result = db_ops.get_latest_net_value_before(stock_id, date_str)
                if result:
                    return result
        return None

    def has_data(self) -> bool:
        return self._price > 0

    # ============================================================
    # Net value operations (matching PHP _yahooStockGetData)
    # ============================================================

    def _yahoo_stock_get_data(
        self, yahoo_symbol: str, stock_id: int
    ) -> Optional[Tuple[float, str]]:
        """Fetch latest net value from Yahoo and store in database.

        PHP对应: _yahooStockGetData($strSymbol, $strStockId)
        使用 chart JSON API，获取1天数据，写入 netvaluehistory 表。
        返回最新写入的 (net_value, date)。

        Args:
            yahoo_symbol: Yahoo格式代码
            stock_id: 数据库中的 stock_id

        Returns:
            (net_value, date_str) 或 None
        """
        if not self._db:
            self._error = "No database session"
            return None

        ar_result = _get_yahoo_chart_data(yahoo_symbol, range_str='1d')
        if not ar_result:
            return None

        ar_timestamp = ar_result['timestamp']
        ar_adjclose = ar_result['indicators']['adjclose'][0]['adjclose']

        db_ops = YahooStockDB(self._db)

        # PHP: for ($i = 0; $i < count($arTimeStamp); $i++)
        for i in range(len(ar_timestamp)):
            dt = datetime.fromtimestamp(int(ar_timestamp[i]), tz=timezone.utc)
            str_date = dt.strftime('%Y-%m-%d')
            str_net_value = mysql_round(ar_adjclose[i])

            # PHP: if ($net_sql->WriteDaily($strStockId, $strDate, $strNetValue))
            if db_ops.write_net_value(stock_id, str_date, str_net_value):
                logger.info(f"Updated net value for {yahoo_symbol} {str_date} {str_net_value}")
                return (str_net_value, str_date)

        return None

    def get_net_value(self, stock_id: Optional[int] = None) -> Optional[Tuple[float, str]]:
        """Force get latest net value from Yahoo (no condition checking).

        PHP对应: YahooGetNetValue($ref)
        索引直接用原始symbol，其他用 BuildYahooNetValueSymbol 加 -IV 后缀。

        Args:
            stock_id: 数据库 stock_id，如果为None则自动查找

        Returns:
            (net_value, date_str) 或 None
        """
        if self.is_index:
            yahoo_sym = self.yahoo_symbol
        else:
            yahoo_sym = build_yahoo_net_value_symbol(self.yahoo_symbol, 'IV')

        if not yahoo_sym:
            return None

        if stock_id is None and self._db:
            db_ops = YahooStockDB(self._db)
            stock_id = db_ops.get_stock_id(self.symbol)

        if stock_id is None:
            self._error = f"Stock {self.symbol} not found in database"
            return None

        return self._yahoo_stock_get_data(yahoo_sym, stock_id)

    def update_net_value(self, stock_id: Optional[int] = None) -> Optional[Tuple[float, str]]:
        """Update net value (with condition checking, matching PHP YahooUpdateNetValue).

        PHP对应: YahooUpdateNetValue($ref)
        条件检查:
        1. 股票必须有数据 (HasData)
        2. 数据库中不能已有今天的数据
        3. 美股必须在收盘后 (16:55 ET) 才更新
        """
        if not self._db:
            self._error = "No database session"
            return None

        db_ops = YahooStockDB(self._db)

        if stock_id is None:
            stock_id = db_ops.get_stock_id(self.symbol)
        if stock_id is None:
            return None

        # PHP: _yahooGetNetValueSymbol — 判断是否需要获取净值
        yahoo_sym = self._get_net_value_symbol()
        if yahoo_sym is None:
            return None

        # PHP: if ($net_sql->GetRecord($strStockId, $strDate)) return; // already have today
        now_ymd = datetime.now(timezone.utc)
        str_date = now_ymd.strftime('%Y-%m-%d')
        existing = db_ops.get_net_value_by_date(stock_id, str_date)
        if existing is not None:
            logger.debug(f"{self.symbol}: Already have today's net value {existing}")
            return None

        # PHP: if ($iHourMinute < 1655) return; // Market not closed
        hour_minute = now_ymd.hour * 100 + now_ymd.minute
        if now_ymd.strftime('%Y-%m-%d') == str_date and hour_minute < 1655:
            logger.debug(f"{self.symbol}: US market not closed yet ({hour_minute})")
            return None

        return self._yahoo_stock_get_data(yahoo_sym, stock_id)

    def _get_net_value_symbol(self) -> Optional[str]:
        """Determine if we should fetch net value for this symbol.

        PHP对应: _yahooGetNetValueSymbol($sym, $strSymbol)
        某些类型不需要获取（期货、A股、H股、部分指数/ETF）。
        """
        sym = self._symbol

        # PHP: if ($sym->IsSinaFuture()) return false;
        if sym.is_future():
            return None
        # PHP: if ($sym->IsSymbolA() || $sym->IsSymbolH()) return false;
        if sym.is_symbol_a() or sym.is_symbol_h():
            return None
        # PHP: if ($sym->IsIndex() || $sym->IsSinaGlobalIndex()) return false;
        if sym.is_index():
            return None

        # PHP: switch — 某些ETF不需要
        skip_symbols = {'IBB', 'QQQ', 'USO'}
        if self.yahoo_symbol in skip_symbols:
            return None

        # PHP: return BuildYahooNetValueSymbol($strSymbol)
        return build_yahoo_net_value_symbol(self.yahoo_symbol, 'IV')

    # ============================================================
    # History chart operations (matching PHP UpdateYahooHistoryChart)
    # ============================================================

    def update_history_chart(self, stock_id: Optional[int] = None) -> bool:
        """Update full history chart data from Yahoo into database.

        PHP对应: UpdateYahooHistoryChart($ref)
        获取2年日线数据，写入 stockhistory 表。
        包含去重、零成交量过滤、空数据过滤等逻辑。

        Returns:
            True if any data was updated
        """
        if not self._db:
            self._error = "No database session"
            return False

        db_ops = YahooStockDB(self._db)

        if stock_id is None:
            stock_id = db_ops.get_stock_id(self.symbol)
        if stock_id is None:
            stock_id = db_ops.ensure_stock_id(self.symbol)
        if stock_id is None:
            return False

        # PHP: if ($strCurDate == $date_sql->ReadDate($strStockId)) return false;
        cur_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        saved_date = db_ops.get_history_date(stock_id)
        if saved_date == cur_date:
            logger.info(f"{self.symbol}: History chart already updated today")
            return False

        # PHP: $arResult = _getYahooChartData($strYahooSymbol, ..., '2y')
        ar_result = _get_yahoo_chart_data(self.yahoo_symbol, range_str='2y')
        if not ar_result:
            return False

        records = _parse_chart_result(ar_result)
        if not records:
            return False

        # PHP: 写入数据库循环
        total = 0
        modified = 0

        for rec in records:
            str_date = rec['date']
            str_close = rec['close']
            str_volume = rec['volume']
            str_adjclose = rec['adjclose']

            total += 1
            if db_ops.write_history(
                stock_id, str_date,
                close=str_close,
                volume=str_volume,
                adjclose=str_adjclose,
                open_price=rec['open'],
                high=rec['high'],
                low=rec['low']
            ):
                modified += 1

        # PHP: $his_sql->DeleteByZeroVolume($strStockId)
        db_ops.delete_by_zero_volume(stock_id)

        # PHP: $date_sql->WriteDate($strStockId, $strCurDate)
        db_ops.write_history_date(stock_id, cur_date)

        logger.info(f"{self.symbol}: History chart updated, total={total}, modified={modified}")
        return modified > 0

    # ============================================================
    # Query operations (database first)
    # ============================================================

    def get_net_value_from_db(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get net value from database.

        PHP对应: SqlGetNetValueByDate($strStockId, $strDate)
        """
        if not self._db:
            return None
        db_ops = YahooStockDB(self._db)
        return db_ops.get_net_value_by_date(stock_id, date_str)

    def get_close_from_db(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get close price from database.

        PHP对应: SqlGetHistoryByDate($strStockId, $strDate)
        """
        if not self._db:
            return None
        db_ops = YahooStockDB(self._db)
        return db_ops.get_history_by_date(stock_id, date_str)

    def get_adjclose_from_db(self, stock_id: int, date_str: str) -> Optional[float]:
        """Get adjclose from database.

        PHP对应: SqlGetAdjCloseByDate($strStockId, $strDate)
        """
        if not self._db:
            return None
        db_ops = YahooStockDB(self._db)
        return db_ops.get_adjclose_by_date(stock_id, date_str)

    def get_latest_price(self) -> float:
        """Get the latest adjclose price (from DB or Yahoo).

        PHP对应: 先查数据库，没有再从Yahoo获取
        """
        if self._db:
            try:
                db_ops = YahooStockDB(self._db)
                stock_id = db_ops.get_stock_id(self.symbol)
                if stock_id:
                    record = db_ops.get_net_value_record_now(stock_id)
                    if record:
                        self._price = record['close']
                        self._date = record['date']
                        return self._price
                    from app.models.market_data import StockHistory
                    latest = self._db.query(StockHistory).filter(
                        StockHistory.stock_id == stock_id
                    ).order_by(StockHistory.date.desc()).first()
                    if latest:
                        self._price = latest.close
                        self._date = latest.date.strftime('%Y-%m-%d')
                        return self._price
            except Exception:
                pass

        try:
            result = self.get_net_value()
            if result:
                self._price, self._date = result[0], result[1]
                return self._price
        except Exception:
            pass

        try:
            ar_result = _get_yahoo_chart_data(self.yahoo_symbol, range_str='5d')
            if ar_result:
                records = _parse_chart_result(ar_result)
                if records:
                    latest = records[-1]
                    self._price = latest['adjclose']
                    self._date = latest['date']
                    return self._price
        except Exception:
            pass

        price, date_str, prev_close, prev_date_str = self._fetch_sina_us_price()
        if price > 0:
            self._price = price
            self._date = date_str
            if prev_close > 0 and prev_date_str:
                self._prev_close = prev_close
                self._prev_date = prev_date_str
            return self._price

        return 0.0

    def _fetch_sina_us_price(self) -> tuple:
        """Fetch US stock price from Sina as fallback.

        Returns:
            (price, date_str, prev_close, prev_date_str) or (0, '', 0, '')
            新浪美股API: http://hq.sinajs.cn/list=gb_{symbol}
            字段对照(已验证):
              [0]=名称, [1]=当前价/收盘, [2]=涨跌额, [3]=日期时间,
              [4]=涨跌幅%, [5]=开盘价, [6]=最高, [7]=最低,
              [26]=昨收价(prev_close), [34]=最近收盘日期
        """
        from app.utils.http_client import HttpClient
        from datetime import timedelta

        us_symbol = self._symbol.symbol
        if us_symbol.startswith('^'):
            return 0.0, '', 0.0, ''

        url = f"http://hq.sinajs.cn/list=gb_{us_symbol.lower()}"
        http_client = HttpClient()

        try:
            response = http_client.get(
                url, timeout=10,
                headers={"Referer": "http://finance.sina.com.cn"},
            )
            if response and response.status_code == 200:
                content = response.text
                if '=' in content and '"' in content:
                    data_str = content.split('"')[1]
                    if data_str:
                        fields = data_str.split(',')
                        if len(fields) >= 27:
                            price = float(fields[1])
                            prev_close = float(fields[26])
                            date_str = fields[3] if len(fields) > 3 else ''
                            if date_str:
                                date_part = date_str.split()[0] if ' ' in date_str else date_str
                                parts = date_part.split('-')
                                if len(parts) == 3:
                                    date_str = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                                else:
                                    date_str = date_part
                            prev_date_str = ''
                            if date_str and prev_close > 0:
                                try:
                                    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
                                    prev_dt = dt - timedelta(days=1)
                                    prev_date_str = prev_dt.strftime('%Y-%m-%d')
                                except Exception:
                                    pass
                            return price, date_str, prev_close, prev_date_str
        except Exception as e:
            logger.debug(f"Sina US stock fetch failed for {us_symbol}: {e}")

        return 0.0, '', 0.0, ''

    def get_price_at_date(self, date_str: str) -> Optional[float]:
        """Get price at specific date (database first).

        PHP对应: 先 SqlGetNetValueByDate / SqlGetHistoryByDate，没有再从Yahoo获取
        """
        if self._db:
            db_ops = YahooStockDB(self._db)
            stock_id = db_ops.get_stock_id(self.symbol)
            if stock_id:
                # Try netvaluehistory
                val = db_ops.get_net_value_by_date(stock_id, date_str)
                if val is not None:
                    return val
                # Try stockhistory
                val = db_ops.get_adjclose_by_date(stock_id, date_str)
                if val is not None:
                    return val

        return None

    def get_ema(self, days: int = 50) -> Optional[float]:
        """Calculate EMA from database history.

        PHP对应: 从 stockhistory 表读取历史数据计算EMA
        """
        if not self._db:
            return None

        db_ops = YahooStockDB(self._db)
        stock_id = db_ops.get_stock_id(self.symbol)
        if not stock_id:
            return None

        from app.models.market_data import StockHistory
        records = self._db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id
        ).order_by(StockHistory.date.asc()).limit(days * 2).all()

        if len(records) < days:
            return None

        prices = [r.adjclose for r in records]
        k = 2.0 / (days + 1)

        ema = prices[0]
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)

        return ema

    def fetch_daily(self, days: int = 365) -> List[Dict[str, Any]]:
        """Fetch daily historical data (from database).

        PHP对应: 从 stockhistory 表查询
        """
        if not self._db:
            return []

        db_ops = YahooStockDB(self._db)
        stock_id = db_ops.get_stock_id(self.symbol)
        if not stock_id:
            return []

        from app.models.market_data import StockHistory
        cutoff = datetime.now() - timedelta(days=days)
        records = self._db.query(StockHistory).filter(
            StockHistory.stock_id == stock_id,
            StockHistory.date >= cutoff.date()
        ).order_by(StockHistory.date.asc()).all()

        return [{
            'date': r.date.strftime('%Y-%m-%d'),
            'open': r.open or 0.0,
            'high': r.high or 0.0,
            'low': r.low or 0.0,
            'close': r.close,
            'volume': r.volume,
            'adj_close': r.adjclose,
        } for r in records]


# ============================================================
# Batch utilities
# ============================================================

def fetch_batch_prices(symbols: List[str], db: Optional[Session] = None) -> Dict[str, float]:
    """Fetch latest prices for multiple symbols (from database)."""
    result = {}

    for symbol in symbols:
        try:
            yahoo = YahooStock(symbol, db=db)
            price = yahoo.get_latest_price()
            if price > 0:
                result[symbol] = price
        except Exception:
            pass

    return result


def get_dividend_yield(symbol: str) -> Optional[float]:
    """Get dividend yield (placeholder implementation)."""
    return None


def get_pe_ratio(symbol: str) -> Optional[float]:
    """Get P/E ratio (placeholder implementation)."""
    return None
