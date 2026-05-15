"""Stock history and technical analysis.

Translated from PHP stockhis.php.
Provides SMA, EMA, Bollinger Bands calculations and historical data analysis.
"""

import math
from typing import List, Dict, Optional, Tuple

from app.utils.date_utils import StringYMD, GetNowYMD


MAX_QUOTES_DAYS = 620
BOLL_DAYS = 20
SMA_SECTION = 'SMA'


def _ignore_current_trading_data(date_str: str) -> bool:
    """Check if current trading data should be ignored."""
    now_ymd = GetNowYMD()
    if now_ymd.get_ymd() == date_str:
        if not now_ymd.is_stock_trading_hour_end():
            return True
    return False


def _est_sma(values: List[float], period: int) -> str:
    """Estimate SMA value."""
    num = period - 1
    total = 0.0
    count = 0
    
    for val in values:
        total += val
        count += 1
        if count == num:
            break
    
    return str(total / num)


def get_quadratic_equation_root(a: float, b: float, c: float) -> Optional[Tuple[float, float]]:
    """Solve quadratic equation ax^2 + bx + c = 0."""
    delta = b * b - 4.0 * a * c
    if delta >= 0.0:
        x1 = (-b + math.sqrt(delta)) / (2.0 * a)
        x2 = (-b - math.sqrt(delta)) / (2.0 * a)
        return (x1, x2)
    return None


def _est_bollinger_bands(values: List[float], period: int) -> Optional[Tuple[str, str]]:
    """Estimate Bollinger Bands."""
    f_sum = 0.0
    f_quadratic_sum = 0.0
    i_num = period - 1
    i_count = 0
    
    for f_val in values:
        f_sum += f_val
        f_quadratic_sum += f_val * f_val
        i_count += 1
        if i_count == i_num:
            break
    
    f = 1.0 * (period - 4)
    a = f * i_num * i_num - 4 * i_num
    b = (8 - 2 * f * i_num) * f_sum
    c = f * f_sum * f_sum - 4 * f_quadratic_sum
    
    if roots := get_quadratic_equation_root(a, b, c):
        x1, x2 = roots
        sigma1 = (f_sum - i_num * x1) / 2
        sigma2 = (f_sum - i_num * x2) / 2
        return (str(x1 - 2 * sigma1), str(x2 - 2 * sigma2))
    return None


def _est_next_bollinger_bands(values: List[float], period: int) -> Optional[Tuple[str, str]]:
    """Estimate next day Bollinger Bands."""
    f_sum = 0.0
    f_quadratic_sum = 0.0
    i_num = period - 2
    i_count = 0
    
    for f_val in values:
        f_sum += f_val
        f_quadratic_sum += f_val * f_val
        i_count += 1
        if i_count == i_num:
            break
    
    f = 1.0 * (period - 8)
    a = f * i_num * i_num - 16 * i_num
    b = (32 - 2 * f * i_num) * f_sum
    c = f * f_sum * f_sum - 16 * f_quadratic_sum
    
    if roots := get_quadratic_equation_root(a, b, c):
        x1, x2 = roots
        sigma1 = (f_sum - i_num * x1) / 4
        sigma2 = (f_sum - i_num * x2) / 4
        return (str(x1 - 2 * sigma1), str(x2 - 2 * sigma2))
    return None


def _is_week_end(str_ymd: str, str_next_day_ymd: str = None) -> bool:
    """Check if date is week end."""
    ymd = StringYMD(str_ymd)
    
    if str_next_day_ymd:
        next_ymd = StringYMD(str_next_day_ymd)
        if ymd.get_day_of_week() >= next_ymd.get_day_of_week():
            return True
    else:
        if ymd.is_friday():
            return True
        
        now_ymd = GetNowYMD()
        if now_ymd.is_week_day():
            if ymd.get_day_of_week() > now_ymd.get_day_of_week():
                return True
        else:
            return True
    
    return False


def _is_month_end(str_ymd: str, str_next_day_ymd: str = None) -> bool:
    """Check if date is month end."""
    ymd = StringYMD(str_ymd)
    
    if str_next_day_ymd:
        next_ymd = StringYMD(str_next_day_ymd)
    else:
        now_ymd = GetNowYMD()
        if now_ymd.get_ymd() == str_ymd or now_ymd.is_weekend():
            i_tick = now_ymd.get_next_trading_day_tick()
            next_ymd = StringYMD.from_tick(i_tick)
        else:
            next_ymd = now_ymd
    
    return ymd.get_month() != next_ymd.get_month()


class MaxMin:
    """Track max and min values."""
    
    def __init__(self):
        self._max = None
        self._min = None
    
    @property
    def max(self):
        return self._max
    
    @property
    def min(self):
        return self._min
    
    def init(self, f_max: float, f_min: float):
        """Initialize max and min if not already set."""
        if self._min is None and self._max is None:
            self._min = f_min
            self._max = f_max
    
    def set(self, f_val: float):
        """Update max and min with new value."""
        if self._max is None or f_val > self._max:
            self._max = f_val
        if self._min is None or f_val < self._min:
            self._min = f_val
    
    def fit(self, f_val: float) -> bool:
        """Check if value is within min and max."""
        if self._min is not None and self._max is not None:
            return self._min < f_val < self._max
        return False


class StockHistory:
    """Stock history analysis class."""
    
    def __init__(self, ref, after_hour: bool = False):
        self._stock_ref = ref
        self._periods = [5, 10, 20]
        self._sma = {}
        self._next = {}
        self._after_hour = {}
        self._color = {}
        self._order = []
        self._start_date = None
        
        ref.set_time_zone()
        self._start_date = self._calc_start_date()
        self._config_sma()
        
        if after_hour and self.need_after_hour_est():
            self._on_test()
            self._get_color_and_order_array(self._next)
        else:
            self._get_color_and_order_array(self._sma)
    
    @property
    def start_date(self):
        return self._start_date
    
    def get_start_date(self) -> Optional[str]:
        """Get start date."""
        return self._start_date
    
    def _build_next_name(self, name: str) -> str:
        """Build next SMA name."""
        return name + 'Next'
    
    def _cfg_set_sma(self, cfg, name: str, sma: str, next_val: str = None):
        """Set SMA value in config."""
        self._sma[name] = sma
        self._next[name] = next_val
        
        cfg.set_var(SMA_SECTION, name, sma)
        if next_val:
            cfg.set_var(SMA_SECTION, self._build_next_name(name), next_val)
    
    def _cfg_get_sma(self, cfg, name: str):
        """Get SMA value from config."""
        self._sma[name] = cfg.read_var(SMA_SECTION, name)
        
        if val := cfg.read_var(SMA_SECTION, self._build_next_name(name)):
            self._next[name] = val
        else:
            self._next[name] = None
    
    def _get_ema(self, days: int):
        """Get EMA value."""
        name = f'EMA{days}'
        self._sma[name] = None
        self._next[name] = None
        self._after_hour[name] = None
    
    def _cfg_set_smas(self, cfg, prefix: str, close_values: List[float]):
        """Set multiple SMA values."""
        for period in self._periods:
            self._cfg_set_sma(cfg, f'{prefix}{period}', 
                              _est_sma(close_values, period),
                              _est_sma(close_values, period - 1))
        
        if bands := _est_bollinger_bands(close_values, BOLL_DAYS):
            str_up, str_down = bands
            next_bands = _est_next_bollinger_bands(close_values, BOLL_DAYS)
            if next_bands:
                str_up_next, str_down_next = next_bands
            else:
                str_up_next = str_down_next = None
            
            self._cfg_set_sma(cfg, f'{prefix}BOLLUP', str_up, str_up_next)
            self._cfg_set_sma(cfg, f'{prefix}BOLLDN', str_down, str_down_next)
    
    def _cfg_get_smas(self, cfg, prefix: str):
        """Get multiple SMA values."""
        for period in self._periods:
            self._cfg_get_sma(cfg, f'{prefix}{period}')
        self._cfg_get_sma(cfg, f'{prefix}BOLLUP')
        self._cfg_get_sma(cfg, f'{prefix}BOLLDN')
    
    def _load_config_sma(self, cfg):
        """Load SMA config."""
        self._cfg_get_smas(cfg, 'D')
        self._cfg_get_smas(cfg, 'W')
        self._cfg_get_smas(cfg, 'M')
    
    def _get_day_week_month_data(self):
        """Get daily, weekly, and monthly close data."""
        close = []
        weekly_close = []
        monthly_close = []
        str_next_day_ymd = None
        
        return close, weekly_close, monthly_close
    
    def _save_config_sma(self, cfg):
        """Save SMA config."""
        close, weekly_close, monthly_close = self._get_day_week_month_data()
        
        self._cfg_set_smas(cfg, 'D', close)
        self._cfg_set_smas(cfg, 'W', weekly_close)
        self._cfg_set_smas(cfg, 'M', monthly_close)
        
        cfg.save_data()
    
    def _config_sma(self):
        """Configure SMA values."""
        from app.utils.config_file import INIFile
        
        cfg = INIFile(self._stock_ref.config_name)
        str_cur_date = self._start_date
        
        if cfg.group_exists(SMA_SECTION):
            str_date = cfg.read_var(SMA_SECTION, 'Date')
            if str_date == str_cur_date:
                self._load_config_sma(cfg)
            else:
                cfg.set_group(SMA_SECTION)
                cfg.set_var(SMA_SECTION, 'Date', str_cur_date)
                self._save_config_sma(cfg)
        else:
            cfg.add_group(SMA_SECTION)
            cfg.set_var(SMA_SECTION, 'Date', str_cur_date)
            self._save_config_sma(cfg)
        
        self._get_ema(50)
        self._get_ema(200)
    
    def _on_test_data(self, prefix: str, close_values: List[float]):
        """Process test data."""
        for period in self._periods:
            self._after_hour[f'{prefix}{period}'] = _est_sma(close_values, period)
        
        if bands := _est_bollinger_bands(close_values, BOLL_DAYS):
            str_up, str_down = bands
            self._after_hour[f'{prefix}BOLLUP'] = str_up
            self._after_hour[f'{prefix}BOLLDN'] = str_down
    
    def _on_test(self):
        """Run test analysis."""
        f_price = float(self._stock_ref.price) if self._stock_ref.price else 0.0
        close = [f_price]
        weekly_close = [f_price]
        monthly_close = [f_price]
        
        day_close, week_close, month_close = self._get_day_week_month_data()
        close.extend(day_close)
        weekly_close.extend(week_close)
        monthly_close.extend(month_close)
        
        self._on_test_data('D', close)
        self._on_test_data('W', weekly_close)
        self._on_test_data('M', monthly_close)
    
    def get_ref(self):
        """Get stock reference."""
        return self._stock_ref
    
    def get_stock_id(self) -> str:
        """Get stock ID."""
        return self._stock_ref.get_stock_id()
    
    def _calc_start_date(self) -> Optional[str]:
        """Calculate start date."""
        return None
    
    def get_bull_bear(self) -> Optional[str]:
        """Get bull/bear market indicator."""
        if 'EMA50' in self._sma and 'EMA200' in self._sma:
            if float(self._sma['EMA50']) > float(self._sma['EMA200']):
                return '<font color="red">牛市</font>'
            else:
                return '<font color="green">熊市</font>'
        return None
    
    def need_after_hour_est(self) -> bool:
        """Check if after-hour estimation is needed."""
        ref = self.get_ref()
        if self.get_start_date() == ref.get_date():
            return False
        
        ref.set_time_zone()
        now_ymd = GetNowYMD()
        return now_ymd.get_hour_minute() > 1520
    
    def _get_color_and_order_array(self, sma_data: Dict[str, str]):
        """Get color and order arrays."""
        mm = MaxMin()
        mm_w = MaxMin()
        ar_val = []
        
        for key, str_val in sma_data.items():
            f_val = float(str_val)
            str_color = None
            first_char = key[0] if key else ''
            
            if first_char == 'D':
                mm.init(0.0, 10000000.0)
                mm.set(f_val)
                ar_val.append(f_val)
            elif first_char == 'W':
                mm_w.init(mm.max, mm.min)
                mm_w.set(f_val)
                if mm.fit(f_val):
                    str_color = 'silver'
                else:
                    ar_val.append(f_val)
            elif first_char == 'M':
                if mm.fit(f_val):
                    str_color = 'silver'
                elif mm_w.fit(f_val):
                    str_color = 'gray'
                else:
                    ar_val.append(f_val)
            else:
                if mm.fit(f_val):
                    str_color = 'silver'
                else:
                    str_color = 'yellow'
            
            self._color[key] = str_color
        
        ar_val.sort()
        self._order = list({f'{v:.2f}' for v in ar_val})
    
    def get_sma(self) -> Dict[str, str]:
        """Get SMA data."""
        return self._sma
    
    def get_order_array(self) -> List[str]:
        """Get ordered values array."""
        return self._order
    
    def get_color(self, key: str) -> Optional[str]:
        """Get color for a key."""
        return self._color.get(key)