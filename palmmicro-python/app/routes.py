"""Application routes."""

from flask import Blueprint, render_template, request, jsonify, Response

from app.services.stocksymbol import StockSymbol
from app.services.mystockref import MyStockReference
from app.services.stockbot import stock_bot_get_str
from app.services.stockprefetch import stock_prefetch_extended_data
from app.bot.telegram import TelegramStock
from app.bot.weixin import WeixinStock
from app.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint('main', __name__)

TELEGRAM_TOKEN = 'your_telegram_bot_token'
WECHAT_TOKEN = 'your_wechat_token'


def _get_db_session():
    """Get database session (lazy import to avoid circular dependency)."""
    try:
        from app import db
        session = db.session
        return session
    except Exception as e:
        logger.warning(f"Database session unavailable: {e}")
        return None


def _get_calibration_history(symbol, limit=10):
    """Get recent calibration history records for a stock symbol."""
    from app.models.stock import Stock
    from app.models.market_data import CalibrationHistory

    db = _get_db_session()
    if not db:
        return []

    sym = StockSymbol(symbol)
    normalized = sym.normalized

    stock = db.query(Stock).filter(
        Stock.symbol.in_([symbol, normalized, sym.get_digit_a()])
    ).first()
    if not stock:
        return []

    records = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock.id
    ).order_by(CalibrationHistory.date.desc()).limit(limit).all()

    return [
        {
            'date': r.date.strftime('%Y-%m-%d'),
            'factor': round(r.close, 4),
            'time': r.time or '',
            'num': r.num or 1,
            'cells': [
                {'value': r.date.strftime('%Y-%m-%d')},
                {'value': f'{r.close:.4f}', 'align': 'right'},
                {'value': r.time or '-', 'align': 'center'},
                {'value': str(r.num or 1), 'align': 'center'},
            ],
        }
        for r in reversed(records)
    ]


def _is_qdii(symbol: str) -> bool:
    """Check if symbol is a QDII fund."""
    from app.services.qdiiref import (
        in_array_xop_qdii, in_array_xbi_qdii,
        in_array_spy_qdii, in_array_qqq_qdii,
    )
    sym = StockSymbol(symbol)

    if sym.is_fund_qdii():
        return True

    s = sym.normalized
    return (in_array_xop_qdii(s) or in_array_xbi_qdii(s)
            or in_array_spy_qdii(s) or in_array_qqq_qdii(s))


def _handle_qdii(symbol: str):
    """Handle QDII fund request with full data flow.

    PHP对应: _qdii.php → QdiiAccount::Create()
      ① StockPrefetchArrayExtendedData()  ← 预抓取新浪
      ② new QdiiReference()               ← EstNetValue()
      ③ QdiiCreateGroup()                 ← 更新DB（Yahoo+中国货币网）
    """
    from app.services.qdiiref import (
        create_qdii_reference, qdii_create_group,
        qdii_get_est_symbol,
    )

    db = _get_db_session()

    est_symbol = qdii_get_est_symbol(symbol)
    ar = [symbol]
    if est_symbol:
        ar.append(est_symbol)
    stock_prefetch_extended_data(ar)

    ref = create_qdii_reference(symbol, db)

    if ref and db:
        try:
            qdii_create_group(ref)
        except Exception as e:
            logger.warning(f"qdii_create_group failed: {e}")

    return ref


@bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@bp.route('/stock/<symbol>')
def stock_detail(symbol):
    """Stock detail page.

    PHP对应: _qdii.php / _stock.php 网页入口
    QDII基金走完整流程：预抓取 → EstNetValue → QdiiCreateGroup
    """
    is_qdii = _is_qdii(symbol)
    qdii_data = None

    if is_qdii:
        try:
            ref = _handle_qdii(symbol)
            if ref and (ref.get_official_net_value() or ref.price > 0):
                cal_records = _get_calibration_history(symbol, limit=1)
                qdii_data = {
                    'symbol': str(ref.symbol),
                    'name': str(ref.symbol),
                    'price': ref.price,
                    'change': 0,
                    'change_percent': 0,
                    'date': ref.date,
                    'is_qdii': True,
                    'official_net_value': ref.get_official_net_value(),
                    'fair_net_value': ref.get_fair_net_value(),
                    'factor': ref.factor,
                    'est_symbol': str(ref.est_ref.symbol) if ref.est_ref else None,
                    'position': ref._get_position(),
                    'calibration_history': cal_records,
                }
        except Exception as e:
            logger.error(f"QDII flow failed for {symbol}: {e}")

    if qdii_data:
        return render_template('stock_detail.html', data=qdii_data)

    stock_ref = MyStockReference(symbol)
    stock_ref.fetch()

    data = {
        'symbol': str(stock_ref.symbol),
        'name': stock_ref.name,
        'price': stock_ref.price,
        'change': stock_ref.change,
        'change_percent': stock_ref.change_percent,
        'open': stock_ref.open,
        'high': stock_ref.high,
        'low': stock_ref.low,
        'volume': stock_ref.volume,
        'date': stock_ref.date,
        'time': stock_ref.time_hm,
        'is_qdii': is_qdii,
    }

    return render_template('stock_detail.html', data=data)


@bp.route('/api/stock/<symbol>')
def api_stock(symbol):
    """Get stock data as JSON.

    PHP对应: stockdataarray.php → GetStockDataArray()
    QDII基金走完整流程：预抓取 → EstNetValue → QdiiCreateGroup
    """
    is_qdii = _is_qdii(symbol)

    if is_qdii:
        try:
            ref = _handle_qdii(symbol)
            if ref:
                return jsonify({
                    'symbol': str(ref.symbol),
                    'name': str(ref.symbol),
                    'price': ref.price,
                    'date': ref.date,
                    'is_qdii': True,
                    'official_net_value': ref.get_official_net_value(),
                    'fair_net_value': ref.get_fair_net_value(),
                    'factor': ref.factor,
                    'est_symbol': str(ref.est_ref.symbol) if ref.est_ref else None,
                    'position': ref._get_position(),
                })
        except Exception as e:
            logger.error(f"QDII flow failed for {symbol}: {e}")

    stock_ref = MyStockReference(symbol)
    stock_ref.fetch()

    return jsonify({
        'symbol': str(stock_ref.symbol),
        'name': stock_ref.name,
        'price': stock_ref.price,
        'change': stock_ref.change,
        'change_percent': stock_ref.change_percent,
        'open': stock_ref.open,
        'high': stock_ref.high,
        'low': stock_ref.low,
        'volume': stock_ref.volume,
        'date': stock_ref.date,
        'time': stock_ref.time_hm,
        'is_qdii': is_qdii,
    })


@bp.route('/api/search')
def api_search():
    """Search stocks."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    result = stock_bot_get_str(query)
    if result:
        return jsonify({'result': result})
    return jsonify({'result': f'({query}:无数据)'})


@bp.route('/stock/<symbol>/calibration')
def calibration_history(symbol):
    """Calibration history page."""
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import CalibrationHistory

    db = _get_db_session()
    if not db:
        return render_template('calibration_history.html', data={'symbol': symbol, 'records': []})

    sym = StockSymbol(symbol)
    normalized = sym.normalized

    stock = db.query(Stock).filter(Stock.symbol.in_([symbol, normalized, sym.get_digit_a()])).first()
    if not stock:
        return render_template('calibration_history.html', data={'symbol': symbol, 'records': []})

    records = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock.id
    ).order_by(CalibrationHistory.date.desc()).limit(200).all()

    history = []
    for r in records:
        history.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'factor': round(r.close, 4) if r.close else None,
            'time': r.time or '',
            'num': r.num or 1,
        })

    return render_template('calibration_history.html', data={
        'symbol': symbol,
        'name': stock.name or symbol,
        'records': history,
        'total': len(history),
    })


@bp.route('/api/stock/<symbol>/calibration')
def api_calibration(symbol):
    """Get calibration history as JSON."""
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import CalibrationHistory

    db = _get_db_session()
    if not db:
        return jsonify({'error': 'Database unavailable'})

    sym = StockSymbol(symbol)
    normalized = sym.normalized

    stock = db.query(Stock).filter(Stock.symbol.in_([symbol, normalized, sym.get_digit_a()])).first()
    if not stock:
        return jsonify({'symbol': symbol, 'records': [], 'total': 0})

    records = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock.id
    ).order_by(CalibrationHistory.date.desc()).limit(500).all()

    return jsonify({
        'symbol': symbol,
        'records': [{
            'date': r.date.strftime('%Y-%m-%d'),
            'factor': round(r.close, 4) if r.close else None,
            'time': r.time or '',
            'num': r.num or 1,
        } for r in records],
        'total': len(records),
    })


@bp.route('/stock/<symbol>/netvalue')
def netvalue_history(symbol):
    """Net value history page (通用: XOP/USCNY/基金净值)."""
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import NetValueHistory

    db = _get_db_session()
    if not db:
        return render_template('netvalue_history.html', data={'symbol': symbol, 'title': '', 'records': [], 'total': 0})

    sym = StockSymbol(symbol)
    normalized = sym.normalized

    stock = db.query(Stock).filter(Stock.symbol.in_([symbol, normalized, sym.get_digit_a()])).first()
    if not stock:
        return render_template('netvalue_history.html', data={'symbol': symbol, 'title': symbol, 'records': [], 'total': 0})

    records = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock.id
    ).order_by(NetValueHistory.date.desc()).limit(500).all()

    title_map = {
        'XOP': 'XOP (SPDR S&P Oil & Gas Exploration & Production ETF) 收盘价',
        'USCNY': '美元人民币汇率中间价 (USD/CNY)',
    }
    title = title_map.get(stock.symbol, f'{stock.name or stock.symbol} 净值记录')

    precision = sym.get_precision()

    history = []
    rows = []
    for r in records:
        date_str = r.date.strftime('%Y-%m-%d')
        close_val = round(r.close, precision) if r.close else None
        history.append({
            'date': date_str,
            'close': close_val,
        })
        rows.append({
            'cells': [
                {'value': date_str},
                {'value': f'{close_val:.{precision}f}' if close_val is not None else '-', 'align': 'right'},
            ],
        })

    return render_template('netvalue_history.html', data={
        'symbol': symbol,
        'title': title,
        'name': stock.name or symbol,
        'records': history,
        'rows': rows,
        'total': len(history),
        'precision': precision,
    })


@bp.route('/api/stock/<symbol>/netvalue')
def api_netvalue(symbol):
    """Get net value history as JSON."""
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import NetValueHistory

    db = _get_db_session()
    if not db:
        return jsonify({'error': 'Database unavailable'})

    sym = StockSymbol(symbol)
    normalized = sym.normalized

    stock = db.query(Stock).filter(Stock.symbol.in_([symbol, normalized, sym.get_digit_a()])).first()
    if not stock:
        return jsonify({'symbol': symbol, 'records': [], 'total': 0})

    records = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock.id
    ).order_by(NetValueHistory.date.desc()).limit(500).all()

    precision = sym.get_precision()

    return jsonify({
        'symbol': symbol,
        'name': stock.name or symbol,
        'precision': precision,
        'records': [{
            'date': r.date.strftime('%Y-%m-%d'),
            'close': round(r.close, precision) if r.close else None,
        } for r in records],
        'total': len(records),
    })


@bp.route('/stock/<symbol>/premium')
def premium_history(symbol):
    """Premium history page (基金溢价记录).

    PHP对应: fundhistoryparagraph.php (EchoFundHistoryParagraph)
      _echoHistoryTableData() → _echoFundHistoryTableItem()

    表格列: 日期 | 价格(dailystock.close) | 净值(netvalue.close) | 溢价(价格/净值-1)
           | 官方EST(fundest.close) | 误差(EST/净值-1) | XOP净值

    日期对齐逻辑 (PHP: UseSameDayNetValue + GetDatePrev):
      QDII基金(in_arrayQdii): 用前一交易日的净值匹配当日交易价
      非QDII: 同日净值
    """
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import StockHistory, NetValueHistory, FundEst

    db = _get_db_session()
    if not db:
        return render_template('premium_history.html', data={'symbol': symbol, 'rows': [], 'total': 0})

    sym = StockSymbol(symbol)
    stock = db.query(Stock).filter(
        Stock.symbol.in_([symbol, sym.normalized, sym.get_digit_a()])
    ).first()
    if not stock:
        return render_template('premium_history.html', data={
            'symbol': symbol, 'name': symbol, 'rows': [], 'total': 0,
        })

    # PHP: $bSameDay = UseSameDayNetValue($ref);
    #   QDII → false (用前一日净值), 其他 → true (同日)
    is_qdii = _is_qdii(symbol)

    # PHP: $his_sql->GetAll() — 获取所有交易记录
    his_records = db.query(StockHistory).filter(
        StockHistory.stock_id == stock.id
    ).order_by(StockHistory.date.desc()).limit(500).all()

    # PHP: 构建 prev_date 映射 (GetDatePrev 逻辑)
    #   GetDatePrev: SELECT * FROM dailystock WHERE stock_id=? AND date < ? ORDER BY date DESC LIMIT 1
    all_his_dates = sorted([r.date for r in his_records])
    prev_date_map = {}
    for i, dt in enumerate(all_his_dates):
        if i > 0:
            prev_date_map[dt] = all_his_dates[i - 1]

    # PHP: $net_sql — 净值数据
    nav_records = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock.id
    ).all()
    nav_map = {r.date: r.close for r in nav_records}

    # PHP: $fund_est_sql — 官方EST
    est_records = db.query(FundEst).filter(
        FundEst.stock_id == stock.id
    ).all()
    est_map = {r.date: r.close for r in est_records}

    # PHP: 官方EST计算需要的数据源
    #   FundPairReference::GetOfficialNetValue()
    #     pair_ref->GetNetValue(date) → XOP的netvaluehistory(Yahoo收盘价)
    #     cny_ref->GetVal(date)      → USCNY的netvaluehistory(汇率)
    #   EstFromPair(xop_close, cny):
    #     A股: QdiiGetVal = xop_close * cny / factor
    #   存入fundest表，后续从fundest读
    from app.models.market_data import CalibrationHistory, FundPosition, XopNavSsga

    # PHP: XOP收盘价(计算EST用) — 来自netvaluehistory表（Yahoo数据，与校准因子同源）
    xop_stock = db.query(Stock).filter(Stock.symbol == 'XOP').first()
    xop_yahoo_map = {}
    if xop_stock:
        xop_records = db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == xop_stock.id
        ).all()
        xop_yahoo_map = {r.date: r.close for r in xop_records}

    # PHP: XOP净值(展示用) — 来自SSGA官方NAV
    ssga_records = db.query(XopNavSsga).all()
    xop_ssga_map = {r.date: r.close for r in ssga_records}

    # PHP: $this->cny_ref → USCNY netvalue表
    cny_stock = db.query(Stock).filter(Stock.symbol == 'USCNY').first()
    cny_map = {}
    if cny_stock:
        cny_records = db.query(NetValueHistory).filter(
            NetValueHistory.stock_id == cny_stock.id
        ).all()
        cny_map = {r.date: r.close for r in cny_records}

    # PHP: $this->fFactor → calibrationhistory 最新一条 (GetRecordNow)
    cal_record = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock.id
    ).order_by(CalibrationHistory.date.desc()).first()
    factor_val = cal_record.close if cal_record else None

    # PHP: $this->fLastCalibrationVal → lastcalibration表（校准时的价格）
    cal_base_val = None
    if cal_record:
        from app.models.market_data import LastCalibration
        try:
            last_cal = db.query(LastCalibration).get(stock.id)
            cal_base_val = last_cal.close if last_cal else None
        except Exception:
            pass

    # PHP: $this->GetPosition() → fundposition 表
    try:
        pos_record = db.query(FundPosition).get(stock.id)
        position = pos_record.close if pos_record else 1.0
    except Exception:
        position = 1.0

    rows = []
    for r in his_records:
        his_date = r.date
        date_str = his_date.strftime('%Y-%m-%d') if his_date else ''

        # PHP: $strDate = $bSameDay ? $arHistory['date'] : $his_sql->GetDatePrev(...)
        if is_qdii:
            nav_date = prev_date_map.get(his_date)
        else:
            nav_date = his_date

        nav_val = nav_map.get(nav_date) if nav_date else None

        # PHP: GetPercentageDisplay($fNetValue, $fClose) → 溢价 = (价格/净值-1)%
        premium_val = None
        if nav_val and r.close and nav_val != 0:
            premium_val = (r.close / nav_val - 1.0) * 100.0

        # PHP: 官方EST — 与作者一致
        #   PHP: $arFundEst = $fund_est_sql->GetRecord($strStockId, $strDate)
        #   ★ 关键：用 nav_date (不是 his_date) 查 fundest 表
        est_val = est_map.get(nav_date) if est_map and nav_date in est_map else None

        if est_val is None:
            # PHP: EstFromPair($pair_ref->GetNetValue($strOfficialDate), $fCny)
            #   XOP/CNY 也用 nav_date 对应的日期
            xop_for_est = xop_yahoo_map.get(nav_date)
            cny_for_est = cny_map.get(nav_date)

            computed_est = None
            if xop_for_est is not None and cny_for_est is not None and factor_val is not None and abs(factor_val) > 1e-8:
                from app.services.qdiiref import qdii_get_val
                if sym.is_symbol_a():
                    raw_est = qdii_get_val(float(xop_for_est), float(cny_for_est), float(factor_val))
                else:
                    if abs(float(cny_for_est)) > 1e-8:
                        raw_est = (float(xop_for_est) / float(cny_for_est)) / float(factor_val)
                    else:
                        raw_est = None
                if raw_est is not None:
                    from app.services.fundref import fund_adjust_position
                    base = float(cal_base_val) if cal_base_val is not None else raw_est
                    computed_est = fund_adjust_position(position, raw_est, base)
            est_val = computed_est

        # PHP: GetPercentageDisplay($fNetValue, $fEstValue)
        #   StockGetPercentage(fDivisor, fDividend) = (fDividend/fDivisor - 1)*100
        #   调用: GetPercentageDisplay(净值, EST) = (EST/净值-1)%
        error_val = None
        if nav_val and est_val and nav_val != 0:
            error_val = (est_val / nav_val - 1.0) * 100.0

        # PHP: est_ref->GetNetValue() → XOP净值（展示用，SSGA官方NAV）
        xop_val = xop_ssga_map.get(nav_date)

        cells = [
            {'value': date_str},
            {'value': f'{r.close:.3f}' if r.close is not None else '-', 'align': 'right'},
            {'value': f'{nav_val:.4f}' if nav_val is not None else '-', 'align': 'right'},
        ]
        if premium_val is not None:
            cells.append({'value': f'{premium_val:+.2f}%', 'align': 'right'})
        else:
            cells.append({'value': '-', 'align': 'right'})

        cells.append({'value': f'{est_val:.4f}' if est_val is not None else '-', 'align': 'right'})
        if error_val is not None:
            cells.append({'value': f'{error_val:+.2f}%', 'align': 'right'})
        else:
            cells.append({'value': '-', 'align': 'right'})
        cells.append({'value': f'{xop_val:.4f}' if xop_val is not None else '-', 'align': 'right'})

        rows.append({'cells': cells})

    title = f'{stock.name or stock.symbol} 历史价格相对于净值的溢价'

    return render_template('premium_history.html', data={
        'symbol': symbol,
        'title': title,
        'name': stock.name or symbol,
        'rows': rows,
        'total': len(rows),
    })


@bp.route('/api/stock/<symbol>/premium')
def api_premium(symbol):
    """Get premium history as JSON."""
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import NetValueHistory, CalibrationHistory

    db = _get_db_session()
    if not db:
        return jsonify({'error': 'Database unavailable'})

    sym = StockSymbol(symbol)
    stock = db.query(Stock).filter(
        Stock.symbol.in_([symbol, sym.normalized, sym.get_digit_a()])
    ).first()
    if not stock:
        return jsonify({'symbol': symbol, 'records': [], 'total': 0})

    xop_stock = db.query(Stock).filter(Stock.symbol == 'XOP').first()
    cny_stock = db.query(Stock).filter(Stock.symbol == 'USCNY').first()
    if not xop_stock or not cny_stock:
        return jsonify({'symbol': symbol, 'records': [], 'total': 0, 'error': 'Missing XOP or USCNY data'})

    latest_nav = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock.id
    ).order_by(NetValueHistory.date.desc()).first()

    latest_xop = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == xop_stock.id
    ).order_by(NetValueHistory.date.desc()).first()

    latest_cny = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == cny_stock.id
    ).order_by(NetValueHistory.date.desc()).first()

    latest_cal = db.query(CalibrationHistory).filter(
        CalibrationHistory.stock_id == stock.id
    ).order_by(CalibrationHistory.date.desc()).first()

    realtime = {}
    if all([latest_nav, latest_xop, latest_cny, latest_cal]):
        nav_val = latest_nav.close
        nav_date = latest_nav.date.strftime('%Y-%m-%d')
        xop_val = latest_xop.close
        xop_date = latest_xop.date.strftime('%Y-%m-%d')
        cny_val = latest_cny.close
        cny_date = latest_cny.date.strftime('%Y-%m-%d')
        factor_val = latest_cal.close
        cal_date = latest_cal.date.strftime('%Y-%m-%d')

        if factor_val and factor_val != 0:
            est_nav = xop_val * cny_val / factor_val
            premium_pct = (est_nav / nav_val - 1.0) * 100.0
        else:
            est_nav = premium_pct = None

        realtime = {
            'nav_date': nav_date,
            'nav': round(nav_val, 4),
            'xop_date': xop_date,
            'xop': round(xop_val, 2),
            'cny_date': cny_date,
            'cny': round(cny_val, 4),
            'cal_date': cal_date,
            'factor': round(factor_val, 4) if factor_val else None,
            'est_nav': round(est_nav, 4) if est_nav is not None else None,
            'premium': round(premium_pct, 2) if premium_pct is not None else None,
        }

    nav_subq = db.query(
        NetValueHistory.date.label('nav_date'),
        NetValueHistory.close.label('nav'),
    ).filter(NetValueHistory.stock_id == stock.id).subquery()

    xop_subq = db.query(
        NetValueHistory.date.label('xop_date'),
        NetValueHistory.close.label('xop_close'),
    ).filter(NetValueHistory.stock_id == xop_stock.id).subquery()

    cny_subq = db.query(
        NetValueHistory.date.label('cny_date'),
        NetValueHistory.close.label('cny_rate'),
    ).filter(NetValueHistory.stock_id == cny_stock.id).subquery()

    cal_subq = db.query(
        CalibrationHistory.date.label('cal_date'),
        CalibrationHistory.close.label('factor'),
    ).filter(CalibrationHistory.stock_id == stock.id).subquery()

    from sqlalchemy.orm import aliased
    rows_db = db.query(
        nav_subq.c.nav_date, nav_subq.c.nav,
        xop_subq.c.xop_close, cny_subq.c.cny_rate, cal_subq.c.factor,
    ).join(xop_subq, xop_subq.c.xop_date == nav_subq.c.nav_date)\
     .join(cny_subq, cny_subq.c.cny_date == nav_subq.c.nav_date)\
     .join(cal_subq, cal_subq.c.cal_date == nav_subq.c.nav_date)\
     .order_by(nav_subq.c.nav_date.desc()).limit(500).all()

    records = []
    for r in rows_db:
        if r.nav and r.xop_close and r.cny_rate and r.factor and r.factor != 0:
            est_nav = r.xop_close * r.cny_rate / r.factor
            premium_pct = (est_nav / r.nav - 1.0) * 100.0
        else:
            est_nav = premium_pct = None

        records.append({
            'date': r.nav_date.strftime('%Y-%m-%d') if r.nav_date else '',
            'nav': round(r.nav, 4) if r.nav else None,
            'est_nav': round(est_nav, 4) if est_nav is not None else None,
            'premium': round(premium_pct, 2) if premium_pct is not None else None,
            'xop_close': round(r.xop_close, 2) if r.xop_close else None,
            'cny_rate': round(r.cny_rate, 4) if r.cny_rate else None,
            'factor': round(r.factor, 4) if r.factor else None,
        })

    return jsonify({
        'symbol': symbol,
        'name': stock.name or symbol,
        'realtime': realtime,
        'records': records,
        'total': len(records),
    })


@bp.route('/stock/<symbol>/data')
def stock_data(symbol):
    """Stock historical data page (交易数据 + 净值数据).

    展示 dailystock (交易行情) 和 netvalue (基金净值) 两张表的历史记录.
    """
    from app.services.stocksymbol import StockSymbol
    from app.models.stock import Stock
    from app.models.market_data import StockHistory, NetValueHistory

    db = _get_db_session()
    if not db:
        return render_template('stock_data.html', data={'symbol': symbol, 'trading': [], 'nav': [], 'total_trading': 0, 'total_nav': 0})

    sym = StockSymbol(symbol)
    stock = db.query(Stock).filter(
        Stock.symbol.in_([symbol, sym.normalized, sym.get_digit_a()])
    ).first()
    if not stock:
        return render_template('stock_data.html', data={
            'symbol': symbol, 'name': symbol,
            'trading': [], 'nav': [], 'total_trading': 0, 'total_nav': 0,
        })

    trading_records = db.query(StockHistory).filter(
        StockHistory.stock_id == stock.id
    ).order_by(StockHistory.date.desc()).limit(500).all()

    nav_records = db.query(NetValueHistory).filter(
        NetValueHistory.stock_id == stock.id
    ).order_by(NetValueHistory.date.desc()).limit(500).all()

    trading_rows = []
    for r in trading_records:
        date_str = r.date.strftime('%Y-%m-%d') if r.date else ''
        trading_rows.append({
            'cells': [
                {'value': date_str},
                {'value': f'{r.open:.3f}' if r.open is not None else '-', 'align': 'right'},
                {'value': f'{r.high:.3f}' if r.high is not None else '-', 'align': 'right'},
                {'value': f'{r.low:.3f}' if r.low is not None else '-', 'align': 'right'},
                {'value': f'{r.close:.3f}' if r.close is not None else '-', 'align': 'right'},
                {'value': f'{r.volume:,}' if r.volume else '-', 'align': 'right'},
            ],
        })

    nav_rows = []
    for r in nav_records:
        date_str = r.date.strftime('%Y-%m-%d') if r.date else ''
        nav_rows.append({
            'cells': [
                {'value': date_str},
                {'value': f'{r.close:.4f}' if r.close is not None else '-', 'align': 'right'},
            ],
        })

    return render_template('stock_data.html', data={
        'symbol': symbol,
        'name': stock.name or symbol,
        'trading': trading_rows,
        'nav': nav_rows,
        'total_trading': len(trading_rows),
        'total_nav': len(nav_rows),
    })


@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@bp.route('/bot/telegram', methods=['POST'])
def telegram_webhook():
    """Telegram bot webhook endpoint."""
    try:
        data = request.get_json()
        bot = TelegramStock(TELEGRAM_TOKEN)
        result = bot.run(data)

        if result:
            return jsonify(result)
        return Response(status=200)
    except Exception:
        return Response(status=500)


@bp.route('/bot/weixin', methods=['GET', 'POST'])
def weixin_webhook():
    """WeChat bot webhook endpoint."""
    try:
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')

        bot = WeixinStock(WECHAT_TOKEN)

        if request.method == 'GET':
            result = bot.run(signature, timestamp, nonce, echostr=echostr)
            return result
        else:
            body = request.get_data(as_text=True)
            result = bot.run(signature, timestamp, nonce, body=body)
            return Response(result, content_type='application/xml')
    except Exception:
        return Response(status=500)
