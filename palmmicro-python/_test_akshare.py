import os
# 清除所有代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        del os.environ[k]
os.environ['NO_PROXY'] = '*'

import akshare as ak
print('akshare version:', akshare.__version__)

print('\n=== 1. fund_open_fund_hist_em(162411) 历史净值 ===')
try:
    df = ak.fund_open_fund_hist_em(symbol='162411', period='daily',
                                    start_date='20250601', end_date='20260510',
                                    adjust='')
    print(f'OK! {len(df)} rows')
    print('cols:', df.columns.tolist())
    print(df.tail(5).to_string())
except Exception as e:
    print(f'FAIL: {type(e).__name__}: {e}')

print('\n=== 2. stock_zh_a_hist(162411) LOF交易收盘价 ===')
try:
    df2 = ak.stock_zh_a_hist(symbol='162411', period='daily',
                              start_date='20250601', end_date='20260510',
                              adjust='')
    print(f'OK! {len(df2)} rows')
    print('cols:', df2.columns.tolist())
    print(df2.tail(5).to_string())
except Exception as e:
    print(f'FAIL: {type(e).__name__}: {e}')

print('\n=== 3. stock_zh_a_spot_em() 实时 ===')
try:
    df3 = ak.stock_zh_a_spot_em()
    row = df3[df3['代码'] == '162411']
    if not row.empty:
        print(row[['代码','名称','最新价','涨跌幅']].to_string())
    else:
        print('162411 not found in spot data')
        print('Available codes:', df3[df3['代码'].str.startswith('162')][['代码','名称']].head(10).to_string())
except Exception as e:
    print(f'FAIL: {type(e).__name__}: {e}')
