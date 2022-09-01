"""
mktdays.py - Contains helper functions to determine market availability.
https://www.tsx.com/trading/calendars-and-trading-hours/calendar
https://www.nyse.com/markets/hours-calendars
"""

import pandas as pd
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
from typing import Literal


def is_weekend(dt: object) -> bool:
    """Determines whether provided date is a weekend

    :param dt: datetime to check
    :return: whether datetime is a weekend
    """

    return dt.weekday() > 4


def mkt_open(mkt: Literal["tsx", "nyse"], dt: datetime = datetime.today()) -> bool:
    """Determines whether provided market is open on a specified date
    https://pypi.org/project/pandas-market-calendars/

    :param mkt: market to check if open
    :param dt: datetime to check, defaults to datetime.today()
    :return: whether market is open on specified datetime
    """

    dt_str = dt.strftime("%Y-%m-%d")
    mkt_cal = mcal.get_calendar(mkt.upper())
    schedule = mkt_cal.schedule(start_date=dt_str, end_date=dt_str)

    return not schedule.empty
