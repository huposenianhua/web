"""Stock text display module.

Translated from PHP ui/stocktext.php.
Provides text formatting for stock data display.
"""

BOT_EOL = '\n'

STOCK_DISP_PRICE = '价格'
STOCK_DISP_QUANTITY = '量'
STOCK_DISP_CHANGE = '涨跌'
STOCK_DISP_OPEN = '开盘'
STOCK_DISP_HIGH = '最高'
STOCK_DISP_LOW = '最低'
STOCK_DISP_SYMBOL = '代码'
STOCK_DISP_RATIO = '比价'
STOCK_DISP_PREMIUM = '溢价'
STOCK_DISP_EST = '估算'
STOCK_DISP_OFFICIAL = '官方'
STOCK_DISP_FAIR = '合理'
STOCK_DISP_REALTIME = '实时'
STOCK_DISP_NETVALUE = '净值'


def _text_price_volume(ref) -> str:
    """Format price and volume text."""
    text = f":{ref.price} {ref.date} {ref.time_hm}{BOT_EOL}"
    
    volume = ref.volume
    if volume and int(volume) > 0:
        text += f"成交{STOCK_DISP_QUANTITY}:{volume}股{BOT_EOL}"
    
    return text


def text_from_extended_trading_reference(ref) -> str:
    """Format extended trading reference text."""
    return f"{ref.get_market_session()}{_text_price_volume(ref)}"


def text_from_stock_reference(ref) -> str:
    """Format stock reference as text."""
    if not ref.has_data():
        return None
    
    symbol = ref.symbol
    name = symbol
    
    lines = [name, BOT_EOL]
    lines.append(symbol)
    lines.append(BOT_EOL)
    lines.append(f"{STOCK_DISP_PRICE}{_text_price_volume(ref)}")
    lines.append(f"{STOCK_DISP_CHANGE}:{ref.get_percentage_text()}{BOT_EOL}")
    
    if ref.open:
        lines.append(f"{STOCK_DISP_OPEN}:{ref.open}{BOT_EOL}")
    if ref.high:
        lines.append(f"{STOCK_DISP_HIGH}:{ref.high}{BOT_EOL}")
    if ref.low:
        lines.append(f"{STOCK_DISP_LOW}:{ref.low}{BOT_EOL}")
    
    if hasattr(ref, 'extended_ref') and ref.extended_ref:
        lines.append(text_from_extended_trading_reference(ref.extended_ref))
    
    return ''.join(lines)


def text_pair_ratio(ref, name: str, pair_name: str, ratio: str) -> str:
    """Format pair ratio text."""
    text = ''
    if ref:
        text += f"{BOT_EOL}{name}{STOCK_DISP_SYMBOL}:{ref.get_symbol()}"
        pair_ref = ref.get_pair_ref()
        text += f"{BOT_EOL}{pair_name}{STOCK_DISP_SYMBOL}:{pair_ref.get_symbol()}"
        text += f"{BOT_EOL}{ratio}{STOCK_DISP_RATIO}:{ref.get_price_ratio()}{BOT_EOL}"
    return text


def _text_premium(ref, estimate: float) -> str:
    """Format premium text."""
    if ref.has_data():
        return f"{STOCK_DISP_PREMIUM}:{ref.get_percentage_text(estimate)}"
    return ''


def _text_est_premium(ref, estimate: float) -> str:
    """Format estimated premium text."""
    text = f"{STOCK_DISP_EST}:{estimate:.{ref.get_precision()}f}"
    text += f" {_text_premium(ref, estimate)}"
    return text


def _text_est_net_value(fund, ref) -> str:
    """Format estimated net value text."""
    text = ''
    
    if net_value := fund.get_official_net_value():
        text += f"{STOCK_DISP_OFFICIAL}{_text_est_premium(ref, net_value)} {fund.get_official_date()}{BOT_EOL}"
    
    if net_value := fund.get_fair_net_value():
        text += f"{STOCK_DISP_FAIR}{_text_est_premium(ref, net_value)}{BOT_EOL}"
    
    if net_value := fund.get_realtime_net_value():
        text += f"{STOCK_DISP_REALTIME}{_text_est_premium(ref, net_value)}{BOT_EOL}"
    
    return text


def text_from_fund_reference(ref) -> str:
    """Format fund reference as text."""
    if not ref.has_data():
        return None
    
    symbol = ref.symbol
    name = f"{symbol}{BOT_EOL}{symbol}{BOT_EOL}"
    
    if hasattr(ref, 'get_stock_ref'):
        stock_ref = ref.get_stock_ref()
        net_value = ref.get_price()
        date = ref.get_date()
        percentage = ref.get_percentage_text()
    else:
        stock_ref = ref
        netvalue_ref = ref.get_net_value_ref()
        net_value = netvalue_ref.get_price()
        date = netvalue_ref.get_date()
        percentage = netvalue_ref.get_percentage_text()
    
    if stock_ref:
        text = text_from_stock_reference(stock_ref)
        if not text:
            text = name
    else:
        text = name
    
    text += f"{STOCK_DISP_NETVALUE}:{net_value} {date}{BOT_EOL}"
    text += f"{STOCK_DISP_NETVALUE}{STOCK_DISP_CHANGE}:{percentage}{BOT_EOL}"
    
    if stock_ref:
        if stock_ref.get_date() == date:
            text += f"{_text_premium(stock_ref, float(net_value))}{BOT_EOL}"
        text += _text_est_net_value(ref, stock_ref)
    
    return text