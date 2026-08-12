# -*- coding: utf-8 -*-
"""
Trading Engine Service Interfaces
=================================

Clean service interfaces extracted from monolithic CryptoTradingEngine to achieve
SOLID compliance and improve maintainability.

Architecture Pattern: Interface Segregation + Dependency Inversion
- Focused single-responsibility interfaces  
- Clean separation of concerns
- Improved testability through protocols
- Backward compatibility via composition
"""

from typing import Protocol, Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime

# Import necessary types
from .crypto_trading_engine import (
    OrderRequest, OrderResult, PositionInfo, PortfolioSummary, PnLMetrics
)


class ITradingService(Protocol):
    """
    Core trading operations interface.
    
    Responsibilities:
    - Order execution and lifecycle management
    - Exchange routing and connector management  
    - Trade recording and audit logging
    """
    
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        """Execute order with routing and risk validation."""
        ...
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel existing order."""
        ...
    
    def get_order_status(self, order_id: str) -> Optional[Any]:
        """Get current order status."""
        ...
    
    def get_available_exchanges(self) -> List[str]:
        """Get list of available exchanges."""
        ...
    
    def route_order(self, order_request: OrderRequest) -> str:
        """Determine best exchange for order execution."""
        ...


class IPortfolioService(Protocol):
    """
    Portfolio management interface.
    
    Responsibilities:
    - Position tracking and P&L calculations
    - Portfolio creation and management
    - Multi-currency support and conversion
    """
    
    def get_positions(self, portfolio_id: str = "default") -> List[PositionInfo]:
        """Get all positions for a portfolio."""
        ...
    
    def get_portfolio_summary(self, portfolio_id: str = "default") -> PortfolioSummary:
        """Get comprehensive portfolio summary."""
        ...
    
    def calculate_portfolio_value(self, portfolio_id: str, target_currency: str = None) -> Any:
        """Calculate total portfolio value with currency conversion."""
        ...
    
    def create_portfolio(self, portfolio_id: str, base_currency: str = "USDT", 
                        target_allocations: Dict[str, Decimal] = None, 
                        initial_value: Decimal = Decimal("0")) -> Any:
        """Create new portfolio with configuration."""
        ...
    
    def add_position_to_portfolio(self, portfolio_id: str, symbol: str, 
                                 quantity: Decimal, avg_price: Decimal = None, 
                                 exchange: str = "binance", category: str = None):
        """Add position to existing portfolio."""
        ...
    
    def calculate_position_pnl(self, symbol: str, exchange: str = "binance", 
                              portfolio_id: str = "default") -> PnLMetrics:
        """Calculate profit/loss metrics for position."""
        ...


class IAnalyticsService(Protocol):
    """
    Performance analytics and reporting interface.
    
    Responsibilities:
    - Performance metrics calculation (Sharpe, Sortino, Calmar)
    - Benchmark comparison and attribution analysis
    - Risk metrics (VaR, tracking error)
    """
    
    def calculate_portfolio_performance(self, portfolio_id: str) -> Any:
        """Calculate comprehensive performance metrics."""
        ...
    
    def calculate_sharpe_ratio(self, portfolio_id: str, risk_free_rate: Decimal) -> Any:
        """Calculate Sharpe ratio with risk-free rate."""
        ...
    
    def calculate_sortino_ratio(self, portfolio_id: str, target_return: Decimal) -> Any:
        """Calculate Sortino ratio with target return."""
        ...
    
    def calculate_calmar_ratio(self, portfolio_id: str) -> Any:
        """Calculate Calmar ratio (CAGR / Max Drawdown)."""
        ...
    
    def calculate_var(self, portfolio_id: str, confidence_level: Decimal) -> Any:
        """Calculate Value at Risk at specified confidence level."""
        ...
    
    def compare_to_benchmark(self, portfolio_id: str, benchmark: str) -> Any:
        """Compare portfolio performance to benchmark."""
        ...
    
    def calculate_performance_attribution(self, portfolio_id: str) -> Any:
        """Calculate performance attribution by category."""
        ...
    
    def calculate_tracking_error(self, portfolio_id: str, benchmark: str) -> Any:
        """Calculate tracking error analysis."""
        ...


class IRebalancingService(Protocol):
    """
    Portfolio rebalancing interface.
    
    Responsibilities:
    - Portfolio drift detection and analysis
    - Rebalancing trade generation
    - Cost analysis and optimization
    """
    
    def detect_portfolio_drift(self, portfolio_id: str) -> Any:
        """Detect drift from target allocations."""
        ...
    
    def generate_rebalancing_trades(self, portfolio_id: str) -> Any:
        """Generate trades to rebalance portfolio."""
        ...
    
    def calculate_rebalancing_costs(self, portfolio_id: str, trades: List[Dict]) -> Any:
        """Calculate transaction costs for rebalancing."""
        ...
    
    def set_trading_fees(self, exchange: str, symbol: str, 
                        maker_fee: Decimal, taker_fee: Decimal):
        """Set trading fees for cost calculations."""
        ...
    
    def set_market_impact(self, symbol: str, impact_pct: Decimal):
        """Set market impact estimates."""
        ...


class IHatchetAdapter(Protocol):
    """
    Hatchet workflow integration interface.
    
    Responsibilities:
    - Workflow orchestration and management
    - Event-driven architecture coordination
    - Performance monitoring and metrics
    """
    
    def execute_order_workflow(self, order_request: OrderRequest) -> Any:
        """Execute order via Hatchet workflow."""
        ...
    
    def start_rebalancing_workflow(self, portfolio_id: str, 
                                  target_allocations: Dict = None) -> Any:
        """Start portfolio rebalancing workflow."""
        ...
    
    def start_risk_monitoring_workflow(self, portfolio_id: str, 
                                     check_interval: str, **config) -> Any:
        """Start risk monitoring workflow."""
        ...
    
    def emit_price_update_event(self, symbol: str, price: Decimal) -> Any:
        """Emit price update event to workflows."""
        ...
    
    def get_triggered_workflows(self, event_type: str, **filters) -> List[Any]:
        """Get workflows triggered by events."""
        ...
    
    def get_hatchet_metrics(self) -> Any:
        """Get Hatchet workflow performance metrics."""
        ...
    
    def handle_trading_error(self, error_type: str, context: Dict) -> Dict:
        """Handle trading errors via workflows."""
        ...


# Export all interfaces
__all__ = [
    'ITradingService',
    'IPortfolioService', 
    'IAnalyticsService',
    'IRebalancingService',
    'IHatchetAdapter'
]