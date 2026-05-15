"""Stock group/portfolio management.

Translated from PHP stockgroup.php.
Manages stock portfolios with multi-currency support.
"""

from typing import List, Dict, Optional

from app.services.stocksymbol import StockSymbol
from app.services.stock import stock_get_reference
from app.services.stocktrans import MyStockTransaction
from app.utils.currency import MultiCurrency


class StockGroup:
    """Base stock group/portfolio class."""
    
    def __init__(self):
        self.multi_amount = MultiCurrency()
        self.multi_profit = MultiCurrency()
        self._group_id = None
    
    @property
    def group_id(self):
        return self._group_id
    
    @group_id.setter
    def group_id(self, value):
        self._group_id = value
    
    def on_stock_transaction(self, trans):
        """Update multi-currency amounts based on transaction."""
        sym = trans.ref
        
        if sym.is_symbol_a() or sym.symbol == 'fx_susdcnh':
            self.multi_amount.cny += trans.get_value()
            self.multi_profit.cny += trans.get_profit()
        elif sym.is_symbol_h():
            self.multi_amount.hkd += trans.get_value()
            self.multi_profit.hkd += trans.get_profit()
        else:
            self.multi_amount.usd += trans.get_value()
            self.multi_profit.usd += trans.get_profit()
    
    def convert_currency(self, usd_cny: float, hkd_cny: float):
        """Convert all amounts to CNY."""
        self.multi_amount.convert(usd_cny, hkd_cny)
        self.multi_profit.convert(usd_cny, hkd_cny)


class MyStockGroup(StockGroup):
    """User-specific stock group with transaction tracking."""
    
    def __init__(self, group_id: str, refs: list = None):
        super().__init__()
        self._group_id = group_id
        self._transactions = []
        
        if refs:
            for ref in refs:
                self._add_transaction(ref)
    
    @property
    def transactions(self):
        return self._transactions
    
    def get_transaction_by_symbol(self, symbol: str) -> Optional[MyStockTransaction]:
        """Get transaction by stock symbol."""
        for trans in self._transactions:
            if trans.get_symbol() == symbol:
                return trans
        return None
    
    def _add_transaction(self, ref):
        """Add a new transaction."""
        self._transactions.append(MyStockTransaction(ref, self._group_id))
    
    def _check_symbol(self, symbol: str):
        """Ensure symbol has a transaction, create if missing."""
        if not self.get_transaction_by_symbol(symbol):
            self._add_transaction(stock_get_reference(symbol))
    
    def set_value(self, symbol: str, total_records: int, total_shares: int, total_cost: float):
        """Set transaction value for a symbol."""
        self._check_symbol(symbol)
        
        for trans in self._transactions:
            if trans.get_symbol() == symbol:
                trans.set_value(total_records, total_shares, total_cost)
                self.on_stock_transaction(trans)
                break
    
    def get_total_records(self) -> int:
        """Get total number of records across all transactions."""
        total = 0
        for trans in self._transactions:
            total += trans.get_total_records()
        return total