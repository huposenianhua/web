"""Sina Finance real-time data fetcher.

Translated from PHP stock/mystockref.php.
Fetches real-time stock quotes from Sina Finance API.
"""

import time
import re
from typing import Optional

from app.services.stockref import StockRef
from app.utils.http_client import HttpClient


class MyStockReference(StockRef):
    """Sina Finance stock data fetcher.
    
    Supports A-shares, H-shares, US stocks, funds, indices, futures, and forex.
    """
    
    _BASE_URL = "http://hq.sinajs.cn/list="
    _SINA_REFERER = "http://finance.sina.com.cn"

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self._http_client = HttpClient()

    def fetch(self) -> bool:
        """Fetch data from Sina Finance API."""
        sina_symbol = self._symbol.get_sina_symbol()
        url = self._BASE_URL + sina_symbol

        try:
            response = self._http_client.get(
                url, timeout=10,
                headers={"Referer": self._SINA_REFERER},
            )
            if response and response.status_code == 200:
                content = response.text
                return self.parse(content)
            else:
                self.error = f"HTTP error: {response.status_code if response else 'None'}"
                return False
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse(self, data: str) -> bool:
        """Parse Sina Finance response.
        
        Sina returns data in format:
        var hq_str_sh600519="贵州茅台,1680.00,1670.00,...";
        
        Returns:
            True if parsing successful.
        """
        try:
            pattern = r'var hq_str_[^=]+="([^"]+)"'
            match = re.search(pattern, data)
            if not match:
                self.error = "No data found"
                return False
            
            fields = match.group(1).split(',')
            
            symbol_type = self._symbol.get_type()
            
            if symbol_type in ('a_share', 'fund', 'qdii'):
                return self._parse_a_share(fields)
            elif symbol_type == 'h_share':
                return self._parse_h_share(fields)
            elif symbol_type == 'us_stock':
                return self._parse_us_stock(fields)
            elif symbol_type == 'index':
                return self._parse_index(fields)
            elif symbol_type == 'future':
                return self._parse_future(fields)
            elif symbol_type == 'forex':
                return self._parse_forex(fields)
            else:
                return self._parse_generic(fields)
        
        except Exception as e:
            self.error = f"Parse error: {str(e)}"
            return False
    
    def _parse_a_share(self, fields: list) -> bool:
        """Parse A-share data (60+ fields)."""
        if len(fields) < 32:
            return False

        # A-share format:
        # 0: name, 1: open, 2: prev_close, 3: price, 4: high, 5: low
        # 6: buy1, 7: sell1, 8: volume, 9: amount
        # 10-14: buy1-buy5 prices, 15-19: buy1-buy5 volumes
        # 20-24: sell1-sell5 prices, 25-29: sell1-sell5 volumes
        # 30: date, 31: time

        self.name = fields[0]
        self.open = float(fields[1]) if fields[1] else 0.0
        prev_close = float(fields[2]) if fields[2] else 0.0
        self.prev_price = prev_close
        self.price = float(fields[3]) if fields[3] else 0.0
        self.high = float(fields[4]) if fields[4] else 0.0
        self.low = float(fields[5]) if fields[5] else 0.0
        self.volume = int(float(fields[8])) if fields[8] else 0

        if len(fields) > 30 and fields[30]:
            self.date = fields[30]
        if len(fields) > 31 and fields[31]:
            self.time_hm = fields[31]

        if prev_close > 0:
            self.change = self.price - prev_close
            self.change_percent = (self.change / prev_close) * 100

        self.last_update = time.time()
        return True
    
    def _parse_h_share(self, fields: list) -> bool:
        """Parse H-share data."""
        if len(fields) < 11:
            return False
        
        # H-share format:
        # 0: name, 1: price, 2: change, 3: change_percent, 4: high, 5: low
        # 6: open, 7: volume, 8: amount, 9: time
        
        self.name = fields[0]
        self.price = float(fields[1]) if fields[1] else 0.0
        self.change = float(fields[2]) if fields[2] else 0.0
        self.change_percent = float(fields[3]) if fields[3] else 0.0
        self.high = float(fields[4]) if fields[4] else 0.0
        self.low = float(fields[5]) if fields[5] else 0.0
        self.open = float(fields[6]) if fields[6] else 0.0
        self.volume = int(float(fields[7])) if fields[7] else 0
        
        self.last_update = time.time()
        return True
    
    def _parse_us_stock(self, fields: list) -> bool:
        """Parse US stock data."""
        if len(fields) < 8:
            return False
        
        # US stock format:
        # 0: name, 1: price, 2: change, 3: change_percent, 4: high, 5: low
        # 6: open, 7: volume
        
        self.name = fields[0]
        self.price = float(fields[1]) if fields[1] else 0.0
        self.change = float(fields[2]) if fields[2] else 0.0
        self.change_percent = float(fields[3]) if fields[3] else 0.0
        self.high = float(fields[4]) if fields[4] else 0.0
        self.low = float(fields[5]) if fields[5] else 0.0
        self.open = float(fields[6]) if fields[6] else 0.0
        self.volume = int(float(fields[7])) if fields[7] else 0
        
        self.last_update = time.time()
        return True
    
    def _parse_index(self, fields: list) -> bool:
        """Parse index data."""
        if len(fields) < 10:
            return False
        
        # Index format:
        # 0: name, 1: open, 2: prev_close, 3: price, 4: high, 5: low
        # 6: volume, 7: amount, 8: up_count, 9: down_count
        
        self.name = fields[0]
        self.open = float(fields[1]) if fields[1] else 0.0
        prev_close = float(fields[2]) if fields[2] else 0.0
        self.price = float(fields[3]) if fields[3] else 0.0
        self.high = float(fields[4]) if fields[4] else 0.0
        self.low = float(fields[5]) if fields[5] else 0.0
        
        if prev_close > 0:
            self.change = self.price - prev_close
            self.change_percent = (self.change / prev_close) * 100
        
        self.last_update = time.time()
        return True
    
    def _parse_future(self, fields: list) -> bool:
        """Parse futures data."""
        if len(fields) < 10:
            return False
        
        # Futures format:
        # 0: name, 1: price, 2: change, 3: change_percent, 4: high, 5: low
        # 6: open, 7: settle, 8: volume, 9: open_interest
        
        self.name = fields[0]
        self.price = float(fields[1]) if fields[1] else 0.0
        self.change = float(fields[2]) if fields[2] else 0.0
        self.change_percent = float(fields[3]) if fields[3] else 0.0
        self.high = float(fields[4]) if fields[4] else 0.0
        self.low = float(fields[5]) if fields[5] else 0.0
        self.open = float(fields[6]) if fields[6] else 0.0
        self.volume = int(float(fields[8])) if fields[8] else 0
        
        self.last_update = time.time()
        return True
    
    def _parse_forex(self, fields: list) -> bool:
        """Parse forex data."""
        if len(fields) < 8:
            return False
        
        # Forex format:
        # 0: name, 1: bid, 2: ask, 3: price, 4: change, 5: change_percent
        # 6: high, 7: low
        
        self.name = fields[0]
        self.price = float(fields[3]) if fields[3] else 0.0
        self.change = float(fields[4]) if fields[4] else 0.0
        self.change_percent = float(fields[5]) if fields[5] else 0.0
        self.high = float(fields[6]) if fields[6] else 0.0
        self.low = float(fields[7]) if fields[7] else 0.0
        
        self.last_update = time.time()
        return True
    
    def _parse_generic(self, fields: list) -> bool:
        """Fallback parser for unknown types."""
        if len(fields) < 4:
            return False
        
        self.name = fields[0] if fields[0] else str(self._symbol)
        
        try:
            self.price = float(fields[1]) if fields[1] else 0.0
            if len(fields) > 2:
                self.change = float(fields[2]) if fields[2] else 0.0
            if len(fields) > 3:
                self.change_percent = float(fields[3]) if fields[3] else 0.0
            if len(fields) > 4:
                self.high = float(fields[4]) if fields[4] else 0.0
            if len(fields) > 5:
                self.low = float(fields[5]) if fields[5] else 0.0
            
            self.last_update = time.time()
            return True
        except ValueError:
            return False


# ============================================================
# Batch fetch utilities
# ============================================================

async def fetch_batch(symbols: list) -> dict:
    """Fetch multiple symbols in a single request."""
    if not symbols:
        return {}
    
    sina_symbols = [StockRef(s)._symbol.get_sina_symbol() for s in symbols]
    url = MyStockReference._BASE_URL + ','.join(sina_symbols)
    
    http_client = HttpClient()
    try:
        response = await http_client.get_async(url, timeout=15)
        if response and response.status_code == 200:
            return _parse_batch_response(response.text, symbols)
    except Exception:
        pass
    
    return {}


def _parse_batch_response(data: str, symbols: list) -> dict:
    """Parse batch response into dictionary of results."""
    result = {}
    lines = data.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.search(r'var hq_str_([a-z]+[_]?[a-z0-9]+)="([^"]+)"', line, re.IGNORECASE)
        if match:
            sina_symbol = match.group(1).lower()
            fields = match.group(2).split(',')
            
            for symbol in symbols:
                ref = MyStockReference(symbol)
                if ref._symbol.get_sina_symbol().lower() == sina_symbol:
                    ref.parse(line)
                    result[symbol] = ref.get_data_dict()
                    break
    
    return result