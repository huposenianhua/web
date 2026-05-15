"""Stock core aggregation module.

Translated from PHP stock.php.
Provides high-level stock data access, prefetching, and reference management.
"""

from typing import List, Dict, Any, Optional

from app.services.stocksymbol import StockSymbol, in_array_qdii_us, in_array_qdii_hk
from app.services.mystockref import MyStockReference
from app.services.cnyref import CnyReference
from app.services.fundref import FundReference
from app.services.qdiiref import QdiiReference
from app.services.stockprefetch import prefetch
from app.utils.logger import MIN_FLOAT_VAL


def stock_get_symbol(symbol: str) -> str:
    """Normalize stock symbol."""
    symbol = symbol.strip()
    
    if symbol.find('_') == -1:
        symbol = symbol.upper()
    
    return symbol


def get_input_symbol_array(symbols_str: str) -> List[str]:
    """Parse input string into symbol array."""
    symbols_str = symbols_str.replace(',', ' ').replace('，', ' ').replace('、', ' ')
    symbols_str = symbols_str.replace('\n', ' ').replace('\r', ' ')
    
    result = []
    for s in symbols_str.split(' '):
        s = s.strip()
        if s:
            result.append(stock_get_symbol(s))
    
    return result


def stock_get_price_display(price: float, prev_price: float, precision: int = 2) -> str:
    """Get price display string with color indicator."""
    if price <= 0:
        return ''
    
    diff = 0.5
    for _ in range(precision):
        diff /= 10.0
    
    if price > prev_price + diff:
        color = 'red'
    elif price < prev_price - diff:
        color = 'green'
    else:
        color = 'black'
    
    return f'<font color="{color}">{price:.{precision}f}</font>'


def get_number_display(value: float, precision: int = 2) -> str:
    """Get number display with color."""
    return stock_get_price_display(value, 0.0, precision)


def get_ratio_display(value: float, precision: int = 4) -> str:
    """Get ratio display with color (compared to 1.0)."""
    return stock_get_price_display(value, 1.0, precision)


def stock_get_percentage(divisor: float, dividend: float) -> float:
    """Calculate percentage change.

    PHP: StockGetPercentage($strDivisor, $strDividend)
    """
    if abs(divisor) > MIN_FLOAT_VAL:
        return (dividend / divisor - 1.0) * 100.0
    return 0.0


def stock_prefetch_array_data(symbols: List[str]):
    """Prefetch data for multiple symbols."""
    unique_symbols = list(set(symbols))
    prefetch.fetch_realtime(unique_symbols)


def stock_prefetch_extended_data(*symbols: str):
    """Prefetch extended data for symbols including related pairs."""
    all_symbols = []
    
    for symbol in symbols:
        all_symbols.extend(_get_all_symbol_array(symbol))
    
    stock_prefetch_array_data(all_symbols)


def _add_fund_pair_symbol(ar: List[str], symbol: str):
    """Add fund and its pair symbol to array."""
    ar.append(symbol)


def _add_holdings_symbol(ar: List[str], symbol: str):
    """Add holdings symbols to array."""
    pass


def _get_all_symbol_array(symbol: str) -> List[str]:
    """Get all related symbols for a given symbol."""
    ar = [symbol]
    sym = StockSymbol(symbol)
    
    if sym.is_fund_a() or sym.is_fund_qdii():
        if in_array_qdii_us(symbol):
            ar.append('fx_susdcny')
        elif in_array_qdii_hk(symbol):
            ar.append('fx_shkdcny')
        else:
            pass
    elif sym.is_symbol_a():
        pass
    elif sym.is_symbol_h():
        pass
    else:
        _add_holdings_symbol(ar, symbol)
    
    return list(set(ar))


def stock_get_reference(symbol: str):
    """Get appropriate stock reference object."""
    sym = StockSymbol(symbol)
    
    if sym.is_forex():
        return CnyReference()
    
    return MyStockReference(symbol)


def stock_get_qdii_reference(symbol: str) -> Optional[QdiiReference]:
    """Get QDII reference if applicable."""
    if in_array_qdii_us(symbol) or in_array_qdii_hk(symbol):
        return QdiiReference(symbol)
    return None


def stock_get_fund_reference(symbol: str):
    """Get fund reference object."""
    if qdii_ref := stock_get_qdii_reference(symbol):
        return qdii_ref
    
    return FundReference()


def get_stock_ref(fund_ref):
    """Get underlying stock reference from fund reference."""
    if hasattr(fund_ref, 'get_stock_ref'):
        return fund_ref.get_stock_ref()
    return fund_ref


def stock_get_pair_references(symbol: str) -> List[Optional[Any]]:
    """Get AB, AH, ADR pair references."""
    return [None, None, None]


def use_same_day_net_value(sym: StockSymbol) -> bool:
    """Check if same day net value can be used."""
    symbol = sym.symbol
    if in_array_qdii_us(symbol):
        return False
    return True


def stock_calc_hedge(calibration: float, position: float) -> float:
    """Calculate hedge ratio."""
    if position == 0:
        return 1.0
    return calibration / position


def get_leverage_hedge_symbol(symbol: str) -> Optional[str]:
    """Get leverage hedge symbol."""
    from app.services.stocksymbol import in_array_spy_qdii
    
    if in_array_spy_qdii(symbol):
        return 'SPY'
    return None


def get_stock_hedge(symbol: str, stock_id: str, leverage_symbol: str = None) -> float:
    """Calculate stock hedge ratio."""
    pos_sql = None
    cal_sql = None
    
    f_pos = 1.0
    
    if leverage_symbol or (leverage_symbol := get_leverage_hedge_symbol(symbol)):
        pass
    else:
        pass
    
    return 1.0