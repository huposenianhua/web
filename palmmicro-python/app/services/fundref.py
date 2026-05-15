"""Fund reference fetcher.

Translated from PHP stock/fundref.php.
Fetches fund net value data from Sina Finance and stores in database.

PHP对应:
  - FundReference       → FundReference
  - FundAdjustPosition  → fund_adjust_position
  - FundReverseAdjustPosition → fund_reverse_adjust_position
  - StockCompareEstResult → stock_compare_est_result
  - StockUpdateEstResult  → stock_update_est_result

PHP数据流:
  1. FundReference.LoadData() → LoadSinaFundData() 从Sina获取净值
  2. NetValueReference.__construct() → StockCompareEstResult() 写入netvaluehistory表
  3. 后续查询从netvaluehistory表读取历史净值

净值存储:
  - netvaluehistory 表: 存储每日官方净值 (close字段)
  - fundest 表: 存储估算净值 (用于误差对比)
  - calibration 表: 存储校准因子
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.services.stocksymbol import StockSymbol
from app.services.mystockref import MyStockReference
from app.services.stockref import StockRef
from app.utils.logger import get_logger, MIN_FLOAT_VAL
from app.utils.file_cache import get_sina_cache_path, read_cached_file

logger = get_logger(__name__)


# ============================================================
# Position adjustment functions (matching PHP fundref.php)
# ============================================================

def fund_adjust_position(f_ratio: float, f_val: float, f_old_val: float) -> float:
    """Adjust value by position ratio.

    PHP: FundAdjustPosition($fRatio, $fVal, $fOldVal)
    Formula: x = r * (x0 * y / y0) + (1 - r) * x0 = r * y + (1 - r) * x0

    Used to adjust estimated net value by fund position.
    """
    return f_ratio * f_val + (1.0 - f_ratio) * f_old_val


def fund_reverse_adjust_position(f_ratio: float, f_val: float, f_old_val: float) -> float:
    """Reverse adjust value by position ratio.

    PHP: FundReverseAdjustPosition($fRatio, $fVal, $fOldVal)
    Formula: y = (y0 * x / x0) / r - y0 * (1 / r - 1)
    """
    if abs(f_ratio) < MIN_FLOAT_VAL:
        return 0.0
    return f_val / f_ratio - f_old_val * (1.0 / f_ratio - 1.0)


# ============================================================
# Database operations for fund net value
# ============================================================

def _get_stock_id(db: Session, symbol: str, create: bool = False) -> Optional[int]:
    """Get stock_id for symbol.

    PHP: SqlGetStockId($strSymbol)
    Tries both prefixed (SZ162411) and bare (162411) formats.
    """
    from app.models.stock import Stock
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        sym = StockSymbol(symbol)
        if sym.is_symbol_a():
            stock = db.query(Stock).filter(Stock.symbol == sym.get_digit_a()).first()
        if not stock:
            bare = symbol.lstrip('SH').lstrip('SZ')
            if bare != symbol:
                stock = db.query(Stock).filter(Stock.symbol == bare).first()
    if not stock and create:
        stock = Stock(symbol=symbol, name=symbol)
        db.add(stock)
        db.commit()
        db.refresh(stock)
    return stock.id if stock else None


def _insert_net_value(db: Session, stock_id: int, date_str: str, net_value: float) -> bool:
    """Insert net value into netvaluehistory table.

    PHP: $net_sql->InsertDaily($strStockId, $strDate, $strNetValue)
    Returns True if a new record was inserted.
    """
    from app.models.market_data import NetValueHistory

    dt = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Check if already exists
    existing = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id,
        NetValueHistory.date == dt
    ).first()
    if existing:
        return False

    # Insert new record
    stmt = mysql_insert(NetValueHistory).values(
        stock_id=stock_id,
        date=dt,
        close=net_value,
    )
    stmt = stmt.on_duplicate_key_update(close=stmt.inserted.close)
    db.execute(stmt)
    db.commit()
    return True


def _get_net_value_by_date(db: Session, stock_id: int, date_str: str) -> Optional[float]:
    """Get net value from database by date.

    PHP: SqlGetNetValueByDate($strStockId, $strDate)
    """
    from app.models.market_data import NetValueHistory
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    record = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id,
        NetValueHistory.date == dt
    ).first()
    return record.close if record else None


def _get_net_value_now(db: Session, stock_id: int) -> Optional[Dict[str, Any]]:
    """Get latest net value record.

    PHP: $net_sql->GetRecordNow($strStockId)
    """
    from app.models.market_data import NetValueHistory
    record = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id
    ).order_by(NetValueHistory.date.desc()).first()
    if record:
        return {'date': record.date.strftime('%Y-%m-%d'), 'close': record.close}
    return None


def _get_net_value_prev(db: Session, stock_id: int, date_str: str) -> Optional[float]:
    """Get previous day's net value.

    PHP: $sql->GetClosePrev($strStockId, $strDate)
    """
    from app.models.market_data import NetValueHistory
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    record = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id,
        NetValueHistory.date < dt
    ).order_by(NetValueHistory.date.desc()).first()
    return record.close if record else None


def _get_calibration_close_now(db: Session, stock_id: int) -> Optional[float]:
    """Get latest calibration value.

    PHP: $cal_sql->GetCloseNow($strStockId)
    """
    from app.models.market_data import CalibrationHistory
    record = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock_id
    ).order_by(CalibrationHistory.date.desc()).first()
    return record.close if record else None


def _get_calibration_date_now(db: Session, stock_id: int) -> Optional[str]:
    """Get latest calibration date.

    PHP: $cal_sql->GetDateNow($strStockId)
    """
    from app.models.market_data import CalibrationHistory
    record = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock_id
    ).order_by(CalibrationHistory.date.desc()).first()
    return record.date.strftime('%Y-%m-%d') if record else None


def _write_calibration(db: Session, stock_id: int, date_str: str, value: float):
    """Write calibration value using weighted average strategy.

    PHP对应: CalibrationSql::WriteDailyAverage()
    
    作者的加权平均策略:
      - 同一天多次校准 → 取平均值（而非覆盖）
      - 例如: 第1次算出1286.85, 第2次算出1286.86 → 存储 (1286.85+1286.86)/2 = 1286.855, num=2
      - 这样如果盘中数据波动，最终记录的是当日所有校准的均值，更稳定
    
    对比旧策略(直接覆盖):
      - 第1次: 1286.85 → 存1286.85
      - 第2次: 1286.86 → 覆盖为1286.86 (第1次的值丢失了)
    """
    from app.models.market_data import CalibrationHistory
    from datetime import datetime as dt_class

    dt = dt_class.strptime(date_str, '%Y-%m-%d').date()
    now_str = dt_class.now().strftime('%H:%M')

    existing = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock_id,
        CalibrationHistory.date == dt
    ).first()

    if existing:
        old_avg = existing.close or 0.0
        old_num = existing.num or 1
        if abs(old_avg - value) > MIN_FLOAT_VAL:
            new_total = old_num * old_avg + value
            new_num = old_num + 1
            new_avg = new_total / new_num
            existing.close = new_avg
            existing.time = now_str
            existing.num = new_num
        else:
            return
    else:
        cal = CalibrationHistory(
            stock_id=stock_id,
            date=dt,
            close=value,
            time=now_str,
            num=1,
        )
        db.add(cal)

    db.commit()


def _get_fund_est(db: Session, stock_id: int, date_str: str) -> Optional[float]:
    """Get estimated net value.

    PHP: $fund_est_sql->GetClose($strStockId, $strDate)
    """
    from app.models.market_data import FundEst
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    record = db.query(FundEst).filter(
        FundEst.stock_id == stock_id,
        FundEst.date == dt
    ).first()
    return record.close if record else None


def _write_fund_est(db: Session, stock_id: int, date_str: str, value: float):
    """Write estimated net value.

    PHP: $fund_est_sql->WriteDaily($strStockId, $strDate, $strNetValue)
    """
    from app.models.market_data import FundEst
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    stmt = mysql_insert(FundEst).values(
        stock_id=stock_id,
        date=dt,
        close=value,
    )
    stmt = stmt.on_duplicate_key_update(close=stmt.inserted.close)
    db.execute(stmt)
    db.commit()


# ============================================================
# Core: StockCompareEstResult (matching PHP stock.php)
# ============================================================

def stock_compare_est_result(
    db: Session,
    stock_id: int,
    net_value: float,
    date_str: str,
    symbol: str
) -> bool:
    """Compare and store fund net value, check estimation error.

    PHP: StockCompareEstResult($strStockId, $strNetValue, $strDate, $strSymbol)

    1. Insert net value into netvaluehistory
    2. Compare with estimated value if exists
    3. Trigger error if estimation error > 1%

    Returns:
        True if new net value was inserted
    """
    # PHP: $net_sql->InsertDaily($strStockId, $strDate, $strNetValue)
    if not _insert_net_value(db, stock_id, date_str, net_value):
        return False

    # PHP: $fund_est_sql->GetClose($strStockId, $strDate)
    str_est_value = _get_fund_est(db, stock_id, date_str)
    if str_est_value:
        # PHP: $fPercentage = StockGetPercentage(floatval($strNetValue), floatval($strEstValue))
        if abs(net_value) > MIN_FLOAT_VAL:
            f_percentage = (str_est_value / net_value - 1.0) * 100.0
            # PHP: if (abs($fPercentage) > 1.0) trigger_error(...)
            if abs(f_percentage) > 1.0:
                logger.warning(f"Net value estimation error: {symbol} actual={net_value} est={str_est_value} error={f_percentage:.2f}%")

    return True


def stock_update_est_result(
    db: Session,
    stock_id: int,
    net_value: float,
    date_str: str
):
    """Update estimated net value result.

    PHP: StockUpdateEstResult($strStockId, $fNetValue, $strDate)

    Only update when net value is not ready (not in netvaluehistory).
    """
    # PHP: if ($net_sql->GetRecord($strStockId, $strDate) == false)
    existing = _get_net_value_by_date(db, stock_id, date_str)
    if existing is None:
        # PHP: $fund_est_sql->WriteDaily($strStockId, $strDate, strval($fNetValue))
        _write_fund_est(db, stock_id, date_str, net_value)


def daily_calibration(
    stock_id: int,
    pair_stock_id: int,
    cny_ref: Optional['CnyReference'],
    db: Session
) -> bool:
    """Daily calibration for fund pair reference.

    PHP: FundPairReference::DailyCalibration()
      $strStockId = $this->GetStockId();
      $net_sql = GetNetValueHistorySql();
      $cal_sql = GetCalibrationSql();
      $strDate = $net_sql->GetDateNow($strStockId);
      if ($strDate == $cal_sql->GetDateNow($strStockId)) return;  // already calibrated

      if ($strNetValue = $net_sql->GetCloseNow($strStockId))
      {
          if ($fPairNetValue = $this->pair_ref->GetNetValue($strDate))
          {
              $fFactor = $this->CalcFactor($fPairNetValue, floatval($strNetValue), $strDate);
              $cal_sql->WriteDaily($strStockId, $strDate, strval($fFactor));
              $this->LoadCalibration();
          }
      }

    Args:
        stock_id: Fund stock ID (e.g., TQQQ)
        pair_stock_id: Pair fund stock ID (e.g., QQQ)
        cny_ref: CNY reference for forex adjustment (optional)
        db: SQLAlchemy session

    Returns:
        True if calibration was performed
    """
    from app.models.market_data import NetValueHistory, CalibrationHistory

    # Get latest netvaluehistory date for this stock
    latest_net = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock_id
    ).order_by(NetValueHistory.date.desc()).first()

    if not latest_net:
        logger.debug(f'daily_calibration: no net value for stock_id={stock_id}')
        return False

    net_date = latest_net.date
    net_value = latest_net.close

    # Get latest calibration date for this stock
    latest_cal = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock_id
    ).order_by(CalibrationHistory.date.desc()).first()

    # PHP: if ($strDate == $cal_sql->GetDateNow($strStockId)) return;
    if latest_cal and latest_cal.date == net_date:
        logger.debug(f'daily_calibration: already calibrated for {stock_id} {net_date}')
        return False

    # Get pair net value for the same date
    pair_net = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == pair_stock_id,
        NetValueHistory.date == net_date
    ).first()

    if not pair_net:
        logger.debug(f'daily_calibration: no pair net value for {pair_stock_id} {net_date}')
        return False

    pair_net_value = pair_net.close

    # PHP: CalcFactor($fPairNetValue, $fNetValue, $strDate)
    # Factor = pair_net_value / net_value (with forex adjustment)
    adjusted_net_value = net_value
    if cny_ref:
        cny_val = cny_ref.get_close(str(net_date))
        if cny_val:
            # PHP: if ($this->IsSymbolA()) $fNetValue /= $fCny; else $fNetValue *= $fCny;
            # For US ETFs, we multiply by CNY (convert USD to CNY)
            adjusted_net_value = net_value * cny_val

    if abs(adjusted_net_value) < MIN_FLOAT_VAL:
        return False

    factor = pair_net_value / adjusted_net_value

    # PHP: $cal_sql->WriteDaily($strStockId, $strDate, strval($fFactor));
    from sqlalchemy.dialects.mysql import insert as mysql_insert
    stmt = mysql_insert(CalibrationHistory).values(
        stock_id=stock_id,
        date=net_date,
        close=factor,
    )
    stmt = stmt.on_duplicate_key_update(close=stmt.inserted.close)
    db.execute(stmt)
    db.commit()

    logger.info(f'daily_calibration: stock_id={stock_id} date={net_date} factor={factor:.6f}')
    return True


# ============================================================
# FundReference (matching PHP stock/fundref.php)
# ============================================================

class FundReference:
    """Fund reference with net value data.

    PHP: class FundReference extends MysqlReference

    PHP行为:
      1. __construct() → 创建MyStockReference, 加载calibration数据
      2. LoadData() → LoadSinaFundData() 从Sina获取实时净值
      3. GetOfficialNetValue() / GetFairNetValue() / GetRealtimeNetValue() 获取各类净值
      4. UpdateOfficialNetValue() → StockCompareEstResult() 写入数据库
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        """
        Args:
            symbol: Fund symbol, e.g., 'SZ162411'
            db: SQLAlchemy session
        """
        self._symbol = symbol
        self._db = db
        self._sym = StockSymbol(symbol)

        # PHP: $this->stock_ref = new MyStockReference($strSymbol)
        self._stock_ref: Optional[MyStockReference] = None
        if self._sym.is_fund_a():
            self._stock_ref = MyStockReference(symbol)

        # PHP: $this->strSqlId = $this->GetStockId()
        self._sql_id: Optional[int] = None
        if db:
            self._sql_id = _get_stock_id(db, symbol, create=True)

        # PHP: $this->fFactor = floatval($cal_sql->GetCloseNow($strStockId))
        self._factor: float = 1.0
        if db and self._sql_id:
            cal_close = _get_calibration_close_now(db, self._sql_id)
            if cal_close:
                self._factor = cal_close

        # Estimated net values
        self._official_net_value: Optional[float] = None
        self._fair_net_value: Optional[float] = None
        self._realtime_net_value: Optional[float] = None
        self._official_date: Optional[str] = None

        # Fund net value from f_ API (actual NAV, not trading price)
        self._fund_nav_price: Optional[float] = None
        self._fund_nav_prev: Optional[float] = None
        self._fund_nav_date: Optional[str] = None

        # CNY reference for forex
        self._cny_ref = None

    def load_data(self):
        """Load fund data from Sina.

        PHP: FundReference::LoadData() → LoadSinaFundData()
          Uses f_ prefix API for actual net value (not sz/sh trading price).
          Format: name, current_nav, accumulated_nav, prev_nav, date, ...
        """
        if self._stock_ref:
            self._stock_ref.fetch()

        fund_symbol = self._sym.get_sina_fund_symbol()
        if not fund_symbol:
            return

        try:
            from app.utils.http_client import HttpClient
            http_client = HttpClient()
            url = f"http://hq.sinajs.cn/list={fund_symbol}"
            response = http_client.get(
                url, timeout=10,
                headers={"Referer": "http://finance.sina.com.cn"},
            )
            if response and response.status_code == 200:
                import re
                match = re.search(r'var hq_str_[^=]+="([^"]+)"', response.text)
                if match:
                    fields = match.group(1).split(',')
                    if len(fields) >= 5:
                        nav = float(fields[1]) if fields[1] else 0.0
                        prev_nav = float(fields[3]) if len(fields) > 3 and fields[3] else 0.0
                        nav_date = fields[4] if len(fields) > 4 else ''
                        if nav > 0 and nav_date:
                            self._fund_nav_price = nav
                            self._fund_nav_prev = prev_nav
                            self._fund_nav_date = nav_date
        except Exception as e:
            logger.debug(f"Fund NAV fetch failed for {fund_symbol}: {e}")

    @property
    def symbol(self) -> str:
        if self._stock_ref:
            return self._stock_ref.symbol
        return self._symbol

    @property
    def sql_id(self) -> Optional[int]:
        if self._stock_ref:
            # Get from stock_ref if available
            pass
        return self._sql_id

    @property
    def price(self) -> float:
        """Current net value price (NAV from f_ API takes priority)."""
        if self._fund_nav_price is not None:
            return self._fund_nav_price
        if self._stock_ref:
            return self._stock_ref.price
        return 0.0

    @property
    def prev_price(self) -> float:
        """Previous net value (NAV from f_ API takes priority)."""
        if self._fund_nav_prev is not None:
            return self._fund_nav_prev
        if self._stock_ref:
            return self._stock_ref.prev_price
        return 0.0

    @property
    def date(self) -> str:
        """Current date (NAV date from f_ API takes priority)."""
        if self._fund_nav_date:
            return self._fund_nav_date
        if self._stock_ref:
            return self._stock_ref.date
        return datetime.now().strftime('%Y-%m-%d')

    @property
    def factor(self) -> float:
        """Calibration factor."""
        return self._factor

    def get_official_net_value(self) -> Optional[float]:
        """Get official net value."""
        return self._official_net_value

    def get_fair_net_value(self) -> Optional[float]:
        """Get fair net value."""
        return self._fair_net_value

    def get_realtime_net_value(self) -> Optional[float]:
        """Get realtime estimated net value."""
        return self._realtime_net_value

    def get_official_date(self) -> Optional[str]:
        """Get official net value date."""
        return self._official_date

    def set_forex(self, cny_symbol: str):
        """Set forex reference.

        PHP: FundReference::SetForex($strCny)
        """
        from app.services.cnyref import CnyReference
        if self._db:
            self._cny_ref = CnyReference(cny_symbol, self._db)

    def get_cny_ref(self):
        """Get CNY reference."""
        return self._cny_ref

    def update_est_net_value(self):
        """Update estimated net value in database.

        PHP: FundReference::UpdateEstNetValue() → StockUpdateEstResult()
        """
        if self._db and self._sql_id:
            official = self.get_official_net_value()
            official_date = self.get_official_date()
            if official and official_date:
                stock_update_est_result(self._db, self._sql_id, official, official_date)

    def update_official_net_value(self) -> bool:
        """Update official net value in database.

        PHP: FundReference::UpdateOfficialNetValue() → StockCompareEstResult()

        Returns:
            True if new net value was inserted
        """
        if self._db and self._sql_id:
            price = self.price
            date_str = self.date
            if price > 0 and date_str:
                return stock_compare_est_result(self._db, self._sql_id, price, date_str, self.symbol)
        return False

    def insert_fund_calibration(self):
        """Insert fund calibration value.

        PHP: FundReference::InsertFundCalibration()
        """
        if self._db and self._sql_id:
            _write_calibration(self._db, self._sql_id, self.date, self._factor)

    def _get_calibration_base_val(self) -> float:
        """Get calibration base value.

        PHP: FundReference::_getCalibrationBaseVal()
        """
        if self._db and self._sql_id:
            cal_date = _get_calibration_date_now(self._db, self._sql_id)
            if cal_date:
                val = _get_net_value_by_date(self._db, self._sql_id, cal_date)
                return val or 0.0
        return 0.0

    def adjust_position(self, f_val: float) -> float:
        """Adjust value by position ratio.

        PHP: FundReference::AdjustPosition($fVal)
        """
        # Get position from database
        position = self._get_position()
        base_val = self._get_calibration_base_val()
        return fund_adjust_position(position, f_val, base_val)

    def reverse_adjust_position(self, f_val: float) -> float:
        """Reverse adjust value by position ratio.

        PHP: FundReference::ReverseAdjustPosition($fVal)
        """
        position = self._get_position()
        base_val = self._get_calibration_base_val()
        return fund_reverse_adjust_position(position, f_val, base_val)

    def _get_position(self) -> float:
        """Get fund position ratio from fundposition table.

        PHP: $pos_sql->ReadPos($strStockId) ?: $this->GetDefaultPosition()
        
        Default: 0.95 for LOF funds, 1.0 for others (PHP: IsLofA() ? 0.95 : 1.0)
        """
        if self._db and self._sql_id:
            from app.models.market_data import FundPosition
            pos_record = self._db.query(FundPosition).get(self._sql_id)
            if pos_record:
                return pos_record.close
        
        if self._sym.is_lof_a():
            return 0.95
        return 1.0

    def get_close(self, date_str: str) -> Optional[float]:
        """Get net value for specific date.

        PHP: MysqlReference::GetClose($strDate)
        """
        if date_str == self.date:
            return self.price
        if self._db and self._sql_id:
            return _get_net_value_by_date(self._db, self._sql_id, date_str)
        return None

    def get_val(self, date_str: Optional[str] = None) -> Optional[float]:
        """Get net value.

        PHP: MysqlReference::GetVal($strDate)
        """
        if date_str:
            close = self.get_close(date_str)
            if close is not None:
                return float(close)
            return None
        return float(self.price) if self.price else None


# ============================================================
# Convenience functions
# ============================================================

def get_fund_net_value(symbol: str, db: Optional[Session] = None) -> float:
    """Get fund net value.

    First tries database, then fetches from Sina if needed.
    """
    if db:
        stock_id = _get_stock_id(db, symbol)
        if stock_id:
            # Try to get from database first
            record = _get_net_value_now(db, stock_id)
            if record:
                return record['close']

    # Fetch from Sina
    ref = FundReference(symbol, db)
    ref.load_data()
    return ref.price


def get_fund_net_value_by_date(symbol: str, date_str: str, db: Session) -> Optional[float]:
    """Get fund net value for specific date from database."""
    stock_id = _get_stock_id(db, symbol)
    if stock_id:
        return _get_net_value_by_date(db, stock_id, date_str)
    return None


def update_fund_net_value(symbol: str, db: Session) -> bool:
    """Update fund net value from Sina to database.

    Returns True if new value was inserted.
    """
    ref = FundReference(symbol, db)
    ref.load_data()
    return ref.update_official_net_value()


def get_fund_info(symbol: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Get fund information."""
    ref = FundReference(symbol, db)
    ref.load_data()

    return {
        'symbol': symbol,
        'price': ref.price,
        'prev_price': ref.prev_price,
        'date': ref.date,
        'factor': ref.factor,
    }


def get_fund_list() -> List[Dict[str, str]]:
    """Get list of common funds."""
    return [
        {'symbol': 'SH510050', 'name': '华夏上证50ETF'},
        {'symbol': 'SH510300', 'name': '华泰柏瑞沪深300ETF'},
        {'symbol': 'SZ159919', 'name': '嘉实沪深300ETF'},
        {'symbol': 'SH510500', 'name': '南方中证500ETF'},
        {'symbol': 'SZ159901', 'name': '易方达深证100ETF'},
        {'symbol': 'SZ159902', 'name': '华夏中小板ETF'},
        {'symbol': 'SH510880', 'name': '华泰柏瑞红利ETF'},
        {'symbol': 'SZ159915', 'name': '易方达创业板ETF'},
        {'symbol': 'SZ162411', 'name': '华宝油气'},
    ]
