# src/zvt/trading/models.py
"""
Trading Models for ZVT Crypto Trading Platform
Data models for orders, positions, trades, and portfolio management

This module defines the core data structures used throughout the trading system.
All models use Decimal for precise financial calculations.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class OrderType(Enum):
    """Order types supported by the trading system"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    OCO = "oco"  # One-Cancels-Other


class OrderSide(Enum):
    """Order sides - buy or sell"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status throughout lifecycle"""
    PENDING = "pending"
    PLACED = "placed"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """
    Order model representing a trading order
    Used for order placement, tracking, and management
    """
    symbol: str
    side: OrderSide
    amount: Decimal
    order_type: OrderType
    price: Optional[Decimal] = None  # Required for limit orders
    stop_price: Optional[Decimal] = None  # Required for stop orders
    time_in_force: str = "GTC"  # Good-Till-Cancelled
    order_id: Optional[str] = None
    client_order_id: Optional[str] = field(default_factory=lambda: str(uuid4()))
    allow_splitting: bool = False
    max_slippage: Optional[Decimal] = None
    
    def __post_init__(self):
        """Validate order parameters after initialization"""
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders require a price")
        
        if self.order_type == OrderType.STOP_LOSS and self.stop_price is None:
            raise ValueError("Stop loss orders require a stop price")


@dataclass 
class ExecutionEstimate:
    """Execution cost and timing estimates for an order"""
    estimated_cost: Decimal
    estimated_slippage: Decimal
    estimated_fee: Decimal
    estimated_execution_time: float  # seconds
    confidence_level: Decimal  # 0.0 to 1.0


@dataclass
class SplitOrder:
    """Represents a portion of a split order"""
    exchange: str
    amount: Decimal
    estimated_price: Decimal
    routing_reason: str


@dataclass
class OrderRoutingResult:
    """Result of order routing analysis"""
    selected_exchange: str
    routing_reason: str
    execution_estimate: Optional[ExecutionEstimate] = None
    alternative_exchanges: List[str] = field(default_factory=list)
    split_required: bool = False
    split_orders: List[SplitOrder] = field(default_factory=list)


@dataclass
class OrderResult:
    """Result of order placement operation"""
    success: bool
    order_id: Optional[str] = None
    status: str = "unknown"
    exchange: str = ""
    message: str = ""
    limit_price: Optional[Decimal] = None
    reserved_amount: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderValidationResult:
    """Result of order validation checks"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class OrderStatusInfo:
    """Current status information for an order"""
    order_id: str
    current_status: str
    filled_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class Trade:
    """
    Trade execution record
    Represents a completed trade transaction
    """
    trade_id: str
    symbol: str
    side: str  # "buy" or "sell"
    amount: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    exchange: str = ""
    order_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of the trade"""
        return self.amount * self.price


@dataclass
class Position:
    """
    Position model representing a trading position
    Supports multi-exchange position aggregation
    """
    symbol: str
    total_quantity: Decimal = Decimal("0")
    avg_cost: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    exchange_positions: Dict[str, Decimal] = field(default_factory=dict)
    last_update: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> Optional[Decimal]:
        """Current market value - requires current price"""
        return None  # Will be calculated by PositionManager
    
    @property
    def total_cost_basis(self) -> Decimal:
        """Total cost basis of the position"""
        return self.total_quantity * self.avg_cost


@dataclass
class PositionPnL:
    """Position profit and loss information"""
    symbol: str
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    percentage_return: Decimal
    market_value: Decimal
    cost_basis: Decimal
    
    @property
    def total_pnl(self) -> Decimal:
        """Total PnL (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl


@dataclass
class RiskMetrics:
    """Position or portfolio risk metrics"""
    value_at_risk_95: Optional[Decimal] = None
    volatility: Decimal = Decimal("0")
    max_drawdown_pct: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None


@dataclass
class PortfolioSummary:
    """Summary of portfolio positions and performance"""
    total_cost: Decimal
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_return_pct: Decimal
    number_of_positions: int
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class ConcentrationRiskCheck:
    """Result of portfolio concentration risk analysis"""
    exceeds_limit: bool
    projected_allocation: Decimal
    max_allowed_allocation: Decimal
    current_allocation: Decimal


@dataclass
class CorrelationRiskAnalysis:
    """Portfolio correlation risk analysis"""
    high_correlation_pairs: List[Dict[str, Any]]
    portfolio_correlation_score: Decimal
    diversification_ratio: Decimal


@dataclass
class LeverageInfo:
    """Portfolio leverage information"""
    current_leverage: Decimal
    max_leverage: Decimal
    leverage_utilization: Decimal
    remaining_buying_power: Decimal
    margin_used: Decimal
    account_equity: Decimal


@dataclass
class PositionSnapshot:
    """Historical snapshot of a position"""
    timestamp: datetime
    quantity: Decimal
    avg_cost: Decimal
    market_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None


@dataclass
class PositionHistory:
    """Historical position data and analytics"""
    symbol: str
    snapshots: List[PositionSnapshot]
    total_trades: int
    total_volume: Decimal
    first_trade_date: datetime
    last_trade_date: datetime


@dataclass
class PerformanceMetrics:
    """Position performance analytics"""
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_return: Decimal
    return_percentage: Decimal
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    max_consecutive_wins: int
    max_consecutive_losses: int


@dataclass
class DrawdownAnalysis:
    """Position drawdown analysis"""
    max_drawdown_pct: Decimal
    max_drawdown_amount: Decimal
    current_drawdown_pct: Decimal
    current_drawdown_amount: Decimal
    drawdown_periods: List[Dict[str, Any]]
    recovery_periods: List[Dict[str, Any]]


# Exchange and Market Data Models

@dataclass
class ExchangeLiquidity:
    """Exchange liquidity information"""
    exchange: str
    symbol: str
    bid_depth: Decimal = Decimal("0")
    ask_depth: Decimal = Decimal("0")
    fee: Decimal = Decimal("0.001")
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class MarketPrice:
    """Current market price information"""
    symbol: str
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderBookLevel:
    """Order book price level"""
    price: Decimal
    quantity: Decimal


@dataclass
class OrderBook:
    """Exchange order book data"""
    symbol: str
    exchange: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def best_bid(self) -> Optional[Decimal]:
        """Best bid price"""
        return self.bids[0].price if self.bids else None
    
    @property  
    def best_ask(self) -> Optional[Decimal]:
        """Best ask price"""
        return self.asks[0].price if self.asks else None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Bid-ask spread"""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


# Portfolio Management Models

@dataclass
class Portfolio:
    """Portfolio containing multiple positions"""
    portfolio_id: str
    positions: Dict[str, Position] = field(default_factory=dict)
    cash_balances: Dict[str, Decimal] = field(default_factory=dict)
    base_currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class BalanceInfo:
    """Account balance information"""
    currency: str
    total_balance: Decimal
    available_balance: Decimal
    reserved_balance: Decimal = Decimal("0")
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class MarginInfo:
    """Margin account information"""
    total_equity: Decimal
    used_margin: Decimal
    free_margin: Decimal
    margin_level: Decimal  # Percentage
    margin_call_level: Decimal = Decimal("1.0")  # 100%
    stop_out_level: Decimal = Decimal("0.5")  # 50%


# Risk Management Models

@dataclass 
class PositionLimit:
    """Position size limits for risk management"""
    symbol: str
    max_position: Decimal
    max_order_size: Decimal = Decimal("0")
    max_daily_volume: Decimal = Decimal("0")
    enabled: bool = True


@dataclass
class RiskLimit:
    """Risk management limits"""
    max_portfolio_leverage: Decimal = Decimal("1.0")
    max_position_size_pct: Decimal = Decimal("0.1")  # 10%
    max_daily_loss_pct: Decimal = Decimal("0.05")  # 5%
    max_correlation_exposure: Decimal = Decimal("0.6")  # 60%
    var_limit_pct: Decimal = Decimal("0.02")  # 2%


@dataclass
class RiskAlert:
    """Risk management alert"""
    alert_id: str
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    symbol: Optional[str] = None
    current_value: Optional[Decimal] = None
    limit_value: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False