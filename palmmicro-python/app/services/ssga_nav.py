import os
import tempfile
from datetime import datetime

import openpyxl
import requests


def fetch_ssga_nav_excel(symbol='XOP'):
    url = (
        f'https://www.ssga.com/us/en/individual/etfs/'
        f'spdr-sp-oil-gas-exploration-production-etf-{symbol.lower()}'
        f'/library-content/products/fund-data/etfs/us/navhist-us-en-{symbol.lower()}.xlsx'
    )
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    if resp.status_code != 200:
        return None
    tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name


def parse_ssga_nav_excel(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=5, values_only=True):
        if not row[0] or row[1] is None:
            continue
        date_str = str(row[0]).strip()
        try:
            dt = datetime.strptime(date_str, '%d-%b-%Y').date()
            nav = float(row[1])
            records.append({'date': dt, 'nav': nav})
        except (ValueError, TypeError):
            continue
    os.unlink(filepath)
    return records
