# -*- coding: utf-8 -*-

from sqlalchemy import Column, Float, Boolean, Integer
from zvt.domain.quotes import KdataCommon, TickCommon


class CryptoKdataCommon(KdataCommon):
    """
    Common kdata fields for cryptocurrency trading pairs and perpetual futures.
    Extends the base KdataCommon with crypto-specific fields.
    
    Note: Crypto markets use 'bfq' adjustment type only (no splits/dividends)
    """
    
    #: Volume in base asset (e.g., BTC volume for BTC/USDT)
    volume_base = Column(Float)
    #: Volume in quote asset (e.g., USDT volume for BTC/USDT)  
    volume_quote = Column(Float)
    #: Number of trades in this interval
    trade_count = Column(Integer)
    #: Volume-weighted average price
    vwap = Column(Float)
    
    #: Market conditions indicators
    #: True if this interval had significant price volatility
    is_high_volatility = Column(Boolean, default=False)
    #: True if trading volume was unusually high
    is_high_volume = Column(Boolean, default=False)


class CryptoTickCommon(TickCommon):
    """
    Common tick/quote fields for cryptocurrency markets.
    Extends base TickCommon with crypto-specific real-time data.
    """
    
    #: 24-hour price change percentage
    change_24h_pct = Column(Float)
    #: 24-hour volume in base asset
    volume_24h_base = Column(Float)
    #: 24-hour volume in quote asset
    volume_24h_quote = Column(Float)
    #: 24-hour high price
    high_24h = Column(Float)
    #: 24-hour low price
    low_24h = Column(Float)
    
    #: Order book depth (top 5 levels)
    #: These extend the base bid_vol/ask_vol from TickCommon
    order_book_depth = Column(Integer, default=5)
    
    #: Market microstructure
    #: Bid-ask spread
    spread = Column(Float)
    #: Spread as percentage of mid price
    spread_pct = Column(Float)
    #: Mid price (bid + ask) / 2
    mid_price = Column(Float)


# For compatibility - these will be used by auto-generated schemas
__all__ = ["CryptoKdataCommon", "CryptoTickCommon"]