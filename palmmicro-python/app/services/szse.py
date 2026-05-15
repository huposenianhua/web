"""Shenzhen Stock Exchange (SZSE) data fetcher.

Translated from PHP stock/szse.php.
Fetches LOF shares data from SZSE official API.

PHP对应:
  - SzseGetLofShares() → szse_get_lof_shares()
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.services.stocksymbol import StockSymbol
from app.utils.http_client import HttpClient
from app.utils.file_cache import _get_cache_file_path, read_cached_file
from app.utils.logger import get_logger

logger = get_logger(__name__)

# PHP: SZSE API endpoint
SZSE_BASE_URL = 'http://www.szse.cn'
SZSE_LOF_API = '/api/report/ShowReport/data'

# PHP: Cache file name pattern
SZSE_CACHE_PREFIX = 'szse'

# PHP: Data not updated until 9:15
SZSE_DATA_UPDATE_HOUR_MINUTE = 915

# PHP: Cache TTL (20 minutes)
SZSE_CACHE_TTL_MINUTES = 20


def _get_szse_lof_url(digit_a: str) -> str:
    """Build SZSE LOF API URL.

    PHP: GetSzseUrl().'api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1945_LOF&txtQueryKeyAndJC='.$ref->GetDigitA()
    """
    params = {
        'SHOWTYPE': 'JSON',
        'CATALOGID': '1945_LOF',
        'txtQueryKeyAndJC': digit_a,
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return f"{SZSE_BASE_URL}{SZSE_LOF_API}?{query}"


def _parse_szse_lof_response(ar: dict, expected_date: str) -> Optional[int]:
    """Parse SZSE LOF response and extract shares.

    PHP:
        $ar0 = $ar[0];
        if (isset($ar0['metadata'])) {
            $arMetaData = $ar0['metadata'];
            if ($arMetaData['subname'] == $strDate) {
                if (isset($ar0['data'])) {
                    $arData = $ar0['data'];
                    $arData0 = $arData[0];
                    $strClose = str_replace(',', '', $arData0['dqgm']);
                    return intval($strClose);
                }
            }
        }
    """
    if not ar or not isinstance(ar, list) or len(ar) == 0:
        return None

    ar0 = ar[0]
    if not isinstance(ar0, dict):
        return None

    # Check metadata date
    metadata = ar0.get('metadata')
    if not metadata:
        logger.debug('szse_get_lof_shares: no metadata')
        return None

    subname = metadata.get('subname')
    if subname != expected_date:
        logger.debug(f'szse_get_lof_shares: different date: {subname} vs {expected_date}')
        return None

    # Extract shares data
    data = ar0.get('data')
    if not data or not isinstance(data, list) or len(data) == 0:
        logger.debug('szse_get_lof_shares: no data')
        return None

    ar_data0 = data[0]
    if not isinstance(ar_data0, dict):
        return None

    # dqgm = 当期规模 (current scale/shares)
    dqgm = ar_data0.get('dqgm')
    if not dqgm:
        return None

    # Remove commas and convert to int
    shares_str = str(dqgm).replace(',', '')
    try:
        return int(shares_str)
    except (ValueError, TypeError):
        return None


def szse_get_lof_shares(symbol: str, db: Session) -> bool:
    """Get LOF shares from SZSE and write to database.

    PHP: function SzseGetLofShares($ref)
      1. if ($ref->IsShenZhenLof() == false) return;
      2. if ($sql->GetRecord($strStockId, $strDate)) return;  // already have today's data
      3. if ($ref->GetHourMinute() < 915) return;  // data not updated until 9:15
      4. Fetch from SZSE API
      5. $sql->WriteDaily($strStockId, $strDate, $strClose);

    Args:
        symbol: Stock symbol, e.g., 'SZ162411'
        db: SQLAlchemy session

    Returns:
        True if data was written, False otherwise
    """
    from app.models.market_data import SharesHistory

    sym = StockSymbol(str(symbol))

    # PHP: if ($ref->IsShenZhenLof() == false) return;
    if not sym.is_shenzhen_lof():
        logger.debug(f'szse_get_lof_shares: {symbol} is not Shenzhen LOF')
        return False

    # Get stock_id
    from app.models.stock import Stock
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        logger.debug(f'szse_get_lof_shares: stock not found: {symbol}')
        return False

    stock_id = stock.id

    # PHP: $strDate = $ref->GetDate();
    tz_sh = timezone(timedelta(hours=8))
    now_sh = datetime.now(tz_sh)
    date_str = now_sh.strftime('%Y-%m-%d')

    # PHP: if ($sql->GetRecord($strStockId, $strDate)) return;
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    existing = db.query(SharesHistory).filter(
        SharesHistory.stock_id == stock_id,
        SharesHistory.date == dt
    ).first()
    if existing:
        logger.debug(f'szse_get_lof_shares: already have {symbol} {date_str}')
        return False

    # PHP: if ($ref->GetHourMinute() < 915) return;
    hour_minute = now_sh.hour * 100 + now_sh.minute
    if hour_minute < SZSE_DATA_UPDATE_HOUR_MINUTE:
        logger.debug(f'szse_get_lof_shares: data not updated yet {hour_minute}')
        return False

    # PHP: GetSzseUrl().'api/report/ShowReport/data?...'
    digit_a = sym.get_digit_a()
    if not digit_a:
        logger.debug(f'szse_get_lof_shares: no digit A for {symbol}')
        return False

    url = _get_szse_lof_url(digit_a)

    # PHP: DebugGetSymbolFile('szse', $ref->GetSymbol())
    cache_path = _get_cache_file_path(SZSE_CACHE_PREFIX, symbol)

    # Fetch data
    http = HttpClient()
    try:
        response = http.get(url, cache_path=cache_path, cache_ttl_minutes=SZSE_CACHE_TTL_MINUTES)
        if not response:
            return False

        ar = response.json() if hasattr(response, 'json') else None
        if not ar:
            return False

    except Exception as e:
        logger.warning(f'szse_get_lof_shares: fetch failed: {e}')
        return False

    # Parse response
    shares = _parse_szse_lof_response(ar, date_str)
    if shares is None:
        return False

    # PHP: $sql->WriteDaily($strStockId, $strDate, $strClose);
    from sqlalchemy.dialects.mysql import insert as mysql_insert
    stmt = mysql_insert(SharesHistory).values(
        stock_id=stock_id,
        date=dt,
        close=shares,
    )
    stmt = stmt.on_duplicate_key_update(close=stmt.inserted.close)
    db.execute(stmt)
    db.commit()

    logger.info(f'szse_get_lof_shares: wrote {symbol} {date_str} shares={shares}')
    return True
