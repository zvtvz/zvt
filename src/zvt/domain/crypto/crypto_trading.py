# -*- coding: utf-8 -*-
"""
Crypto Trading Domain Models
Database schema for order management, positions, and trade execution
"""

from decimal import Decimal
from enum import Enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DECIMAL
from sqlalchemy.orm import declarative_base
import uuid

from zvt.contract import Mixin
from zvt.contract.register import register_schema

CryptoTradingBase = declarative_base()


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    OCO = "oco"  # One-Cancels-Other


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"


class CryptoOrder(CryptoTradingBase, Mixin):
    """
    Cryptocurrency order management table
    Tracks all orders from creation to completion
    """
    __tablename__ = "crypto_order"
    
    # Order identification
    strategy_id = Column(String(128))  # Strategy that generated this order
    parent_order_id = Column(String(128))  # For split/child orders
    exchange_order_id = Column(String(128))  # Exchange-specific order ID
    
    # Trading pair and exchange
    entity_id = Column(String(128))  # CryptoPair/CryptoPerp entity ID
    symbol = Column(String(32), nullable=False)  # BTC/USDT, ETH/USDT
    exchange = Column(String(32), nullable=False)  # binance, okx, bybit, coinbase
    
    # Order specifications
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit, stop_loss
    quantity = Column(DECIMAL(20, 8), nullable=False)  # Order quantity
    price = Column(DECIMAL(20, 8))  # Limit price (null for market orders)
    stop_price = Column(DECIMAL(20, 8))  # Stop price for stop orders
    time_in_force = Column(String(10), default="GTC")  # GTC, IOC, FOK
    
    # Order status and execution
    status = Column(String(20), default=OrderStatus.PENDING.value)
    filled_quantity = Column(DECIMAL(20, 8), default=0)  # Quantity filled so far
    remaining_quantity = Column(DECIMAL(20, 8))  # Quantity remaining
    avg_fill_price = Column(DECIMAL(20, 8))  # Average execution price
    
    # Timestamps
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    submitted_timestamp = Column(DateTime)  # When submitted to exchange
    filled_timestamp = Column(DateTime)  # When completely filled
    cancelled_timestamp = Column(DateTime)  # When cancelled
    
    # Fees and costs
    commission = Column(DECIMAL(20, 8), default=0)  # Trading fees paid
    commission_asset = Column(String(10))  # Asset used for fees (USDT, BNB, etc.)
    
    # Additional metadata
    client_order_id = Column(String(128))  # Client-generated unique ID
    order_reason = Column(Text)  # Why this order was placed
    order_metadata = Column(JSON)  # Additional order metadata


class CryptoPosition(CryptoTradingBase, Mixin):
    """
    Cryptocurrency position tracking table
    Tracks current positions across exchanges with real-time PnL
    """
    __tablename__ = "crypto_position"
    
    # Position identification
    portfolio_id = Column(String(128), nullable=False)  # Portfolio this position belongs to
    strategy_id = Column(String(128))  # Strategy managing this position
    
    # Trading pair and exchange
    entity_id = Column(String(128))  # CryptoPair/CryptoPerp entity ID
    symbol = Column(String(32), nullable=False)  # BTC/USDT, ETH/USDT
    exchange = Column(String(32), nullable=False)  # binance, okx, bybit, coinbase
    
    # Position details
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(DECIMAL(20, 8), nullable=False)  # Current position size
    avg_entry_price = Column(DECIMAL(20, 8), nullable=False)  # Average entry price
    current_price = Column(DECIMAL(20, 8))  # Current market price
    
    # PnL tracking
    unrealized_pnl = Column(DECIMAL(20, 8), default=0)  # Mark-to-market PnL
    realized_pnl = Column(DECIMAL(20, 8), default=0)  # Realized PnL from closed trades
    total_cost = Column(DECIMAL(20, 8), nullable=False)  # Total cost basis
    market_value = Column(DECIMAL(20, 8))  # Current market value
    
    # Margin and leverage (for derivatives)
    margin_used = Column(DECIMAL(20, 8), default=0)  # Margin allocated to position
    leverage = Column(DECIMAL(5, 2), default=1.0)  # Leverage ratio
    liquidation_price = Column(DECIMAL(20, 8))  # Liquidation price (for leveraged positions)
    
    # Risk management
    stop_loss_price = Column(DECIMAL(20, 8))  # Stop loss level
    take_profit_price = Column(DECIMAL(20, 8))  # Take profit level
    
    # Position lifecycle
    opened_timestamp = Column(DateTime, default=datetime.utcnow)
    last_update_timestamp = Column(DateTime, default=datetime.utcnow)
    closed_timestamp = Column(DateTime)  # When position was closed
    
    # Accounting method
    accounting_method = Column(String(10), default="FIFO")  # FIFO, LIFO, AvgCost


class CryptoTrade(CryptoTradingBase, Mixin):
    """
    Cryptocurrency trade execution table
    Records individual trade executions and fills
    """
    __tablename__ = "crypto_trade"
    
    # Trade identification
    order_id = Column(String(128), nullable=False)  # Order that generated this trade
    position_id = Column(String(128))  # Position this trade affects
    exchange_trade_id = Column(String(128))  # Exchange-specific trade ID
    
    # Trading pair and exchange
    entity_id = Column(String(128))  # CryptoPair/CryptoPerp entity ID
    symbol = Column(String(32), nullable=False)  # BTC/USDT, ETH/USDT
    exchange = Column(String(32), nullable=False)  # binance, okx, bybit, coinbase
    
    # Trade details
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(DECIMAL(20, 8), nullable=False)  # Trade quantity
    price = Column(DECIMAL(20, 8), nullable=False)  # Execution price
    notional_value = Column(DECIMAL(20, 8), nullable=False)  # Total trade value
    
    # Fees and costs
    commission = Column(DECIMAL(20, 8), default=0)  # Trading fee
    commission_asset = Column(String(10))  # Fee currency
    is_maker = Column(Boolean, default=False)  # Maker vs taker trade
    
    # Timing
    execution_timestamp = Column(DateTime, default=datetime.utcnow)
    trade_date = Column(DateTime)  # Settlement date
    
    # Market context
    bid_price = Column(DECIMAL(20, 8))  # Best bid at execution time
    ask_price = Column(DECIMAL(20, 8))  # Best ask at execution time
    spread = Column(DECIMAL(20, 8))  # Bid-ask spread
    
    # Trade metadata
    liquidity_flag = Column(String(10))  # Added/Removed liquidity
    trade_metadata = Column(JSON)  # Additional trade data


class CryptoPortfolio(CryptoTradingBase, Mixin):
    """
    Cryptocurrency portfolio summary table
    Tracks portfolio-level metrics and performance
    """
    __tablename__ = "crypto_portfolio"
    
    # Portfolio identification
    portfolio_name = Column(String(128), nullable=False)
    user_id = Column(String(128), nullable=False)  # Owner user ID
    strategy_ids = Column(JSON)  # List of strategies in this portfolio
    
    # Portfolio configuration
    base_currency = Column(String(10), default="USDT")  # Portfolio base currency
    exchanges = Column(JSON)  # List of exchanges used
    is_active = Column(Boolean, default=True)  # Portfolio active status
    
    # Current value and performance
    total_value = Column(DECIMAL(20, 8))  # Current portfolio value
    cash_balance = Column(DECIMAL(20, 8))  # Available cash
    invested_value = Column(DECIMAL(20, 8))  # Value in positions
    total_cost = Column(DECIMAL(20, 8))  # Total cost basis
    
    # Daily performance
    daily_pnl = Column(DECIMAL(20, 8))  # Today's PnL
    daily_return_pct = Column(DECIMAL(10, 6))  # Today's return %
    
    # Cumulative performance
    total_return = Column(DECIMAL(20, 8))  # Total dollar return
    total_return_pct = Column(DECIMAL(10, 6))  # Total percentage return
    
    # Risk metrics
    max_drawdown = Column(DECIMAL(10, 6))  # Maximum drawdown %
    volatility = Column(DECIMAL(10, 6))  # Return volatility
    sharpe_ratio = Column(DECIMAL(10, 6))  # Risk-adjusted return
    win_rate = Column(DECIMAL(5, 4))  # Percentage of winning trades
    
    # Portfolio limits
    max_position_size = Column(DECIMAL(20, 8))  # Maximum position size
    max_daily_loss = Column(DECIMAL(20, 8))  # Maximum daily loss limit
    max_leverage = Column(DECIMAL(5, 2), default=1.0)  # Maximum leverage allowed
    
    # Timestamps
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    last_update_timestamp = Column(DateTime, default=datetime.utcnow)


class CryptoRiskLimit(CryptoTradingBase, Mixin):
    """
    Risk management limits and controls
    Defines risk limits at portfolio and position levels
    """
    __tablename__ = "crypto_risk_limit"
    
    # Scope identification
    portfolio_id = Column(String(128))  # Portfolio these limits apply to
    strategy_id = Column(String(128))  # Strategy these limits apply to
    symbol = Column(String(32))  # Symbol these limits apply to (if symbol-specific)
    exchange = Column(String(32))  # Exchange these limits apply to
    
    # Position limits
    max_position_size = Column(DECIMAL(20, 8))  # Maximum position size
    max_position_value = Column(DECIMAL(20, 8))  # Maximum position value
    max_portfolio_allocation = Column(DECIMAL(5, 4))  # Maximum % of portfolio
    
    # Loss limits
    stop_loss_pct = Column(DECIMAL(5, 4))  # Stop loss percentage
    daily_loss_limit = Column(DECIMAL(20, 8))  # Maximum daily loss
    drawdown_limit = Column(DECIMAL(5, 4))  # Maximum drawdown before stop
    
    # Leverage limits
    max_leverage = Column(DECIMAL(5, 2), default=1.0)  # Maximum leverage
    margin_ratio_limit = Column(DECIMAL(5, 4))  # Minimum margin ratio
    
    # Trading frequency limits
    max_orders_per_hour = Column(Integer)  # Order rate limiting
    max_orders_per_day = Column(Integer)  # Daily order limit
    cooling_period_minutes = Column(Integer)  # Cooling period after loss
    
    # Active status
    is_active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    updated_timestamp = Column(DateTime, default=datetime.utcnow)


# Register schemas with ZVT
register_schema(
    providers=["zvt"],
    db_name="crypto_trading",
    schema_base=CryptoTradingBase
)

# Export all trading models
__all__ = [
    "OrderSide",
    "OrderType", 
    "OrderStatus",
    "PositionSide",
    "CryptoOrder",
    "CryptoPosition",
    "CryptoTrade",
    "CryptoPortfolio",
    "CryptoRiskLimit"
]