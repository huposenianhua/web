"""CNY exchange rate fetcher.

Translated from PHP stock/cnyref.php + stock/chinamoney.php.
Uses China Money (chinamoney.com.cn) official middle rates.
Data is stored in netvaluehistory table (matching PHP original).

PHP对应:
  - CnyReference       → CnyReference
  - UsdHkdReference    → UsdHkdReference
  - GetChinaMoney()    → get_china_money()
  - _chinaMoneyNeedData()  → _china_money_need_data()
  - _chinaMoneyInsertData() → _china_money_insert_data()

PHP数据流:
  1. CnyReference.LoadData() → 从 netvaluehistory 表读取最新汇率
  2. GetChinaMoney() → 每日9:15后从中国货币网获取官方中间价
  3. 写入 netvaluehistory 表（stock_id 对应 USCNY/EUCNY/JPCNY/HKCNY）
  4. 后续查询直接从数据库读取

汇率代码对照:
  USCNY = USD/CNY 中间价（1美元=?人民币）
  EUCNY = EUR/CNY 中间价
  JPCNY = 100JPY/CNY 中间价
  HKCNY = HKD/CNY 中间价
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

from sqlalchemy.orm import Session

from app.utils.logger import get_logger
from app.utils.file_cache import debug_json, get_chinamoney_cache_path, SECONDS_IN_MIN

logger = get_logger(__name__)

# PHP: GetChinaMoneyUrl().'r/cms/www/chinamoney/data/fx/ccpr.json'
CHINA_MONEY_JSON_URL = 'https://www.chinamoney.com.cn/r/cms/www/chinamoney/data/fx/ccpr.json'

# PHP: if ($ref->GetHourMinute() < 915) return;  // Data not updated until 9:15
CHINA_MONEY_UPDATE_HOUR_MINUTE = 915

# 汇率代码 → 中国货币网字段名映射
# PHP: switch ($strPair) { case 'USD/CNY': ... case 'EUR/CNY': ... }
CURRENCY_PAIR_MAP = {
    'USCNY': 'USD/CNY',
    'EUCNY': 'EUR/CNY',
    'JPCNY': '100JPY/CNY',
    'HKCNY': 'HKD/CNY',
}


# ============================================================
# Core: China Money data fetch (matching PHP chinamoney.php)
# ============================================================

def _china_money_need_data(db: Session, date_str: str) -> bool:
    """Check if we need to fetch China Money data for this date.

    PHP: _chinaMoneyNeedData($strDate)
      $net_sql = GetNetValueHistorySql();
      if ($net_sql->GetRecord(SqlGetStockId('USCNY'), $strDate)) return false;
      return $strDate;

    Returns:
        True  — 需要获取数据（数据库没有该日期的记录）
        False — 不需要（已有数据）
    """
    stock_id = _get_stock_id(db, 'USCNY')
    if stock_id is None:
        return True

    from app.models.market_data import NetValueHistory
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    record = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id,
        NetValueHistory.date == dt
    ).first()
    return record is None


def _china_money_insert_data(db: Session, money_symbol: str, date_str: str, price: float):
    """Insert exchange rate into netvaluehistory table.

    PHP: _chinaMoneyInsertData($strMoney, $strDate, $strPrice)
      $net_sql = GetNetValueHistorySql();
      $net_sql->InsertDaily(SqlGetStockId($strMoney), $strDate, $strPrice);
    """
    stock_id = _get_stock_id(db, money_symbol, create=True)
    if stock_id is None:
        return

    from app.models.market_data import NetValueHistory
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    stmt = mysql_insert(NetValueHistory).values(
        stock_id=stock_id,
        date=dt,
        close=price,
    )
    stmt = stmt.on_duplicate_key_update(close=stmt.inserted.close)
    db.execute(stmt)
    db.commit()
    logger.info(f"Inserted {money_symbol} {date_str} {price}")


def _get_stock_id(db: Session, symbol: str, create: bool = False) -> Optional[int]:
    """Get stock_id for exchange rate symbol.

    PHP: SqlGetStockId($strSymbol)
    """
    from app.models.stock import Stock
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        sym_bare = symbol.lstrip('SH').lstrip('SZ')
        if sym_bare != symbol:
            stock = db.query(Stock).filter(Stock.symbol == sym_bare).first()
    if not stock and create:
        stock = Stock(symbol=symbol, name=symbol)
        db.add(stock)
        db.commit()
        db.refresh(stock)
    return stock.id if stock else None


def get_china_money(db: Session, ref_date: Optional[str] = None) -> bool:
    """Fetch exchange rates from China Money and store in database.

    PHP: GetChinaMoney($ref)
      1. _chinaMoneyNeedData($ref->GetDate()) == false → return
      2. $ref->GetHourMinute() < 915 → return
      3. StockDebugJson(DebugGetChinaMoneyFile(), GetChinaMoneyJsonUrl())
      4. Parse JSON → insert into netvaluehistory

    Args:
        db: SQLAlchemy session
        ref_date: Reference date (YYYY-MM-DD), defaults to today (Asia/Shanghai)

    Returns:
        True if data was fetched and stored, False otherwise
    """
    # PHP: $ref->SetTimeZone() — use Asia/Shanghai timezone
    tz_sh = timezone(timedelta(hours=8))
    now_sh = datetime.now(tz_sh)

    if ref_date is None:
        ref_date = now_sh.strftime('%Y-%m-%d')

    # PHP: if (_chinaMoneyNeedData($ref->GetDate()) == false) return;
    if not _china_money_need_data(db, ref_date):
        logger.debug(f"China Money: already have data for {ref_date}")
        return False

    # PHP: if ($ref->GetHourMinute() < 915) return;
    hour_minute = now_sh.hour * 100 + now_sh.minute
    if hour_minute < CHINA_MONEY_UPDATE_HOUR_MINUTE:
        logger.debug(f"China Money: not yet 9:15 (current {hour_minute})")
        return False

    # PHP: StockDebugJson(DebugGetChinaMoneyFile(), GetChinaMoneyJsonUrl())
    cache_path = get_chinamoney_cache_path()
    http_client = __import__('app.utils.http_client', fromlist=['HttpClient']).HttpClient()

    def _fetch(url: str) -> Optional[str]:
        try:
            response = http_client.get(url, timeout=15)
            if response and response.status_code == 200:
                return response.text
        except Exception as e:
            logger.error(f"China Money request failed: {e}")
        return None

    ar = debug_json(cache_path, CHINA_MONEY_JSON_URL, _fetch, interval=SECONDS_IN_MIN)
    if ar is None:
        return False

    # PHP: $arData = $ar['data'];
    ar_data = ar.get('data', {})
    if not ar_data:
        logger.warning("China Money: no 'data' key")
        return False

    # PHP: $strDate = _chinaMoneyNeedData(substr($arData['lastDate'], 0, 10))
    # lastDate format: "2018-04-12 9:15"
    last_date = ar_data.get('lastDate', '')
    str_date = last_date[:10] if last_date else ref_date

    # Double check: DB might have been updated by another process
    if not _china_money_need_data(db, str_date):
        logger.debug(f"China Money: already have data for {str_date} (after fetch)")
        return False

    # PHP: if (isset($ar['records'])) { foreach ($ar['records'] as $arPair) { ... } }
    ar_records = ar.get('records', [])
    if not ar_records:
        logger.warning("China Money: no 'records' key")
        return False

    inserted = False
    for ar_pair in ar_records:
        str_pair = ar_pair.get('vrtEName', '')
        str_price = ar_pair.get('price', '')

        if not str_pair or not str_price:
            continue

        try:
            price = float(str_price)
        except (ValueError, TypeError):
            continue

        # PHP: switch ($strPair) { case 'USD/CNY': ... }
        for money_symbol, pair_name in CURRENCY_PAIR_MAP.items():
            if str_pair == pair_name:
                _china_money_insert_data(db, money_symbol, str_date, price)
                inserted = True
                break

    return inserted


# ============================================================
# CnyReference (matching PHP stock/cnyref.php)
# ============================================================

class CnyReference:
    """CNY exchange rate reference.

    PHP: class CnyReference extends MysqlReference

    PHP行为:
      1. LoadData() → 从 netvaluehistory 表读取最新汇率（USCNY/HKCNY等）
      2. SetTime('09:15:00') → 设置数据更新时间
      3. GetClose($strDate) → 查指定日期汇率
      4. GetVal($strDate) → 获取汇率值

    数据存储在 netvaluehistory 表中:
      - stock_id 对应 stock 表中的 USCNY, HKCNY 等
      - close 字段存储汇率值
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        """
        Args:
            symbol: 汇率代码，如 'USCNY', 'HKCNY', 'EUCNY', 'JPCNY'
            db: SQLAlchemy session
        """
        self._symbol = symbol
        self._db = db
        self._sql_id: Optional[int] = None
        self._price: float = 0.0
        self._date: str = ''
        self._prev_price: float = 0.0

        if db:
            self._load_data()

    def _load_data(self):
        """Load latest exchange rate from database.

        PHP: CnyReference::LoadData()
          $this->strSqlId = SqlGetStockId($strSymbol);
          $this->LoadSqlNetValueData();  → LoadDailySqlData(GetNetValueHistorySql())
          $this->SetTime('09:15:00');
        """
        self._sql_id = _get_stock_id(self._db, self._symbol)
        if self._sql_id is None:
            return

        # PHP: LoadDailySqlData → GetRecordNow → set price/date/prevPrice
        from app.models.market_data import NetValueHistory
        record = self._db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == self._sql_id
        ).order_by(NetValueHistory.date.desc()).first()

        if record:
            self._price = record.close
            self._date = record.date.strftime('%Y-%m-%d')

            # PHP: $this->strPrevPrice = $sql->GetClosePrev($this->strSqlId, $this->strDate)
            prev = self._db.query(NetValueHistory).filter(
                NetValueHistory.stock_id == self._sql_id,
                NetValueHistory.date < record.date
            ).order_by(NetValueHistory.date.desc()).first()
            self._prev_price = prev.close if prev else 0.0

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def sql_id(self) -> Optional[int]:
        return self._sql_id

    @property
    def price(self) -> float:
        return self._price

    @property
    def date(self) -> str:
        return self._date

    @property
    def prev_price(self) -> float:
        return self._prev_price

    def get_close(self, date_str: str) -> Optional[float]:
        """Get exchange rate for a specific date.

        PHP: CnyReference::GetClose($strDate)
          if ($strDate == $this->GetDate()) return $this->GetPrice();
          return SqlGetNetValueByDate($this->strSqlId, $strDate);
        """
        if date_str == self._date:
            return self._price

        if self._db and self._sql_id:
            from app.models.market_data import NetValueHistory
            dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            record = self._db.query(NetValueHistory).filter(
                NetValueHistory.stock_id == self._sql_id,
                NetValueHistory.date == dt
            ).first()
            return record.close if record else None

        return None

    def get_val(self, date_str: Optional[str] = None) -> Optional[float]:
        """Get exchange rate value.

        PHP: MysqlReference::GetVal($strDate)
          if ($strDate) { if ($strClose = $this->GetClose($strDate)) return floatval($strClose); }
          return floatval($this->GetPrice());
        """
        if date_str:
            close = self.get_close(date_str)
            if close is not None:
                return float(close)
            return None
        return float(self._price) if self._price else None

    def has_data(self) -> bool:
        """Whether this reference has valid data."""
        return self._price > 0


# ============================================================
# UsdHkdReference (matching PHP stock/cnyref.php)
# ============================================================

class UsdHkdReference:
    """USD/HKD cross rate via USD/CNY and HKD/CNY.

    PHP: class UsdHkdReference
      $this->uscny_ref = new CnyReference('USCNY');
      $this->hkcny_ref = new CnyReference('HKCNY');
      GetVal() = uscny / hkcny
    """

    def __init__(self, db: Optional[Session] = None):
        self._uscny_ref = CnyReference('USCNY', db)
        self._hkcny_ref = CnyReference('HKCNY', db)

    def get_val(self, date_str: Optional[str] = None) -> Optional[float]:
        """Get USD/HKD rate.

        PHP: return $this->uscny_ref->GetVal($strDate) / $this->hkcny_ref->GetVal($strDate);
        """
        uscny = self._uscny_ref.get_val(date_str)
        hkcny = self._hkcny_ref.get_val(date_str)
        if uscny and hkcny and hkcny > 0:
            return uscny / hkcny
        return None

    def get_close(self, date_str: str) -> Optional[float]:
        """Get USD/HKD close for a specific date.

        PHP: return $this->uscny_ref->GetClose($strDate) / $this->hkcny_ref->GetClose($strDate);
        """
        uscny = self._uscny_ref.get_close(date_str)
        hkcny = self._hkcny_ref.get_close(date_str)
        if uscny and hkcny and hkcny > 0:
            return uscny / hkcny
        return None


# ============================================================
# Convenience functions (compatible with old interface)
# ============================================================

def get_cny_usd(db: Optional[Session] = None) -> float:
    """Get USD/CNY rate (1 USD = ? CNY).

    Uses CnyReference('USCNY') from database.
    """
    ref = CnyReference('USCNY', db)
    return ref.get_val() or 0.0


def get_hkd_cny(db: Optional[Session] = None) -> float:
    """Get HKD/CNY rate (1 HKD = ? CNY).

    Uses CnyReference('HKCNY') from database.
    """
    ref = CnyReference('HKCNY', db)
    return ref.get_val() or 0.0


def get_usd_hkd(db: Optional[Session] = None) -> float:
    """Get USD/HKD cross rate.

    Uses UsdHkdReference.
    """
    ref = UsdHkdReference(db)
    return ref.get_val() or 0.0


def convert_usd_to_cny(amount_usd: float, db: Optional[Session] = None) -> float:
    """Convert USD to CNY."""
    rate = get_cny_usd(db)
    return amount_usd * rate


def convert_cny_to_usd(amount_cny: float, db: Optional[Session] = None) -> float:
    """Convert CNY to USD."""
    rate = get_cny_usd(db)
    if rate > 0:
        return amount_cny / rate
    return 0.0


def convert_hkd_to_cny(amount_hkd: float, db: Optional[Session] = None) -> float:
    """Convert HKD to CNY."""
    rate = get_hkd_cny(db)
    return amount_hkd * rate


def convert_cny_to_hkd(amount_cny: float, db: Optional[Session] = None) -> float:
    """Convert CNY to HKD."""
    rate = get_hkd_cny(db)
    if rate > 0:
        return amount_cny / rate
    return 0.0


def convert_to_cny(amount: float, from_currency: str, db: Optional[Session] = None) -> float:
    """Convert amount to CNY."""
    from_currency = from_currency.upper()
    if from_currency == 'USD':
        return convert_usd_to_cny(amount, db)
    elif from_currency == 'HKD':
        return convert_hkd_to_cny(amount, db)
    return amount


def get_rates(db: Optional[Session] = None) -> Dict[str, float]:
    """Get all exchange rates."""
    return {
        'usd_cny': get_cny_usd(db),
        'hkd_cny': get_hkd_cny(db),
        'usd_hkd': get_usd_hkd(db),
    }
