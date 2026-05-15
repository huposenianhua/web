#!/usr/bin/env python3
"""Test script to verify all services are working correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.stocksymbol import StockSymbol, in_array_qdii_us, get_market_from_symbol
from app.services.mystockref import MyStockReference
from app.services.yahoostock import YahooStock
from app.services.cnyref import get_cny_usd, get_hkd_cny
from app.services.fundref import get_fund_net_value
from app.services.qdiiref import estimate_qdii_value
from app.services.holdingsref import get_etf_holdings
from app.services.chinamoney import get_shibor, get_lpr

def test_stocksymbol():
    """Test StockSymbol class."""
    print("Testing StockSymbol...")
    
    tests = [
        ('SH600519', 'a_share'),
        ('SZ000858', 'a_share'),
        ('00700', 'h_share'),
        ('AAPL', 'us_stock'),
        ('SH510050', 'fund'),
        ('SZ160719', 'qdii'),
    ]
    
    all_passed = True
    for symbol, expected_type in tests:
        sym = StockSymbol(symbol)
        actual_type = sym.get_type()
        if actual_type == expected_type:
            print(f"  ✓ {symbol}: {actual_type}")
        else:
            print(f"  ✗ {symbol}: expected {expected_type}, got {actual_type}")
            all_passed = False
    
    # Test symbol conversion
    sym = StockSymbol('SH600519')
    yahoo = sym.get_yahoo_symbol()
    sina = sym.get_sina_symbol()
    print(f"  ✓ SH600519 -> Yahoo: {yahoo}, Sina: {sina}")
    
    return all_passed

def test_mystockref():
    """Test MyStockReference."""
    print("\nTesting MyStockReference...")
    
    ref = MyStockReference('SH600519')
    success = ref.fetch()
    
    if success:
        print(f"  ✓ Fetched data for SH600519")
        print(f"    Name: {ref.name}")
        print(f"    Price: {ref.price:.2f}")
        print(f"    Change: {ref.change_percent:.2f}%")
        return True
    else:
        print(f"  ✗ Failed to fetch data: {ref.error}")
        return False

def test_yahoostock():
    """Test YahooStock."""
    print("\nTesting YahooStock...")
    
    yahoo = YahooStock('AAPL')
    data = yahoo.fetch_daily(days=7)
    
    if data:
        print(f"  ✓ Fetched {len(data)} days of data for AAPL")
        latest = data[-1]
        print(f"    Latest price: {latest.get('adj_close', 0):.2f}")
        return True
    else:
        print(f"  ✗ Failed to fetch data: {yahoo.error}")
        return False

def test_cnyref():
    """Test CnyRef."""
    print("\nTesting CnyRef...")
    
    cny_usd = get_cny_usd()
    hkd_cny = get_hkd_cny()
    
    if cny_usd > 0:
        print(f"  ✓ CNY/USD: {cny_usd:.4f}")
    else:
        print(f"  ✗ Failed to get CNY/USD")
        return False
    
    if hkd_cny > 0:
        print(f"  ✓ HKD/CNY: {hkd_cny:.4f}")
        return True
    else:
        print(f"  ✗ Failed to get HKD/CNY")
        return False

def test_fundref():
    """Test FundRef."""
    print("\nTesting FundRef...")
    
    value = get_fund_net_value('SH510050')
    
    if value > 0:
        print(f"  ✓ Net value for SH510050: {value:.4f}")
        return True
    else:
        print(f"  ✗ Failed to get fund net value")
        return False

def test_qdiiref():
    """Test QdiiRef."""
    print("\nTesting QdiiRef...")
    
    value = estimate_qdii_value('SZ160719')
    
    if value > 0:
        print(f"  ✓ Estimated QDII value for SZ160719: {value:.4f}")
        return True
    else:
        print(f"  ✗ Failed to estimate QDII value")
        return False

def test_holdingsref():
    """Test HoldingsRef."""
    print("\nTesting HoldingsRef...")
    
    holdings = get_etf_holdings('SH510050')
    
    if holdings:
        print(f"  ✓ Got {len(holdings)} holdings for SH510050")
        for h in holdings[:3]:
            print(f"    - {h['name']}: {h['weight']}%")
        return True
    else:
        print(f"  ✗ Failed to get holdings")
        return False

def test_chinamoney():
    """Test ChinaMoney."""
    print("\nTesting ChinaMoney...")
    
    shibor = get_shibor('ON')
    lpr = get_lpr('1Y')
    
    if shibor > 0:
        print(f"  ✓ SHIBOR ON: {shibor:.2f}%")
    else:
        print(f"  ✗ Failed to get SHIBOR")
        return False
    
    if lpr > 0:
        print(f"  ✓ LPR 1Y: {lpr:.2f}%")
        return True
    else:
        print(f"  ✗ Failed to get LPR")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing all services...")
    print("=" * 60)
    
    tests = [
        test_stocksymbol,
        test_mystockref,
        test_yahoostock,
        test_cnyref,
        test_fundref,
        test_qdiiref,
        test_holdingsref,
        test_chinamoney,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)