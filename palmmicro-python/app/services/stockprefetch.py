"""Stock data prefetching utility.

Translated from PHP stock/stockprefetch.php.
Handles bulk fetching and caching of stock data for improved performance.
"""

import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.mystockref import MyStockReference
from app.services.yahoostock import YahooStock
from app.services.stocksymbol import StockSymbol


class StockPrefetch:
    """Stock data prefetching and caching manager."""
    
    _instance = None
    _cache: Dict[str, dict] = {}
    _cache_time: Dict[str, float] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        return cls()
    
    def get_cached(self, symbol: str, max_age: int = 300) -> Optional[dict]:
        """Get cached data if fresh."""
        symbol = symbol.upper()
        if symbol in self._cache:
            age = time.time() - self._cache_time[symbol]
            if age < max_age:
                return self._cache[symbol]
        return None
    
    def set_cached(self, symbol: str, data: dict):
        """Cache stock data."""
        symbol = symbol.upper()
        self._cache[symbol] = data
        self._cache_time[symbol] = time.time()
    
    def fetch_realtime(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch real-time data for multiple symbols."""
        result = {}
        fresh_symbols = []
        
        for symbol in symbols:
            cached = self.get_cached(symbol)
            if cached:
                result[symbol] = cached
            else:
                fresh_symbols.append(symbol)
        
        if fresh_symbols:
            fresh_data = self._fetch_batch_realtime(fresh_symbols)
            result.update(fresh_data)
        
        return result
    
    def _fetch_batch_realtime(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch real-time data for symbols not in cache."""
        result = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {}
            
            for symbol in symbols:
                future = executor.submit(self._fetch_single_realtime, symbol)
                future_to_symbol[future] = symbol
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data and data.get('price', 0) > 0:
                        result[symbol] = data
                        self.set_cached(symbol, data)
                except Exception:
                    pass
        
        return result
    
    def _fetch_single_realtime(self, symbol: str) -> Optional[dict]:
        """Fetch real-time data for a single symbol."""
        ref = MyStockReference(symbol)
        if ref.fetch():
            return ref.get_data_dict()
        return None
    
    def fetch_historical(self, symbols: List[str], days: int = 30) -> Dict[str, List[dict]]:
        """Fetch historical data for multiple symbols."""
        result = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_symbol = {}
            
            for symbol in symbols:
                future = executor.submit(self._fetch_single_historical, symbol, days)
                future_to_symbol[future] = symbol
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        result[symbol] = data
                except Exception:
                    pass
        
        return result
    
    def _fetch_single_historical(self, symbol: str, days: int) -> Optional[List[dict]]:
        """Fetch historical data for a single symbol."""
        yahoo = YahooStock(symbol)
        return yahoo.fetch_daily(days)
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols."""
        result = {}
        realtime_data = self.fetch_realtime(symbols)
        
        for symbol in symbols:
            if symbol in realtime_data:
                result[symbol] = realtime_data[symbol].get('price', 0.0)
            else:
                yahoo = YahooStock(symbol)
                price = yahoo.get_latest_price()
                if price > 0:
                    result[symbol] = price
        
        return result
    
    def get_average_price(self, symbols: List[str]) -> float:
        """Get average price of a list of symbols."""
        prices = self.fetch_prices(symbols)
        if not prices:
            return 0.0
        return sum(prices.values()) / len(prices)
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_time.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        now = time.time()
        fresh = 0
        stale = 0
        
        for symbol in self._cache:
            age = now - self._cache_time[symbol]
            if age < 300:
                fresh += 1
            else:
                stale += 1
        
        return {
            'total': len(self._cache),
            'fresh': fresh,
            'stale': stale
        }


# ============================================================
# Global instance
# ============================================================

prefetch = StockPrefetch()


# ============================================================
# Helper functions (matching PHP stock.php)
# ============================================================

def stock_prefetch_extended_data(symbols: List[str]) -> None:
    """Prefetch extended data for multiple symbols.

    PHP: StockPrefetchArrayExtendedData($ar)
      $arAll = array();
      foreach ($ar as $strSymbol) {
          if ($sql->GetId($strSymbol))  $arAll = array_merge($arAll, _getAllSymbolArray($strSymbol));
          else                          $arAll[] = $strSymbol;
      }
      StockPrefetchArrayData($arAll);
    """
    # Expand symbols to include related symbols
    all_symbols = set()
    for symbol in symbols:
        symbol = symbol.upper()
        all_symbols.add(symbol)
        # Add related symbols based on type
        sym = StockSymbol(symbol)
        if sym.is_fund_qdii():
            from app.services.qdiiref import qdii_get_est_symbol
            est = qdii_get_est_symbol(symbol)
            if est:
                all_symbols.add(est)
        # Add forex for QDII or A-shares
        if sym.is_fund_qdii() or sym.is_symbol_a():
            all_symbols.add('fx_susdcny')

    # Prefetch all symbols
    prefetch.fetch_realtime(list(all_symbols))


def get_stock_data(symbol: str, force_refresh: bool = False) -> Optional[dict]:
    """Get stock data with caching."""
    if not force_refresh:
        cached = prefetch.get_cached(symbol)
        if cached:
            return cached
    
    ref = MyStockReference(symbol)
    if ref.fetch():
        data = ref.get_data_dict()
        prefetch.set_cached(symbol, data)
        return data
    return None


def get_price(symbol: str, force_refresh: bool = False) -> float:
    """Get current price with caching."""
    data = get_stock_data(symbol, force_refresh)
    return data.get('price', 0.0) if data else 0.0


def get_prices(symbols: List[str]) -> Dict[str, float]:
    """Get prices for multiple symbols."""
    return prefetch.fetch_prices(symbols)