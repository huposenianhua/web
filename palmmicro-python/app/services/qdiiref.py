"""QDII fund estimation.

Translated from PHP stock/qdiiref.php.
Estimates QDII fund net value based on underlying holdings.
Uses database for historical data, matching PHP original.

PHP对应:
  - QdiiGetCalibration()   → qdii_get_calibration()
  - QdiiGetVal()           → qdii_get_val()
  - QdiiGetPeerVal()       → qdii_get_peer_val()
  - QdiiGetEstArray()      → QDII_EST_ARRAY
  - QdiiGetEstSymbol()     → qdii_get_est_symbol()
  - _QdiiReference         → _QdiiReference
  - QdiiReference          → QdiiReference
  - QdiiHkReference        → QdiiHkReference
  - QdiiJpReference        → QdiiJpReference
  - QdiiEuReference        → QdiiEuReference

PHP数据流:
  1. QdiiReference.__construct() → 设置标的Reference（如XOP）
  2. EstNetValue() → AdjustFactor() → 更新校准因子
  3. _getEstNetValue() → 从数据库查询标的历史净值
  4. GetQdiiValue() → 计算QDII估算净值
  5. AdjustPosition() → 应用仓位调整
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session

from app.services.fundref import FundReference, fund_adjust_position
from app.services.stocksymbol import StockSymbol
from app.services.yahoostock import YahooStock, yahoo_update_net_value
from app.services.cnyref import CnyReference
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# Helper functions (matching PHP qdiiref.php)
# ============================================================

def qdii_get_calibration(est: float, cny: float, net_value: float) -> float:
    """Calculate calibration factor.

    PHP: QdiiGetCalibration($strEst, $strCNY, $strNetValue)
    Formula: factor = est * cny / net_value
    """
    if abs(net_value) < 1e-8:
        return 1.0
    return est * cny / net_value


def qdii_get_val(est: float, cny: float, factor: float) -> float:
    """Calculate QDII value from estimate.

    PHP: QdiiGetVal($fEst, $fCny, $fFactor)
    Formula: value = est * cny / factor
    """
    if abs(factor) < 1e-8:
        return 0.0
    return est * cny / factor


def qdii_get_peer_val(qdii: float, cny: float, factor: float) -> float:
    """Calculate estimate value from QDII.

    PHP: QdiiGetPeerVal($fQdii, $fCny, $fFactor)
    Formula: est = qdii * factor / cny
    """
    if abs(cny) < 1e-8:
        return 0.0
    return qdii * factor / cny


# ============================================================
# QDII symbol arrays (matching PHP stocksymbol.php)
# ============================================================

# PHP: QdiiGetXopSymbolArray() = ['SH513350', 'SZ159518', 'SZ162411']
QDII_XOP_SYMBOLS = ['SH513350', 'SZ159518', 'SZ162411']

# PHP: QdiiGetXbiSymbolArray() = ['SZ159502', 'SZ161127']
QDII_XBI_SYMBOLS = ['SZ159502', 'SZ161127']

# PHP: QdiiGetSpySymbolArray()
QDII_SPY_SYMBOLS = ['SZ159655', 'SZ161125', 'SZ160723', 'SZ160719']

# PHP: QdiiGetQqqSymbolArray()
QDII_QQQ_SYMBOLS = ['SH513300', 'SH501018', 'SH501021', 'SZ161130', 'SZ164701']

# PHP: QdiiGetEstArray()
QDII_EST_ARRAY = {
    'SH501300': 'AGG',
    'SH513290': 'IBB',
    'SH513400': '^DJI',
    'SZ160140': 'VNQ',
    'SZ160416': 'IXC',
    'SZ161126': 'RSPH',
    'SZ161128': 'XLK',
    'SZ162415': 'XLY',
    'SZ162719': 'IEO',
    'SZ164824': 'INDA',
    'SZ164906': 'KWEB',
}

# Add XOP symbols
for sym in QDII_XOP_SYMBOLS:
    QDII_EST_ARRAY[sym] = 'XOP'

# Add XBI symbols
for sym in QDII_XBI_SYMBOLS:
    QDII_EST_ARRAY[sym] = 'XBI'

# Add SPY symbols (^GSPC = S&P 500 index)
for sym in QDII_SPY_SYMBOLS:
    QDII_EST_ARRAY[sym] = '^GSPC'

# Add QQQ symbols (^NDX = Nasdaq 100 index)
for sym in QDII_QQQ_SYMBOLS:
    QDII_EST_ARRAY[sym] = '^NDX'


def qdii_get_est_symbol(symbol: str) -> Optional[str]:
    """Get estimate symbol for QDII fund.

    PHP: QdiiGetEstSymbol($strSymbol)
    """
    return QDII_EST_ARRAY.get(symbol.upper())


def qdii_hk_get_est_symbol(symbol: str) -> Optional[str]:
    """Get estimate symbol for HK QDII fund.

    PHP: QdiiHkGetEstSymbol($strSymbol)
    """
    symbol = symbol.upper()
    if symbol == 'SH501025':
        return 'SH000869'
    # Tech QDII HK -> ^HSTECH
    # Hang Seng QDII HK -> ^HSI
    # H-Shares QDII HK -> ^HSCE
    return None


def qdii_jp_get_est_symbol(symbol: str) -> Optional[str]:
    """Get estimate symbol for JP QDII fund.

    PHP: QdiiJpGetEstSymbol($strSymbol)
    """
    return None


def qdii_eu_get_est_symbol(symbol: str) -> Optional[str]:
    """Get estimate symbol for EU QDII fund.

    PHP: QdiiEuGetEstSymbol($strSymbol)
    """
    return None


def in_array_xop_qdii(symbol: str) -> bool:
    """Check if symbol is XOP-tracking QDII.

    PHP: in_arrayXopQdii($strSymbol)
    """
    return symbol.upper() in QDII_XOP_SYMBOLS


def in_array_xbi_qdii(symbol: str) -> bool:
    """Check if symbol is XBI-tracking QDII.

    PHP: in_arrayXbiQdii($strSymbol)
    """
    return symbol.upper() in QDII_XBI_SYMBOLS


def in_array_spy_qdii(symbol: str) -> bool:
    """Check if symbol is SPY-tracking QDII.

    PHP: in_arraySpyQdii($strSymbol)
    """
    return symbol.upper() in QDII_SPY_SYMBOLS


def in_array_qqq_qdii(symbol: str) -> bool:
    """Check if symbol is QQQ-tracking QDII.

    PHP: in_arrayQqqQdii($strSymbol)
    """
    return symbol.upper() in QDII_QQQ_SYMBOLS


# ============================================================
# Database helpers
# ============================================================

def _get_stock_id(db: Session, symbol: str, create: bool = False) -> Optional[int]:
    """Get stock_id for symbol."""
    from app.models.stock import Stock
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        from app.services.stocksymbol import StockSymbol
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


def _get_history_close_prev(db: Session, stock_id: int, date_str: str) -> Optional[float]:
    """Get previous close from stockhistory.

    PHP: $his_sql->GetClosePrev($strStockId, $strDate)
    """
    from app.models.market_data import StockHistory
    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    record = db.query(StockHistory).filter(
        StockHistory.stock_id == stock_id,
        StockHistory.date < dt
    ).order_by(StockHistory.date.desc()).first()
    return record.close if record else None


def _get_fund_est_now(db: Session, stock_id: int) -> Optional[Dict[str, Any]]:
    """Get latest fund estimate record.

    PHP: $fund_est_sql->GetRecordNow($strStockId)
    """
    from app.models.market_data import FundEst
    record = db.query(FundEst).filter(
        FundEst.stock_id == stock_id
    ).order_by(FundEst.date.desc()).first()
    if record:
        return {'date': record.date.strftime('%Y-%m-%d'), 'close': record.close}
    return None


def _write_fund_est(db: Session, stock_id: int, date_str: str, value: float):
    """Write estimated net value.

    PHP: $fund_est_sql->WriteDaily($strStockId, $strDate, $strNetValue)
    """
    from app.models.market_data import FundEst
    from sqlalchemy.dialects.mysql import insert as mysql_insert
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
# _QdiiReference (matching PHP _QdiiReference)
# ============================================================

class _QdiiReference(FundReference):
    """Base QDII reference class.

    PHP: class _QdiiReference extends FundReference

    核心功能:
      1. 从数据库查询标的历史净值
      2. 计算校准因子
      3. 估算QDII净值
      4. 应用仓位调整
    """

    def __init__(self, symbol: str, cny_symbol: str, db: Optional[Session] = None):
        """
        Args:
            symbol: QDII基金代码，如 'SZ162411'
            cny_symbol: 汇率代码，如 'USCNY', 'HKCNY'
            db: SQLAlchemy session
        """
        super().__init__(symbol, db)

        self._cny_symbol = cny_symbol
        self._official_cny: Optional[float] = None
        self._est_ref: Optional[YahooStock] = None
        self._forex_ref: Optional['MyStockReference'] = None

        # Set forex reference
        if db:
            self._cny_ref = CnyReference(cny_symbol, db)

    def set_est_ref(self, est_symbol: str):
        """Set estimate reference (underlying ETF/index).

        PHP: $this->SetEstRef($est_ref)
        """
        self._est_ref = YahooStock(est_symbol, self._db)

    def set_forex_ref(self, forex_symbol: str):
        """Set forex reference for realtime rate.

        PHP: $this->SetForexRef($strSymbol)
          $this->forex_ref = new MyStockReference($strSymbol);
        Uses Sina realtime forex API (e.g. 'fx_susdcny' → hq.sinajs.cn/list=fx_susdcny).
        This is used by GetQdiiValue() for fair/realtime net value calculation,
        providing intraday exchange rates instead of China Money's daily 9:15 fixings.
        """
        from app.services.mystockref import MyStockReference
        self._forex_ref = MyStockReference(forex_symbol)
        self._forex_ref.fetch()

    def get_forex_ref(self) -> Optional['MyStockReference']:
        """Get forex reference.

        PHP: GetForexRef()
          return $this->IsEtfA() ? $this->forex_ref : $this->cny_ref;
        For LOF/ETF-A funds: returns realtime Sina forex (fx_susdcny)
        For other funds: falls back to China Money daily rate
        """
        if self._forex_ref and self._forex_ref.price > 0:
            return self._forex_ref
        return None

    def _get_est_net_value(self, est_ref: YahooStock, date_str: str) -> Optional[float]:
        """Get estimate net value from database.

        PHP: _getEstNetValue($est_ref, $strDate)
          if ($str = SqlGetNetValueByDate($est_ref->GetStockId(), $strDate))
              return $str;
          return false;
        """
        if self._db and est_ref.sql_id:
            return _get_net_value_by_date(self._db, est_ref.sql_id, date_str)
        return None

    def _get_est_price(self, est_ref: YahooStock, date_str: str) -> Optional[float]:
        """Get estimate price.

        PHP: _getEstPrice($est_ref, $strDate)
          $str = $est_ref->GetPrice();
          if (empty($str)) {
              $his_sql = GetStockHistorySql();
              $str = $his_sql->GetClosePrev($est_ref->GetStockId(), $strDate);
          }
          return $str;
        """
        price = est_ref.get_latest_price()
        if price and price > 0:
            return price

        # Fallback to history
        if self._db and est_ref.sql_id:
            return _get_history_close_prev(self._db, est_ref.sql_id, date_str)
        return None

    def _get_official_est_val(self, date_str: str) -> Optional[float]:
        """Get official estimate value.

        PHP: _getOfficialEstVal($strDate)
          $est_ref = $this->GetEstRef();
          if ($str = $this->_getEstNetValue($est_ref, $strDate)) return $str;
          return $this->_getEstPrice($est_ref, $strDate);
        """
        if not self._est_ref:
            return None

        # 1. Try database first
        val = self._get_est_net_value(self._est_ref, date_str)
        if val is not None:
            return val

        # 2. Fallback to price
        return self._get_est_price(self._est_ref, date_str)

    def _get_fair_est_val(self, date_str: str) -> Optional[float]:
        """Get fair estimate value.

        PHP: _getFairEstVal($strDate)
        """
        return self._get_official_est_val(date_str)

    def adjust_factor(self) -> Optional[float]:
        """Adjust calibration factor.

        PHP: AdjustFactor()
          if ($this->UpdateOfficialNetValue()) {
              $strDate = $this->GetDate();
              $cny_ref = $this->GetCnyRef();
              if ($strCNY = $cny_ref->GetClose($strDate)) {
                  $est_ref = $this->GetEstRef();
                  if (($strEst = $this->_getEstNetValue($est_ref, $strDate)) === false) {
                      if (($strEst = $est_ref->GetClose($strDate)) === false) return false;
                  }
                  $this->fFactor = QdiiGetCalibration($strEst, $strCNY, $this->GetPrice());
                  $this->InsertFundCalibration();
                  return $this->fFactor;
              }
          }
          return false;
        """
        if not self.update_official_net_value():
            if self._db and self._sql_id:
                from app.services.fundref import _get_net_value_by_date
                existing = _get_net_value_by_date(self._db, self._sql_id, self.date)
                if not existing:
                    return None
            else:
                return None

        date_str = self.date
        if not self._db or not self._sql_id:
            return None

        cny_val = self._cny_ref.get_close(date_str) if self._cny_ref else None
        if cny_val is None:
            return None

        est_val = self._get_est_net_value(self._est_ref, date_str) if self._est_ref else None
        if est_val is None and self._est_ref:
            est_val = self._est_ref.get_price_at_date(date_str)
        if est_val is None and self._est_ref:
            prior = self._est_ref.get_price_at_or_before_date(date_str)
            if prior:
                est_val, est_actual_date = prior
                logger.info(f"Using prior XOP price for calibration: {est_val} (date={est_actual_date}, target={date_str})")
            else:
                if self._est_ref.date <= date_str:
                    est_val = self._est_ref.price
                    logger.info(f"Using realtime est price for calibration: {est_val} (date={self._est_ref.date})")
                else:
                    logger.warning(f"XOP realtime date {self._est_ref.date} is after fund date {date_str}, skipping calibration")

        if est_val is None:
            return None

        qdii_price = self.price
        if qdii_price and qdii_price > 0:
            self._factor = qdii_get_calibration(est_val, cny_val, qdii_price)
            self.insert_fund_calibration()
            return self._factor

        return None

    def est_net_value(self):
        """Estimate QDII net value.

        PHP: EstNetValue()
        """
        try:
            self.adjust_factor()
        except Exception as e:
            logger.warning(f"adjust_factor failed: {e}")

        if not self._est_ref or not self._cny_ref:
            return

        try:
            est_date = self._est_ref.date
        except Exception:
            est_date = None

        if not est_date:
            est_date = self.date

        if not est_date:
            return

        self._official_cny = self._cny_ref.get_close(est_date)

        if not self._official_cny and self._cny_ref.price > 0:
            self._official_cny = self._cny_ref.price
            logger.info(f"Using latest CNY rate {self._official_cny} for date {est_date}")

        if self._official_cny:
            est_val = self._get_official_est_val(est_date)
            if est_val:
                self._official_net_value = self.get_qdii_value(est_val, self._official_cny)
                self._official_date = est_date
                self.update_est_net_value()
        else:
            if self._db and self._sql_id:
                try:
                    record = _get_fund_est_now(self._db, self._sql_id)
                    if record:
                        self._official_date = record['date']
                        self._official_cny = self._cny_ref.get_close(self._official_date)
                        self._official_net_value = record['close']
                    else:
                        self._official_cny = self._cny_ref.price
                except Exception as e:
                    logger.warning(f"Failed to load fund est from DB: {e}")
                    self._official_cny = self._cny_ref.price

        self._est_realtime_net_value()

    def _est_realtime_net_value(self):
        """Estimate realtime net value.

        PHP: EstRealtimeNetValue()
          Re-fetches forex rate every call (no caching between calls).
        """
        if not self._est_ref:
            return

        est_date = self._est_ref.date
        # Re-fetch realtime forex rate (matches PHP: GetForexRef()->GetPrice() each call)
        if self._forex_ref:
            self._forex_ref.fetch()

        if self._cny_ref:
            cny_date = self._cny_ref.date
            if cny_date != self._official_date or est_date != self._official_date:
                est_val = self._get_fair_est_val(est_date)
                if est_val:
                    self._fair_net_value = self.get_qdii_value(est_val)

    def get_qdii_value(self, est: float, cny: Optional[float] = None) -> float:
        """Calculate QDII value from estimate.

        PHP: GetQdiiValue($strEst, $strCNY = false)
          if ($strCNY == false) {
              $cny_ref = $this->GetForexRef();
              $strCNY = $cny_ref->GetPrice();
          }
          if ($this->fFactor) {
              $fVal = QdiiGetVal(floatval($strEst), floatval($strCNY), $this->fFactor);
              return $this->AdjustPosition($fVal);
          }
          return 0.0;
        """
        if cny is None:
            forex = self.get_forex_ref()
            if forex:
                cny = forex.price
            else:
                cny = self._cny_ref.price if self._cny_ref else 0.0

        if self._factor and self._factor > 0:
            val = qdii_get_val(est, cny, self._factor)
            return self.adjust_position(val)

        return 0.0

    def get_est_value(self, qdii: float) -> float:
        """Calculate estimate value from QDII.

        PHP: GetEstValue($strQdii)
        """
        cny = self._cny_ref.price if self._cny_ref else 0.0
        adjusted = self.reverse_adjust_position(qdii)
        return qdii_get_peer_val(adjusted, cny, self._factor)

    @property
    def official_cny(self) -> Optional[float]:
        return self._official_cny

    @property
    def est_ref(self) -> Optional[YahooStock]:
        return self._est_ref


# ============================================================
# QdiiReference (matching PHP QdiiReference)
# ============================================================

class QdiiReference(_QdiiReference):
    """US QDII reference.

    PHP: class QdiiReference extends _QdiiReference
      public function __construct($strSymbol) {
          parent::__construct($strSymbol, 'USCNY');
          if ($strEstSymbol = QdiiGetEstSymbol($strSymbol)) {
              if (SqlCountHoldings($strEstSymbol) > 0) $est_ref = new HoldingsReference($strEstSymbol);
              else $est_ref = new FundPairReference($strEstSymbol);
              $this->SetEstRef($est_ref);
          }
          $this->SetForexRef('fx_susdcny');
          $this->EstNetValue();
      }
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        super().__init__(symbol, 'USCNY', db)

        est_symbol = qdii_get_est_symbol(symbol)
        if est_symbol:
            self.set_est_ref(est_symbol)

        self.set_forex_ref('fx_susdcny')

        self.load_data()

        if self._est_ref:
            self._est_ref.get_latest_price()

        self.est_net_value()


# ============================================================
# QdiiHkReference (matching PHP QdiiHkReference)
# ============================================================

class QdiiHkReference(_QdiiReference):
    """HK QDII reference.

    PHP: class QdiiHkReference extends _QdiiReference
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        super().__init__(symbol, 'HKCNY', db)

        est_symbol = qdii_hk_get_est_symbol(symbol)
        if est_symbol:
            self.set_est_ref(est_symbol)

        self.set_forex_ref('fx_shkdcny')

        self.est_net_value()


# ============================================================
# QdiiJpReference (matching PHP QdiiJpReference)
# ============================================================

class QdiiJpReference(_QdiiReference):
    """JP QDII reference.

    PHP: class QdiiJpReference extends _QdiiReference
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        super().__init__(symbol, 'JPCNY', db)

        est_symbol = qdii_jp_get_est_symbol(symbol)
        if est_symbol:
            self.set_est_ref(est_symbol)

        self.set_forex_ref('fx_sjpycny')

        self.est_net_value()


# ============================================================
# QdiiEuReference (matching PHP QdiiEuReference)
# ============================================================

class QdiiEuReference(_QdiiReference):
    """EU QDII reference.

    PHP: class QdiiEuReference extends _QdiiReference
    """

    def __init__(self, symbol: str, db: Optional[Session] = None):
        super().__init__(symbol, 'EUCNY', db)

        est_symbol = qdii_eu_get_est_symbol(symbol)
        if est_symbol:
            self.set_est_ref(est_symbol)

        self.set_forex_ref('fx_seurcny')

        self.est_net_value()


# ============================================================
# QdiiCreateGroup (matching PHP _qdiigroup.php)
# ============================================================

def qdii_create_group(
    ref: _QdiiReference,
    leverage_symbols: Optional[List[str]] = None,
    leverage_pairs: Optional[Dict[str, str]] = None
):
    """Update DB with Yahoo net value and China Money rates after EstNetValue().

    PHP: QdiiGroupAccount::QdiiCreateGroup($arLev)
      $est_ref = $ref->GetEstRef();
      if ($ar = YahooUpdateNetValue($est_ref)) { ... }
      GetChinaMoney($stock_ref);
      SzseGetLofShares($stock_ref);
      foreach ($arLev as $strSymbol) {
          $leverage_ref = new FundPairReference($strSymbol);
          YahooUpdateNetValue($leverage_ref);
          $leverage_ref->DailyCalibration();
      }

    ⚠️ 重要：此函数必须在 QdiiReference 构造（EstNetValue）之后调用。
    这是"自举"模式的核心：本次用旧数据估算，同时更新DB供下次使用。

    Args:
        ref: 已创建的 QdiiReference 实例（EstNetValue已执行）
        leverage_symbols: 杠杆ETF symbol列表（如 ['TQQQ', 'SQQQ']）
        leverage_pairs: 杠杆ETF配对关系（如 {'TQQQ': 'QQQ', 'SQQQ': 'QQQ'}）
    """
    if not ref._db:
        return

    db = ref._db
    est_ref = ref.est_ref

    # PHP: if ($ar = YahooUpdateNetValue($est_ref))
    if est_ref:
        yahoo_update_net_value(est_ref, db)

    # PHP: GetChinaMoney($stock_ref)
    from app.services.cnyref import get_china_money
    get_china_money(db)

    # PHP: SzseGetLofShares($stock_ref)
    from app.services.szse import szse_get_lof_shares
    szse_get_lof_shares(ref.symbol, db)

    # PHP: foreach ($arLev as $strSymbol) { YahooUpdateNetValue($leverage_ref); DailyCalibration(); }
    if leverage_symbols:
        from app.services.fundref import daily_calibration
        from app.models.stock import Stock

        for lev_symbol in leverage_symbols:
            # Get stock_id for leverage ETF
            lev_stock = db.query(Stock).filter(Stock.symbol == lev_symbol).first()
            if not lev_stock:
                continue

            # YahooUpdateNetValue
            lev_ref = YahooStock(lev_symbol, db)
            yahoo_update_net_value(lev_ref, db)

            # DailyCalibration
            if leverage_pairs and lev_symbol in leverage_pairs:
                pair_symbol = leverage_pairs[lev_symbol]
                pair_stock = db.query(Stock).filter(Stock.symbol == pair_symbol).first()
                if pair_stock:
                    daily_calibration(
                        stock_id=lev_stock.id,
                        pair_stock_id=pair_stock.id,
                        cny_ref=ref._cny_ref,
                        db=db
                    )


# ============================================================
# Factory function
# ============================================================

def create_qdii_reference(symbol: str, db: Optional[Session] = None) -> Optional[_QdiiReference]:
    """Create appropriate QDII reference based on symbol.

    PHP: stock_get_reference() 中根据symbol类型创建不同的Reference
    """
    sym = StockSymbol(symbol)
    normalized = sym.normalized

    if sym.is_fund_qdii() or in_array_xop_qdii(normalized) or in_array_qqq_qdii(normalized) or in_array_spy_qdii(normalized) or in_array_xbi_qdii(normalized):
        return QdiiReference(normalized, db)

    return None


# ============================================================
# Convenience functions
# ============================================================

def estimate_qdii_value(symbol: str, db: Optional[Session] = None) -> float:
    """Estimate QDII fund net value.

    使用与PHP一致的流程:
    1. 创建QdiiReference
    2. 从数据库查询历史数据
    3. 计算校准因子
    4. 估算净值
    """
    ref = create_qdii_reference(symbol, db)
    if ref:
        return ref.price
    return 0.0


def get_qdii_info(symbol: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Get QDII fund information."""
    ref = create_qdii_reference(symbol, db)
    if ref:
        return {
            'symbol': symbol,
            'price': ref.price,
            'prev_price': ref.prev_price,
            'date': ref.date,
            'factor': ref.factor,
            'official_net_value': ref.get_official_net_value(),
            'fair_net_value': ref.get_fair_net_value(),
            'official_cny': ref.official_cny,
            'est_symbol': ref.est_ref.symbol if ref.est_ref else None,
        }
    return {'symbol': symbol, 'error': 'Unknown QDII type'}


def get_qdii_list() -> List[Dict[str, str]]:
    """Get list of QDII funds."""
    return [
        {'symbol': 'SH513350', 'name': '华宝油气ETF', 'est': 'XOP'},
        {'symbol': 'SZ159518', 'name': '华宝油气LOF', 'est': 'XOP'},
        {'symbol': 'SZ162411', 'name': '华宝油气', 'est': 'XOP'},
        {'symbol': 'SH501018', 'name': '易方达纳斯达克100ETF', 'est': '^NDX'},
        {'symbol': 'SH501021', 'name': '国泰纳斯达克100ETF', 'est': '^NDX'},
        {'symbol': 'SZ161125', 'name': '易方达标普500ETF联接', 'est': '^GSPC'},
        {'symbol': 'SZ161130', 'name': '易方达纳斯达克100ETF联接', 'est': '^NDX'},
        {'symbol': 'SZ164701', 'name': '汇添富纳斯达克100', 'est': '^NDX'},
        {'symbol': 'SZ162415', 'name': '华宝标普美国消费', 'est': 'XLY'},
        {'symbol': 'SZ164906', 'name': '交银中证海外中国互联网', 'est': 'KWEB'},
    ]
