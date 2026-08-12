# -*- coding: utf-8 -*-

import pandas as pd
from typing import List, Optional
from datetime import datetime, time

from zvt.utils.time_utils import to_pd_timestamp


class CryptoTradingCalendar:
    """
    24/7 Cryptocurrency Trading Calendar
    
    Unlike traditional markets, crypto markets operate continuously without
    market holidays or trading sessions. This calendar reflects that reality.
    """
    
    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None) -> pd.DatetimeIndex:
        """
        Get all trading dates for crypto markets (every day is a trading day).
        
        :param start_date: Start date
        :param end_date: End date  
        :return: DatetimeIndex of all dates (daily frequency)
        """
        if start_date is None:
            start_date = "2009-01-03"  # Bitcoin genesis block
        if end_date is None:
            end_date = pd.Timestamp.now()
            
        return pd.date_range(start_date, end_date, freq="D")
    
    @classmethod
    def is_trading_day(cls, timestamp) -> bool:
        """
        Check if a given timestamp is a trading day (always True for crypto).
        
        :param timestamp: Timestamp to check
        :return: Always True (crypto trades 24/7)
        """
        return True
    
    @classmethod
    def get_trading_intervals(cls, include_extended_hours=False) -> List[tuple]:
        """
        Get trading intervals (24/7 for crypto).
        
        :param include_extended_hours: Ignored for crypto (always extended)
        :return: Single 24-hour interval
        """
        return [("00:00", "24:00")]
    
    @classmethod
    def is_trading_time(cls, timestamp=None) -> bool:
        """
        Check if current/given time is within trading hours (always True).
        
        :param timestamp: Timestamp to check (optional)
        :return: Always True (crypto trades 24/7)
        """
        return True
    
    @classmethod
    def get_previous_trading_date(cls, date) -> pd.Timestamp:
        """
        Get the previous trading date (previous day for crypto).
        
        :param date: Reference date
        :return: Previous date
        """
        date = to_pd_timestamp(date)
        return date - pd.Timedelta(days=1)
    
    @classmethod
    def get_next_trading_date(cls, date) -> pd.Timestamp:
        """
        Get the next trading date (next day for crypto).
        
        :param date: Reference date
        :return: Next date
        """
        date = to_pd_timestamp(date)
        return date + pd.Timedelta(days=1)
    
    @classmethod
    def get_trading_minutes_per_day(cls) -> int:
        """
        Get trading minutes per day (1440 for crypto - 24 * 60).
        
        :return: 1440 minutes
        """
        return 24 * 60
    
    @classmethod
    def get_market_open_time(cls, date=None) -> pd.Timestamp:
        """
        Get market open time (00:00 UTC for crypto).
        
        :param date: Reference date
        :return: Midnight UTC
        """
        if date is None:
            date = pd.Timestamp.now().date()
        return pd.Timestamp.combine(date, time.min).tz_localize('UTC')
    
    @classmethod
    def get_market_close_time(cls, date=None) -> pd.Timestamp:
        """
        Get market close time (23:59:59 UTC for crypto).
        
        :param date: Reference date
        :return: End of day UTC
        """
        if date is None:
            date = pd.Timestamp.now().date()
        return pd.Timestamp.combine(date, time.max).tz_localize('UTC')
    
    @classmethod
    def adjust_timestamp_to_trading_period(cls, timestamp) -> pd.Timestamp:
        """
        Adjust timestamp to nearest trading period (no adjustment needed for crypto).
        
        :param timestamp: Input timestamp
        :return: Same timestamp (crypto trades continuously)
        """
        return to_pd_timestamp(timestamp)
    
    @classmethod
    def get_interval_timestamps(
        cls, 
        start_date, 
        end_date, 
        interval_minutes: int = 60
    ) -> pd.DatetimeIndex:
        """
        Get all interval timestamps between dates for crypto markets.
        
        :param start_date: Start date
        :param end_date: End date
        :param interval_minutes: Interval in minutes
        :return: DatetimeIndex with interval timestamps
        """
        start_date = to_pd_timestamp(start_date)
        end_date = to_pd_timestamp(end_date)
        
        freq_str = f"{interval_minutes}min"
        return pd.date_range(
            start=start_date,
            end=end_date,
            freq=freq_str,
            tz='UTC'
        )
    
    @classmethod
    def get_funding_timestamps(
        cls,
        start_date,
        end_date, 
        funding_interval_hours: int = 8
    ) -> pd.DatetimeIndex:
        """
        Get funding settlement timestamps for perpetual futures.
        
        :param start_date: Start date
        :param end_date: End date
        :param funding_interval_hours: Funding interval (default 8 hours)
        :return: DatetimeIndex with funding timestamps
        """
        start_date = to_pd_timestamp(start_date)
        end_date = to_pd_timestamp(end_date)
        
        # Most exchanges settle funding at 00:00, 08:00, 16:00 UTC
        freq_str = f"{funding_interval_hours}h"
        
        # Start from nearest funding time (usually 00:00 UTC)
        start_funding = start_date.floor('D')  # Start of day
        
        return pd.date_range(
            start=start_funding,
            end=end_date,
            freq=freq_str,
            tz='UTC'
        )


class CryptoMarketStatus:
    """
    Crypto market status utilities.
    Unlike traditional markets, crypto status focuses on exchange connectivity
    and maintenance windows rather than market open/close.
    """
    
    @classmethod
    def is_market_open(cls) -> bool:
        """Always True for crypto markets."""
        return True
    
    @classmethod
    def is_weekend(cls, timestamp=None) -> bool:
        """
        Check if timestamp is weekend (irrelevant for crypto but kept for compatibility).
        """
        if timestamp is None:
            timestamp = pd.Timestamp.now()
        return timestamp.weekday() >= 5
    
    @classmethod
    def is_holiday(cls, timestamp=None) -> bool:
        """
        Check if timestamp is holiday (always False for crypto).
        """
        return False
    
    @classmethod
    def get_market_status(cls, timestamp=None) -> str:
        """
        Get current market status (always 'open' for crypto).
        """
        return "open"


# Integration with ZVT TradableEntity classes
def integrate_crypto_calendar():
    """
    Integrate crypto calendar methods with crypto entity classes.
    This function patches the crypto entity classes to use 24/7 calendar.
    """
    from zvt.domain.crypto.crypto_meta import CryptoAsset, CryptoPair, CryptoPerp
    
    # Patch all crypto entities with 24/7 calendar methods
    for crypto_class in [CryptoAsset, CryptoPair, CryptoPerp]:
        crypto_class.get_trading_dates = CryptoTradingCalendar.get_trading_dates
        crypto_class.is_trading_day = CryptoTradingCalendar.is_trading_day
        crypto_class.get_trading_intervals = CryptoTradingCalendar.get_trading_intervals
        crypto_class.is_trading_time = CryptoTradingCalendar.is_trading_time


__all__ = ["CryptoTradingCalendar", "CryptoMarketStatus", "integrate_crypto_calendar"]