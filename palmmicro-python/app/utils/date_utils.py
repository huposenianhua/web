"""Date/time utilities with trading calendar logic.

Translated from PHP class/year_month_day.php.
Provides YMD class hierarchy for trading day calculation, timezone handling,
display formatting, and file cache expiry checking.

Class hierarchy:
    YearMonthDay          (base: tick → YMD, weekday checks, file freshness)
    +-- StringYMD        (construct from 'YYYY-MM-DD' string)
    |   +-- OldestYMD    (fixed date 2014-01-01, validation helpers)
    +-- TickYMD          (adds hour/minute access, trading hour check)
    |   +-- NowYMD       (current time in PRC timezone)
"""

import os
import time as _time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.logger import (
    SECONDS_IN_DAY,
    SECONDS_IN_MIN,
    debug_get_date,
    debug_get_time,
    debug_string,
    _PRC,
)

# ---------------------------------------------------------------------------
# Free function
# ---------------------------------------------------------------------------
def convert_ymd(s: str) -> str:
    """Convert 'YYYYMMDD' to 'YYYY-MM-DD'.

    Translated from PHP ConvertYMD().
    """
    if len(s) >= 8:
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s


# ---------------------------------------------------------------------------
# YearMonthDay — base class
# ---------------------------------------------------------------------------
class YearMonthDay:
    """Date wrapper built from a Unix timestamp, with PRC timezone.

    Translated from PHP YearMonthDay class.
    """

    def __init__(self, timestamp: float) -> None:
        self._timestamp: float = timestamp
        # Store timezone-aware datetime in PRC
        self._dt: datetime = datetime.fromtimestamp(timestamp, tz=_PRC)

    # -- PHP localtime() compatible day-of-week: Sun=0, Mon=1, ..., Sat=6 --
    @property
    def _php_wday(self) -> int:
        """PHP-compatible day of week (Sunday=0 .. Saturday=6)."""
        # Python: Monday=0, Sunday=6 → PHP: Sunday=0, Monday=1, ..., Saturday=6
        return (self._dt.weekday() + 1) % 7

    # -- Getters --
    def get_ymd(self) -> str:
        """Return 'YYYY-MM-DD' string (no timezone conversion)."""
        return debug_get_date(self._timestamp, tz=None)

    def get_display(self, chinese: bool = True) -> str:
        """Return formatted date for display.

        Chinese: 'Y年n月j日', English: 'M j, Y'.
        """
        if chinese:
            return self._dt.strftime("%Y年%-m月%-d日")
        return self._dt.strftime("%b %d, %Y")

    def get_month_day_display(self, chinese: bool = True) -> str:
        """Return month-day display.

        Chinese: 'n月j日', English: 'M j'.
        """
        if chinese:
            return self._dt.strftime("%-m月%-d日")
        return self._dt.strftime("%b %d")

    def get_tick(self) -> float:
        """Return Unix timestamp."""
        return self._timestamp

    # -- Next weekday / trading day --
    def get_next_weekday_tick(self) -> float:
        """Return timestamp of the next weekday (skip weekends).

        Translated from PHP GetNextWeekDayTick().
        """
        if self.is_friday():
            seconds = 3 * SECONDS_IN_DAY
        elif self.is_saturday():
            seconds = 2 * SECONDS_IN_DAY
        else:
            seconds = SECONDS_IN_DAY
        return self._timestamp + seconds

    def get_next_trading_day_tick(self) -> float:
        """Return timestamp of the next trading day (skip weekends + holidays).

        Translated from PHP GetNextTradingDayTick().
        Recursively skips holidays.
        """
        tick = self.get_next_weekday_tick()
        next_ymd = YearMonthDay(tick)
        if next_ymd.is_holiday():
            return next_ymd.get_next_trading_day_tick()
        return tick

    # -- File cache freshness --
    def need_file(self, filename: str, interval: int = SECONDS_IN_MIN) -> float | bool:
        """Check if a cached file needs refresh.

        Translated from PHP NeedFile().

        Returns:
            File's mtime if file needs updating, False if still fresh.
        """
        try:
            mtime = os.path.getmtime(filename)
        except OSError:
            mtime = 1  # File does not exist

        if self._timestamp < (mtime + interval):
            return False  # Still fresh
        return mtime  # Needs update

    # -- Time checks --
    def is_future(self) -> bool:
        """Check if this date is in the future.

        Translated from PHP IsFuture().
        """
        return self._timestamp > _time.time()

    # -- Day-of-week checks --
    def is_monday(self) -> bool:
        """Translated from PHP IsMonday()."""
        return self._php_wday == 1

    def is_friday(self) -> bool:
        """Translated from PHP IsFriday()."""
        return self._php_wday == 5

    def is_saturday(self) -> bool:
        """Translated from PHP IsSaturday()."""
        return self._php_wday == 6

    def is_sunday(self) -> bool:
        """Translated from PHP IsSunday()."""
        return self._php_wday == 0

    def is_weekday(self) -> bool:
        """Translated from PHP IsWeekDay()."""
        return not (self.is_saturday() or self.is_sunday())

    def is_weekend(self) -> bool:
        """Translated from PHP IsWeekend()."""
        return not self.is_weekday()

    def get_day_of_week(self) -> int:
        """Return PHP-compatible day of week (Sun=0 .. Sat=6).

        Translated from PHP GetDayOfWeek().
        """
        return self._php_wday

    # -- Year / month / day components --
    def get_year(self) -> int:
        """Translated from PHP GetYear()."""
        return self._dt.year

    def get_month(self) -> int:
        """Translated from PHP GetMonth()."""
        return self._dt.month

    def get_day(self) -> int:
        """Translated from PHP GetDay()."""
        return self._dt.day

    # -- Holiday check --
    def is_holiday(self) -> bool:
        """Check if this date is a holiday (New Year's Day or weekend).

        Translated from PHP IsHoliday().
        NOTE: Only checks Jan 1 and weekends.
        A full holiday calendar would need external data (Chinese exchange holidays).
        """
        if self._dt.month == 1 and self._dt.day == 1:
            return True
        if self.is_weekend():
            return True
        return False


# ---------------------------------------------------------------------------
# StringYMD — construct from 'YYYY-MM-DD' string
# ---------------------------------------------------------------------------
class StringYMD(YearMonthDay):
    """Construct a YearMonthDay from a 'YYYY-MM-DD' string.

    Translated from PHP StringYMD class.
    """

    def __init__(self, ymd_str: str) -> None:
        parts = ymd_str.split("-")
        if len(parts) != 3:
            debug_string(f"Invalid StringYMD input: {ymd_str}")
            timestamp = _time.time()
        else:
            try:
                dt = datetime(
                    int(parts[0]), int(parts[1]), int(parts[2]),
                    tzinfo=_PRC,
                )
                timestamp = dt.timestamp()
            except ValueError as exc:
                debug_string(f"Invalid StringYMD input: {ymd_str} ({exc})")
                timestamp = _time.time()
        super().__init__(timestamp)


# ---------------------------------------------------------------------------
# OldestYMD — fixed date 2014-01-01, with validation
# ---------------------------------------------------------------------------
class OldestYMD(StringYMD):
    """Represents the oldest valid date (2014-01-01).

    Translated from PHP OldestYMD class.
    """

    def __init__(self) -> None:
        super().__init__("2014-01-01")

    def is_too_old(self, ymd_str: str) -> bool:
        """Check if a date is before the oldest allowed date.

        Translated from PHP IsTooOld().
        """
        ymd = StringYMD(ymd_str)
        if ymd.get_tick() < self.get_tick():
            debug_string(f"Date too old {ymd_str}")
            return True
        return False

    def is_invalid(self, ymd_str: str) -> bool:
        """Check if a date is a weekend or in the future.

        Translated from PHP IsInvalid().
        """
        ymd = StringYMD(ymd_str)
        if ymd.is_weekend():
            debug_string(f"Weekend date {ymd_str}")
            return True
        if ymd.is_future():
            debug_string(f"Future date {ymd_str}")
            return True
        return False


# ---------------------------------------------------------------------------
# TickYMD — extends with hour/minute
# ---------------------------------------------------------------------------
class TickYMD(YearMonthDay):
    """Extends YearMonthDay with hour/minute access.

    Translated from PHP TickYMD class.
    """

    def get_hour(self) -> int:
        """Translated from PHP GetHour()."""
        return self._dt.hour

    def get_minute(self) -> int:
        """Translated from PHP GetMinute()."""
        return self._dt.minute

    def get_hour_minute(self) -> int:
        """Return hour and minute as HHMM integer (e.g., 930 for 09:30).

        Translated from PHP GetHourMinute().
        """
        return self.get_hour() * 100 + self.get_minute()

    def get_hms(self) -> str:
        """Return 'HH:MM:SS' string (no timezone conversion).

        Translated from PHP GetHMS().
        """
        return debug_get_time(self._timestamp, tz=None)

    def is_stock_trading_hour_end(self) -> bool:
        """Check if current hour is past trading hours (after 16:00).

        Translated from PHP IsStockTradingHourEnd().
        """
        return self.get_hour() > 16


# ---------------------------------------------------------------------------
# NowYMD — current time in PRC timezone
# ---------------------------------------------------------------------------
class NowYMD(TickYMD):
    """Represents the current date/time in PRC timezone.

    Translated from PHP NowYMD class.
    """

    def __init__(self) -> None:
        super().__init__(_time.time())

    def check_timezone(self) -> None:
        """Verify timezone hasn't changed unexpectedly.

        Translated from PHP CheckTimeZone().
        In Python, timezone is per-call via ZoneInfo, so this is a no-op,
        but kept for API compatibility.
        """
        pass


# ---------------------------------------------------------------------------
# Global instance and convenience functions
# ---------------------------------------------------------------------------
# Global NowYMD instance (replaces PHP global $g_now_ymd)
_g_now_ymd: NowYMD | None = None


def get_now_tick() -> float:
    """Get current Unix timestamp from the global NowYMD instance.

    Translated from PHP GetNowTick().
    """
    global _g_now_ymd
    if _g_now_ymd is None:
        _g_now_ymd = NowYMD()
    return _g_now_ymd.get_tick()


def get_now_ymd() -> NowYMD:
    """Get the global NowYMD instance, refreshing timezone check.

    Translated from PHP GetNowYMD().
    """
    global _g_now_ymd
    if _g_now_ymd is None:
        _g_now_ymd = NowYMD()
    _g_now_ymd.check_timezone()
    return _g_now_ymd


def get_next_trading_day_ymd(ymd_str: str) -> str:
    """Get the next trading day as 'YYYY-MM-DD' string.

    Translated from PHP GetNextTradingDayYMD().
    """
    ymd = StringYMD(ymd_str)
    tick = ymd.get_next_trading_day_tick()
    next_ymd = TickYMD(tick)
    return next_ymd.get_ymd()
