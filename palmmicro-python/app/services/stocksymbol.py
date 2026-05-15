"""Stock symbol parsing and classification.

Translated from PHP stock/stocksymbol.php.
Provides StockSymbol class for identifying stock types (A/H/US stocks, funds, futures)
and converting between different symbol formats.
"""

import re
from typing import Optional


class StockSymbol:
    """Stock symbol parser and classifier.
    
    Key responsibilities:
    1. Identify stock type (A/H/US stock, fund, future, index)
    2. Convert between different symbol formats (Sina, Yahoo, exchange-specific)
    3. Extract exchange and market information
    """
    
    def __init__(self, symbol: str):
        self._symbol = symbol.strip().upper()
        self._normalized = self._normalize_symbol(self._symbol)
    
    @property
    def symbol(self) -> str:
        return self._symbol
    
    @property
    def normalized(self) -> str:
        return self._normalized
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to consistent format."""
        s = symbol.strip().upper()
        if s.startswith('_'):
            s = s[1:]
        if s.startswith('SH') or s.startswith('SZ'):
            return s[:2] + s[2:].zfill(6)
        if s.isdigit() and len(s) == 6:
            if s.startswith('6'):
                return 'SH' + s
            return 'SZ' + s
        return s
    
    # ============================================================
    # Market type detection
    # ============================================================
    
    def is_symbol_a(self) -> bool:
        """Check if symbol is A-share (Shanghai/Shenzhen)."""
        s = self._normalized
        # shXXXXXX or szXXXXXX format
        if (s.startswith('SH') or s.startswith('SZ')) and len(s) == 8:
            try:
                int(s[2:])
                return True
            except ValueError:
                return False
        return False
    
    def is_symbol_h(self) -> bool:
        """Check if symbol is H-share (Hong Kong)."""
        s = self._normalized
        # 5-digit numeric code
        if len(s) >= 4 and len(s) <= 5 and s.isdigit():
            return True
        # HKEX format
        if s.startswith('HK') and len(s) == 7 and s[2:].isdigit():
            return True
        return False
    
    def is_symbol_us(self) -> bool:
        """Check if symbol is US stock."""
        s = self._normalized
        # NYSE/NASDAQ ticker (letters only or letters with numbers at end)
        pattern = r'^[A-Z]{1,5}[0-9]?$'
        if re.match(pattern, s):
            # Exclude index symbols
            if not s.startswith('^'):
                return True
        return False
    
    def is_fund_a(self) -> bool:
        """Check if symbol is A-share fund (ETF/LOF/QDII).

        PHP: StockSymbol::IsFundA()
          if ($this->IsSymbolA()) {
              if (_isDigitFundA($this->iDigitA)) return true;
          }

        A-share fund codes:
          11xxxx - ETF (SH510xxx, SZ159xxx)
          15xxxx - ETF (SZ159xxx)
          16xxxx - LOF/QDII (SZ162411 etc)
          18xxxx - LOF (SZ18xxxx)
          50xxxx - ETF (SH50xxxx)
          51xxxx - ETF (SH51xxxx)
        """
        s = self._normalized
        if self.is_symbol_a():
            code = s[2:]
            if len(code) == 6 and code[0] in ('1', '5'):
                second_digit = code[1]
                if second_digit in ('1', '5', '6', '8', '0'):
                    return True
        return False
    
    def is_fund_qdii(self) -> bool:
        """Check if symbol is QDII fund."""
        qdii_list = {
            'SH501018', 'SH501021', 'SH501030', 'SH501050', 'SH501060',
            'SZ160719', 'SZ160720', 'SZ160723', 'SZ160725', 'SZ161116',
            'SZ161125', 'SZ161127', 'SZ161129', 'SZ161130', 'SZ161226',
            'SZ162411', 'SZ162415', 'SZ164701', 'SZ164906', 'SZ165513',
        }
        return self._normalized in qdii_list
    
    def is_index(self) -> bool:
        """Check if symbol is an index."""
        s = self._normalized
        # Yahoo index format
        if s.startswith('^'):
            return True
        # SSE indices
        sse_indices = {'000001', '000002', '399001', '399005', '399006'}
        if s in sse_indices:
            return True
        return False
    
    def is_future(self) -> bool:
        """Check if symbol is futures contract."""
        s = self._normalized
        # Sina futures format: nf_XXX
        if s.startswith('NF_'):
            return True
        return False
    
    def is_forex(self) -> bool:
        s = self._normalized
        eastmoney_forex = {'USCNY', 'EUCNY', 'JPCNY', 'HKCNY'}
        if s in eastmoney_forex:
            return True
        return s.upper().startswith('FX_')

    def get_precision(self) -> int:
        """Get display precision based on symbol type.

        PHP: StockSymbol::GetPrecision()
          if ($this->IsFundA() || $this->IsSinaFund() || $this->IsStockB())  return 3;
          else if ($this->IsForex())                                          return 4;
          return 2;
        """
        if self.is_fund_a():
            return 3
        if self.is_forex():
            return 4
        return 2

    # ============================================================
    # Symbol format conversion
    # ============================================================
    
    def get_yahoo_symbol(self) -> str:
        """Get Yahoo Finance symbol format."""
        s = self._normalized
        
        if self.is_symbol_a():
            # A-shares use Yahoo's China market suffix
            if s.startswith('SH'):
                return s[2:] + '.SS'
            elif s.startswith('SZ'):
                return s[2:] + '.SZ'
        
        elif self.is_symbol_h():
            # H-shares
            if s.startswith('HK'):
                return s[2:] + '.HK'
            else:
                return s + '.HK'
        
        elif self.is_symbol_us():
            return s
        
        return s
    
    def get_sina_symbol(self) -> str:
        """Get Sina Finance symbol format."""
        s = self._normalized
        
        if self.is_symbol_a():
            return s.lower()
        
        elif self.is_symbol_h():
            # Sina H-share format
            if s.startswith('HK'):
                return 'hk' + s[2:]
            else:
                return 'hk' + s
        
        elif self.is_symbol_us():
            # Sina US stock format
            return 'gb_' + s.lower()
        
        elif self.is_future():
            return s.lower()
        
        elif self.is_forex():
            return s.lower()
        
        return s.lower()

    def get_sina_fund_symbol(self) -> str:
        """Get Sina fund net value symbol (f_ prefix).

        PHP: GetSinaFundSymbol() → SINA_FUND_PREFIX . strDigitA
        Returns f_162411 for SZ162411, which gives actual NAV (not trading price).
        """
        if self.is_fund_a():
            return 'f_' + self.get_digit_a()
        return ''

    def get_digit_a(self) -> str:
        """Get 6-digit A-share code without prefix."""
        if self.is_symbol_a():
            return self._normalized[2:]
        return self._normalized

    def is_shenzhen(self) -> bool:
        """Check if symbol is Shenzhen A-share.

        PHP: StockSymbol::IsShenZhenA()
        """
        return self._normalized.startswith('SZ') and self.is_symbol_a()

    def is_shenzhen_lof(self) -> bool:
        """Check if symbol is Shenzhen LOF fund.

        PHP: StockSymbol::IsShenZhenLof()
          if ($this->IsShenZhenA()) {
              if (_isDigitShenZhenLof($this->iDigitA)) return true;
          }

        Shenzhen LOF codes: 16xxxx, 18xxxx
        """
        if not self.is_shenzhen():
            return False
        digit_a = self.get_digit_a()
        if len(digit_a) != 6:
            return False
        return digit_a.startswith(('16', '18'))

    def is_lof_a(self) -> bool:
        """Check if symbol is LOF fund (Shenzhen or Shanghai).

        PHP: StockSymbol::IsLofA()
        Shenzhen LOF: 16xxxx, 18xxxx
        Shanghai LOF: 50xxxx
        """
        if self.is_shenzhen_lof():
            return True
        if self.is_symbol_a() and self._normalized.startswith('SH'):
            digit_a = self.get_digit_a()
            if digit_a.startswith('50'):
                return True
        return False

    def get_display(self, chinese: bool = True) -> str:
        """Get display name for the symbol."""
        if self.is_symbol_a():
            exchange = '沪' if self._normalized.startswith('SH') else '深'
            return f"{exchange}{self._normalized[2:]}"
        if self.is_symbol_h():
            return f"HK{self._normalized[-5:]}"
        return self._normalized
    
    # ============================================================
    # Type classification
    # ============================================================
    
    def get_type(self) -> str:
        """Get symbol type as string."""
        if self.is_index():
            return 'index'
        if self.is_future():
            return 'future'
        if self.is_forex():
            return 'forex'
        if self.is_fund_qdii():
            return 'qdii'
        if self.is_fund_a():
            return 'fund'
        if self.is_symbol_a():
            return 'a_share'
        if self.is_symbol_h():
            return 'h_share'
        if self.is_symbol_us():
            return 'us_stock'
        return 'unknown'
    
    def __repr__(self):
        return f"<StockSymbol(symbol='{self._symbol}', type='{self.get_type()}')>"
    
    def __str__(self):
        return self._symbol


# ============================================================
# Helper functions (matching PHP in_arrayQdii* functions)
# ============================================================

def in_array_qdii_us(symbol: str) -> bool:
    """Check if symbol is US-focused QDII fund."""
    qdii_us = {
        'SH501018', 'SH501021', 'SZ160719', 'SZ160723', 'SZ161116',
        'SZ161125', 'SZ161127', 'SZ161129', 'SZ161130', 'SZ162411',
        'SZ162415', 'SZ164701', 'SZ164906', 'SZ165513',
    }
    return symbol.upper() in qdii_us


def in_array_qdii_hk(symbol: str) -> bool:
    """Check if symbol is HK-focused QDII fund."""
    qdii_hk = {
        'SH501030', 'SH501050', 'SH501060', 'SZ160720', 'SZ160725',
        'SZ161226',
    }
    return symbol.upper() in qdii_hk


def in_array_spy_qdii(symbol: str) -> bool:
    """Check if symbol is SPY-related QDII fund."""
    spy_qdii = {'SZ160719', 'SZ161125'}
    return symbol.upper() in spy_qdii


def get_market_from_symbol(symbol: str) -> str:
    """Get market code from symbol."""
    sym = StockSymbol(symbol)
    if sym.is_symbol_a():
        return 'CN'
    if sym.is_symbol_h():
        return 'HK'
    if sym.is_symbol_us():
        return 'US'
    return 'UNKNOWN'