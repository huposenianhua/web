"""Stock reference base class.

Translated from PHP stock/stockref.php.
Provides StockRef base class for uniform interface to real-time data fetching,
parsing, and caching across different data sources.
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from app.services.stocksymbol import StockSymbol


class StockRef(ABC):
    """Base class for stock data references.
    
    All stock data fetchers should inherit from this class to provide
    a consistent interface for getting real-time quotes.
    
    Attributes:
        symbol: StockSymbol instance
        name: Display name
        price: Current price
        change: Price change amount
        change_percent: Price change percentage
        volume: Trading volume
        high: Day high
        low: Day low
        open: Day open
        cached: Whether data is from cache
        last_update: Timestamp of last update
    """
    
    def __init__(self, symbol: str):
        self._symbol = StockSymbol(symbol)
        self._name: str = ""
        self._price: float = 0.0
        self._prev_price: float = 0.0
        self._change: float = 0.0
        self._change_percent: float = 0.0
        self._volume: int = 0
        self._high: float = 0.0
        self._low: float = 0.0
        self._open: float = 0.0
        self._date: str = ""
        self._time_hm: str = ""
        self._cached: bool = False
        self._last_update: float = 0.0
        self._error: str = ""
    
    @property
    def symbol(self) -> StockSymbol:
        return self._symbol
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value
    
    @property
    def price(self) -> float:
        return self._price
    
    @price.setter
    def price(self, value: float):
        self._price = value
    
    @property
    def change(self) -> float:
        return self._change
    
    @change.setter
    def change(self, value: float):
        self._change = value
    
    @property
    def change_percent(self) -> float:
        return self._change_percent
    
    @change_percent.setter
    def change_percent(self, value: float):
        self._change_percent = value
    
    @property
    def volume(self) -> int:
        return self._volume
    
    @volume.setter
    def volume(self, value: int):
        self._volume = value
    
    @property
    def high(self) -> float:
        return self._high
    
    @high.setter
    def high(self, value: float):
        self._high = value
    
    @property
    def low(self) -> float:
        return self._low
    
    @low.setter
    def low(self, value: float):
        self._low = value
    
    @property
    def open(self) -> float:
        return self._open
    
    @open.setter
    def open(self, value: float):
        self._open = value
    
    @property
    def prev_price(self) -> float:
        return self._prev_price
    
    @prev_price.setter
    def prev_price(self, value: float):
        self._prev_price = value
    
    @property
    def date(self) -> str:
        return self._date
    
    @date.setter
    def date(self, value: str):
        self._date = value
    
    @property
    def time_hm(self) -> str:
        return self._time_hm
    
    @time_hm.setter
    def time_hm(self, value: str):
        self._time_hm = value
    
    @property
    def cached(self) -> bool:
        return self._cached
    
    @cached.setter
    def cached(self, value: bool):
        self._cached = value
    
    @property
    def last_update(self) -> float:
        return self._last_update
    
    @last_update.setter
    def last_update(self, value: float):
        self._last_update = value
    
    @property
    def error(self) -> str:
        return self._error
    
    @error.setter
    def error(self, value: str):
        self._error = value
    
    @abstractmethod
    def fetch(self) -> bool:
        """Fetch data from source.
        
        Returns:
            True if successful, False on error.
        """
        pass
    
    @abstractmethod
    def parse(self, data: str) -> bool:
        """Parse raw data into properties.
        
        Args:
            data: Raw data string from source.
        
        Returns:
            True if parsing successful.
        """
        pass
    
    def is_valid(self) -> bool:
        """Check if data is valid (price > 0)."""
        return self._price > 0.0001
    
    def is_fresh(self, max_age_seconds: float = 300) -> bool:
        """Check if data is fresh (within max_age_seconds)."""
        if self._last_update == 0:
            return False
        return (time.time() - self._last_update) < max_age_seconds
    
    def get_data_dict(self) -> Dict[str, Any]:
        """Get all data as a dictionary."""
        return {
            'symbol': str(self._symbol),
            'name': self._name,
            'price': self._price,
            'prev_price': self._prev_price,
            'change': self._change,
            'change_percent': self._change_percent,
            'volume': self._volume,
            'high': self._high,
            'low': self._low,
            'open': self._open,
            'date': self._date,
            'time_hm': self._time_hm,
            'cached': self._cached,
            'last_update': self._last_update,
            'error': self._error,
        }
    
    def __repr__(self):
        from app.utils.logger import strval_round
        return f"<StockRef(symbol='{self._symbol}', price={strval_round(self._price)})>"
    
    def __str__(self):
        from app.utils.logger import strval_round
        return f"{self._symbol}: {self._name} @ {strval_round(self._price)}"


class StockRefFactory:
    """Factory for creating StockRef instances based on symbol type."""
    
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register(cls, symbol_type: str, ref_class: type):
        """Register a StockRef subclass for a symbol type."""
        cls._registry[symbol_type] = ref_class
    
    @classmethod
    def create(cls, symbol: str) -> StockRef:
        """Create a StockRef instance based on symbol type."""
        sym = StockSymbol(symbol)
        symbol_type = sym.get_type()
        
        if symbol_type in cls._registry:
            return cls._registry[symbol_type](symbol)
        
        # Default to MyStockReference for unknown types
        from app.services.mystockref import MyStockReference
        return MyStockReference(symbol)