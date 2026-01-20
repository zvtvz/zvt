# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float, Integer, DateTime, BigInteger, JSON, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

CryptoTickBase = declarative_base()


class CryptoTrade(CryptoTickBase, Mixin):
    """
    Individual cryptocurrency trades (tick-level data).
    Captures every executed trade with price, volume, and side information.
    """
    __tablename__ = "crypto_trade"
    
    #: Provider-specific fields
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    
    #: Trade execution details
    #: Trade ID from exchange (for deduplication)
    trade_id = Column(String(length=128))
    #: Execution price
    price = Column(Float)
    #: Trade volume in base asset
    volume = Column(Float)
    #: Trade volume in quote asset (price * volume)
    quote_volume = Column(Float)
    #: Trade side: 'buy' or 'sell' (from taker perspective)
    side = Column(String(length=16))
    
    #: Market microstructure
    #: True if this trade was buyer-initiated (market buy)
    is_buyer_maker = Column(Boolean)
    #: Best bid price at time of trade
    bid_price = Column(Float)
    #: Best ask price at time of trade  
    ask_price = Column(Float)
    #: Spread at time of trade
    spread = Column(Float)
    
    #: Additional metadata
    #: Exchange-specific trade flags
    trade_flags = Column(String(length=64))
    #: Millisecond precision timestamp
    timestamp_ms = Column(BigInteger)


class CryptoOrderbook(CryptoTickBase, Mixin):
    """
    Level 2 order book snapshots and incremental updates.
    Captures bid/ask depth at multiple price levels.
    """
    __tablename__ = "crypto_orderbook"
    
    #: Provider-specific fields
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    
    #: Order book versioning and integrity
    #: Update ID for ordering and gap detection
    update_id = Column(BigInteger)
    #: Previous update ID for continuity checking
    prev_update_id = Column(BigInteger)
    #: First update ID in this message (for snapshots)
    first_update_id = Column(BigInteger)
    #: Last update ID in this message
    last_update_id = Column(BigInteger)
    
    #: Order book data structure
    #: Bid levels: [price, quantity] pairs
    bids = Column(JSON)
    #: Ask levels: [price, quantity] pairs  
    asks = Column(JSON)
    
    #: Order book quality metrics
    #: Number of bid levels
    bid_levels = Column(Integer)
    #: Number of ask levels
    ask_levels = Column(Integer)
    #: Best bid price
    best_bid = Column(Float)
    #: Best ask price
    best_ask = Column(Float)
    #: Bid-ask spread
    spread = Column(Float)
    #: Spread as percentage of mid price
    spread_pct = Column(Float)
    #: Mid price
    mid_price = Column(Float)
    
    #: Depth analysis
    #: Total bid volume (all levels)
    bid_volume = Column(Float)
    #: Total ask volume (all levels)
    ask_volume = Column(Float)
    #: Volume-weighted bid price
    bid_vwap = Column(Float)
    #: Volume-weighted ask price
    ask_vwap = Column(Float)
    
    #: Data integrity
    #: Exchange-provided checksum for validation
    checksum = Column(String(length=64))
    #: Is this a snapshot (True) or incremental update (False)
    is_snapshot = Column(Boolean, default=False)
    #: Millisecond precision timestamp
    timestamp_ms = Column(BigInteger)


class CryptoFunding(CryptoTickBase, Mixin):
    """
    Perpetual futures funding rate data.
    Critical for perpetual contract pricing and cost calculation.
    """
    __tablename__ = "crypto_funding"
    
    #: Provider-specific fields
    provider = Column(String(length=32))
    code = Column(String(length=32))  # perpetual contract code
    name = Column(String(length=32))
    
    #: Funding rate mechanics
    #: Current funding rate (as decimal, e.g., 0.0001 = 0.01%)
    funding_rate = Column(Float)
    #: Predicted next funding rate
    predicted_rate = Column(Float)
    #: Funding timestamp (when rate was/will be applied)
    funding_timestamp = Column(DateTime)
    #: Next funding timestamp
    next_funding_timestamp = Column(DateTime)
    #: Funding interval in hours
    funding_interval_hours = Column(Integer, default=8)
    
    #: Funding rate calculation inputs
    #: Mark price used for funding calculation
    mark_price = Column(Float)
    #: Index price (underlying asset price)
    index_price = Column(Float) 
    #: Premium rate component
    premium_rate = Column(Float)
    #: Interest rate component
    interest_rate = Column(Float)
    
    #: Funding cost impact
    #: For 1x long position (negative = pay funding)
    funding_cost_long = Column(Float)
    #: For 1x short position (positive = receive funding)  
    funding_cost_short = Column(Float)
    
    #: Historical context
    #: 24-hour average funding rate
    avg_funding_24h = Column(Float)
    #: Maximum funding rate in last 24h
    max_funding_24h = Column(Float)
    #: Minimum funding rate in last 24h
    min_funding_24h = Column(Float)
    
    #: Market indicators derived from funding
    #: True if funding rate indicates strong bullish sentiment
    is_bullish_funding = Column(Boolean)
    #: True if funding rate is at extreme levels
    is_extreme_funding = Column(Boolean)
    
    #: Data source metadata
    #: Calculation timestamp
    calculation_timestamp = Column(DateTime)
    #: Millisecond precision timestamp
    timestamp_ms = Column(BigInteger)


# Register all tick schemas with crypto providers
register_schema(
    providers=["binance", "okx", "bybit", "coinbase", "ccxt"],
    db_name="crypto_tick",
    schema_base=CryptoTickBase
)

# Export all tick schemas
__all__ = ["CryptoTrade", "CryptoOrderbook", "CryptoFunding"]