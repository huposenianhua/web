"""Stock transaction handling.

Translated from PHP stocktrans.php.
Provides transaction tracking and profit calculation.
"""

from typing import Optional


class StockTransaction:
    """Base stock transaction class."""
    
    def __init__(self):
        self._total_shares = 0
        self._total_cost = 0.0
        self._total_records = 0
    
    @property
    def total_shares(self):
        return self._total_shares
    
    @property
    def total_cost(self):
        return self._total_cost
    
    @property
    def total_records(self):
        return self._total_records
    
    def get_total_shares(self) -> int:
        """Get total number of shares."""
        return self._total_shares
    
    def get_total_cost(self) -> float:
        """Get total cost."""
        return self._total_cost
    
    def get_total_records(self) -> int:
        """Get total number of records."""
        return self._total_records
    
    def set_value(self, total_records: int = 0, total_shares: int = 0, total_cost: float = 0.0):
        """Set transaction values."""
        self._total_cost = total_cost
        self._total_shares = total_shares
        self._total_records = total_records
    
    def add_transaction(self, shares: int, cost: float = 0.0):
        """Add a new transaction."""
        self._total_cost += cost
        self._total_shares += shares
        self._total_records += 1
    
    def add(self, trans: 'StockTransaction'):
        """Add another transaction to this one."""
        self.add_transaction(trans.get_total_shares(), trans.get_total_cost())
    
    def get_avg_cost(self) -> float:
        """Calculate average cost per share."""
        if self._total_shares != 0:
            return self._total_cost / self._total_shares
        return 0.0


class MyStockTransaction(StockTransaction):
    """User-specific stock transaction with reference."""
    
    def __init__(self, ref, group_id: str = None):
        super().__init__()
        self._ref = ref
        self._group_id = group_id
        self._stock_group_item_id = None
        
        if group_id and ref:
            pass
    
    def get_ref(self):
        """Get stock reference."""
        return self._ref
    
    def get_group_id(self) -> Optional[str]:
        """Get group ID."""
        return self._group_id
    
    def get_symbol(self) -> Optional[str]:
        """Get stock symbol."""
        if self._ref:
            return self._ref.symbol
        return None
    
    def get_avg_cost_display(self) -> str:
        """Get formatted average cost display."""
        if self._ref:
            return self._ref.get_price_display(self.get_avg_cost())
        return ''
    
    def get_value(self) -> float:
        """Calculate current value."""
        if self._ref:
            price = self._ref.price if self._ref.price else 0.0
            return self.get_total_shares() * price
        return 0.0
    
    def get_profit(self) -> float:
        """Calculate profit."""
        return self.get_value() - self.get_total_cost()
    
    def get_profit_display(self) -> str:
        """Get formatted profit display."""
        from app.services.stock import get_number_display
        return get_number_display(self.get_profit())


def get_sql_transaction_date(record: dict) -> str:
    """Extract date from filled datetime string."""
    filled = record.get('filled', '')
    if filled:
        return filled.split(' ')[0]
    return ''


def add_sql_transaction(trans: StockTransaction, record: dict):
    """Add transaction from SQL record."""
    quantity = int(record.get('quantity', 0))
    price = float(record.get('price', 0.0))
    fees = float(record.get('fees', 0.0))
    trans.add_transaction(quantity, quantity * price + fees)


def update_stock_group_item_transaction(sql, group_item_id: str):
    """Update stock group item transaction."""
    trans = StockTransaction()
    pass


def update_stock_group_item(group_id: str, group_item_id: str):
    """Update stock group item."""
    if not group_id or not group_item_id:
        return
    pass