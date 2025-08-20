# -*- coding: utf-8 -*-
"""
Crypto Trading Engine
Core trading engine that orchestrates order execution, position management, and risk controls
"""

import asyncio
import logging
import time
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import uuid

import pandas as pd
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.contract.api import get_db_session
from zvt.domain.crypto import (
    CryptoOrder, CryptoPosition, TradingTrade, CryptoPortfolio, CryptoRiskLimit,
    OrderSide, OrderType, OrderStatus, PositionSide, CryptoPair, CryptoPerp
)
from zvt.services.crypto.data_loader import CryptoDataLoader
from zvt.services.crypto.stream_service import CryptoStreamService
from zvt.utils.time_utils import now_pd_timestamp, to_pd_timestamp

logger = logging.getLogger(__name__)


@dataclass
class OrderRequest:
    """Order request data structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    exchange: Optional[str] = None  # Auto-route if None
    strategy_id: Optional[str] = None
    portfolio_id: str = "default"
    time_in_force: str = "GTC"
    client_order_id: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class OrderResult:
    """Order execution result"""
    success: bool
    order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    message: str = ""
    filled_quantity: Decimal = Decimal(0)
    avg_fill_price: Optional[Decimal] = None
    commission: Decimal = Decimal(0)
    commission_asset: str = ""


@dataclass
class PositionInfo:
    """Position information data structure"""
    symbol: str
    exchange: str
    side: PositionSide
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    market_value: Decimal
    cost_basis: Decimal


@dataclass
class PortfolioSummary:
    """Portfolio summary information"""
    portfolio_id: str
    total_value: Decimal
    cash_balance: Decimal
    invested_value: Decimal
    daily_pnl: Decimal
    total_return: Decimal
    total_return_pct: float
    positions: List[PositionInfo]


class OrderManager:
    """Manages order lifecycle and execution"""
    
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.pending_orders: Dict[str, CryptoOrder] = {}
        
    def create_order(self, order_request: OrderRequest) -> str:
        """Create a new order and store in database"""
        order_id = str(uuid.uuid4())
        
        # Generate client order ID if not provided
        if not order_request.client_order_id:
            order_request.client_order_id = f"ZVT_{int(time.time() * 1000)}"
        
        # Create order record
        order = CryptoOrder(
            id=order_id,
            strategy_id=order_request.strategy_id,
            symbol=order_request.symbol,
            exchange=order_request.exchange or "auto",
            side=order_request.side.value,
            order_type=order_request.order_type.value,
            quantity=order_request.quantity,
            price=order_request.price,
            stop_price=order_request.stop_price,
            time_in_force=order_request.time_in_force,
            status=OrderStatus.PENDING.value,
            remaining_quantity=order_request.quantity,
            client_order_id=order_request.client_order_id,
            order_reason=f"Strategy: {order_request.strategy_id}",
            order_metadata=order_request.metadata or {}
        )
        
        # Save to database
        with get_db_session(provider="zvt", data_schema=CryptoOrder) as session:
            session.add(order)
            session.commit()
            session.refresh(order)
        
        self.pending_orders[order_id] = order
        logger.info(f"Created order {order_id}: {order_request.side.value} {order_request.quantity} {order_request.symbol}")
        
        return order_id
    
    def update_order_status(self, order_id: str, status: OrderStatus, 
                          filled_quantity: Decimal = None,
                          avg_fill_price: Decimal = None,
                          exchange_order_id: str = None):
        """Update order status and execution details"""
        with get_db_session(provider="zvt", data_schema=CryptoOrder) as session:
            order = session.query(CryptoOrder).filter_by(id=order_id).first()
            if order:
                order.status = status.value
                order.timestamp = now_pd_timestamp()
                
                if exchange_order_id:
                    order.exchange_order_id = exchange_order_id
                
                if filled_quantity is not None:
                    order.filled_quantity = filled_quantity
                    order.remaining_quantity = order.quantity - filled_quantity
                    
                if avg_fill_price is not None:
                    order.avg_fill_price = avg_fill_price
                
                if status == OrderStatus.SUBMITTED:
                    order.submitted_timestamp = datetime.utcnow()
                elif status == OrderStatus.FILLED:
                    order.filled_timestamp = datetime.utcnow()
                elif status == OrderStatus.CANCELLED:
                    order.cancelled_timestamp = datetime.utcnow()
                
                session.commit()
                
                # Update local cache
                if order_id in self.pending_orders:
                    self.pending_orders[order_id] = order
                
                logger.info(f"Updated order {order_id} status to {status.value}")
    
    def get_order(self, order_id: str) -> Optional[CryptoOrder]:
        """Get order by ID"""
        if order_id in self.pending_orders:
            return self.pending_orders[order_id]
        
        with get_db_session(provider="zvt", data_schema=CryptoOrder) as session:
            return session.query(CryptoOrder).filter_by(id=order_id).first()


class PositionManager:
    """Manages cryptocurrency positions and PnL calculation"""
    
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.positions_cache: Dict[str, CryptoPosition] = {}
        
    def get_or_create_position(self, symbol: str, exchange: str, 
                             portfolio_id: str = "default") -> CryptoPosition:
        """Get existing position or create new one"""
        position_key = f"{portfolio_id}_{symbol}_{exchange}"
        
        if position_key in self.positions_cache:
            return self.positions_cache[position_key]
        
        with get_db_session(provider="zvt", data_schema=CryptoPosition) as session:
            position = session.query(CryptoPosition).filter_by(
                portfolio_id=portfolio_id,
                symbol=symbol,
                exchange=exchange
            ).first()
            
            if not position:
                # Create new position
                position = CryptoPosition(
                    id=str(uuid.uuid4()),
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    exchange=exchange,
                    side=PositionSide.LONG.value,
                    quantity=Decimal(0),
                    avg_entry_price=Decimal(0),
                    total_cost=Decimal(0),
                    unrealized_pnl=Decimal(0),
                    realized_pnl=Decimal(0)
                )
                session.add(position)
                session.commit()
                session.refresh(position)
            
            self.positions_cache[position_key] = position
            return position
    
    def update_position_from_trade(self, trade: TradingTrade):
        """Update position based on trade execution"""
        position = self.get_or_create_position(
            trade.symbol, trade.exchange, "default"  # TODO: Get from trade context
        )
        
        trade_quantity = trade.quantity
        trade_value = trade.quantity * trade.price
        
        with get_db_session(provider="zvt", data_schema=CryptoPosition) as session:
            # Refresh position from database
            position = session.merge(position)
            
            if trade.side == OrderSide.BUY.value:
                # Increase position
                if position.quantity == 0:
                    # Opening new position
                    position.quantity = trade_quantity
                    position.avg_entry_price = trade.price
                    position.total_cost = trade_value
                    position.side = PositionSide.LONG.value
                else:
                    # Adding to existing position
                    total_cost = position.total_cost + trade_value
                    total_quantity = position.quantity + trade_quantity
                    position.avg_entry_price = total_cost / total_quantity
                    position.quantity = total_quantity
                    position.total_cost = total_cost
                    
            elif trade.side == OrderSide.SELL.value:
                # Decrease position
                if position.quantity >= trade_quantity:
                    # Closing part or all of position
                    realized_pnl = (trade.price - position.avg_entry_price) * trade_quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= trade_quantity
                    position.total_cost -= position.avg_entry_price * trade_quantity
                    
                    if position.quantity == 0:
                        position.total_cost = Decimal(0)
                        position.avg_entry_price = Decimal(0)
                else:
                    logger.warning(f"Insufficient position to sell: have {position.quantity}, trying to sell {trade_quantity}")
            
            position.last_update_timestamp = datetime.utcnow()
            session.commit()
            
            # Update cache
            position_key = f"{position.portfolio_id}_{position.symbol}_{position.exchange}"
            self.positions_cache[position_key] = position
            
            logger.info(f"Updated position for {trade.symbol}: {position.quantity} @ {position.avg_entry_price}")
    
    def update_market_prices(self, price_updates: Dict[str, Decimal]):
        """Update current market prices and recalculate unrealized PnL"""
        with get_db_session(provider="zvt", data_schema=CryptoPosition) as session:
            for symbol, current_price in price_updates.items():
                positions = session.query(CryptoPosition).filter_by(symbol=symbol).all()
                
                for position in positions:
                    if position.quantity != 0:
                        position.current_price = current_price
                        position.market_value = position.quantity * current_price
                        position.unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity
                        position.last_update_timestamp = datetime.utcnow()
                
                session.commit()
    
    def get_positions(self, portfolio_id: str = "default") -> List[PositionInfo]:
        """Get all positions for a portfolio"""
        with get_db_session(provider="zvt", data_schema=CryptoPosition) as session:
            positions = session.query(CryptoPosition).filter_by(
                portfolio_id=portfolio_id
            ).filter(CryptoPosition.quantity != 0).all()
            
            position_infos = []
            for pos in positions:
                position_infos.append(PositionInfo(
                    symbol=pos.symbol,
                    exchange=pos.exchange,
                    side=PositionSide(pos.side),
                    quantity=pos.quantity,
                    avg_entry_price=pos.avg_entry_price,
                    current_price=pos.current_price or pos.avg_entry_price,
                    unrealized_pnl=pos.unrealized_pnl,
                    realized_pnl=pos.realized_pnl,
                    market_value=pos.market_value or (pos.quantity * pos.avg_entry_price),
                    cost_basis=pos.total_cost
                ))
            
            return position_infos


class RiskManager:
    """Manages risk controls and position limits"""
    
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        
    def validate_order(self, order_request: OrderRequest) -> Tuple[bool, str]:
        """Validate order against risk limits"""
        try:
            # Check position size limits
            if not self._check_position_size_limit(order_request):
                return False, "Order exceeds maximum position size limit"
            
            # Check portfolio allocation limits
            if not self._check_allocation_limit(order_request):
                return False, "Order exceeds maximum portfolio allocation limit"
            
            # Check daily loss limits
            if not self._check_daily_loss_limit(order_request.portfolio_id):
                return False, "Portfolio has exceeded daily loss limit"
            
            # Check order rate limits
            if not self._check_rate_limits(order_request):
                return False, "Order rate limit exceeded"
            
            return True, "Order validated successfully"
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return False, f"Risk validation error: {e}"
    
    def _check_position_size_limit(self, order_request: OrderRequest) -> bool:
        """Check if order exceeds position size limits"""
        with get_db_session(provider="zvt", data_schema=CryptoRiskLimit) as session:
            limits = session.query(CryptoRiskLimit).filter_by(
                symbol=order_request.symbol,
                is_active=True
            ).all()
            
            if not limits:
                return True  # No limits defined
            
            # Get current position
            position_manager = self.trading_engine.position_manager
            current_position = position_manager.get_or_create_position(
                order_request.symbol, 
                order_request.exchange or "binance",
                order_request.portfolio_id
            )
            
            for limit in limits:
                if limit.max_position_size:
                    new_quantity = current_position.quantity + order_request.quantity
                    if new_quantity > limit.max_position_size:
                        return False
            
            return True
    
    def _check_allocation_limit(self, order_request: OrderRequest) -> bool:
        """Check portfolio allocation limits"""
        # Simplified check - in production, would calculate current allocations
        return True
    
    def _check_daily_loss_limit(self, portfolio_id: str) -> bool:
        """Check if portfolio has exceeded daily loss limits"""
        # Simplified check - in production, would calculate daily PnL
        return True
    
    def _check_rate_limits(self, order_request: OrderRequest) -> bool:
        """Check order rate limits"""
        # Simplified check - in production, would track order frequency
        return True


class CryptoTradingEngine:
    """
    Core cryptocurrency trading engine
    Orchestrates order execution, position management, and risk controls
    """
    
    def __init__(self, exchanges: List[str] = None):
        self.exchanges = exchanges or ["binance", "okx", "bybit", "coinbase"]
        self.is_running = False
        
        # Core components
        self.order_manager = OrderManager(self)
        self.position_manager = PositionManager(self)
        self.risk_manager = RiskManager(self)
        
        # Exchange connectors (will be loaded on demand)
        self._connectors: Dict[str, object] = {}
        
        # Data services
        self.data_loader = CryptoDataLoader(exchanges=self.exchanges)
        self.stream_service = None  # Will be initialized if needed
        
        # Performance tracking
        self.order_latency_ms = []
        self.last_price_update = {}
        
        logger.info(f"Initialized CryptoTradingEngine with exchanges: {self.exchanges}")
    
    def start(self):
        """Start the trading engine"""
        if self.is_running:
            logger.warning("Trading engine is already running")
            return
        
        self.is_running = True
        logger.info("CryptoTradingEngine started")
        
        # Start real-time price updates if stream service available
        try:
            from zvt.services.crypto.stream_service import CryptoStreamService
            self.stream_service = CryptoStreamService(exchanges=self.exchanges)
            # TODO: Set up price update handlers
        except Exception as e:
            logger.warning(f"Could not start stream service: {e}")
    
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        if self.stream_service:
            self.stream_service.stop()
        logger.info("CryptoTradingEngine stopped")
    
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        """
        Place a trading order with risk validation and exchange routing
        """
        start_time = time.time()
        
        try:
            # 1. Risk validation
            is_valid, validation_message = self.risk_manager.validate_order(order_request)
            if not is_valid:
                return OrderResult(
                    success=False,
                    message=f"Risk validation failed: {validation_message}"
                )
            
            # 2. Create order record
            order_id = self.order_manager.create_order(order_request)
            
            # 3. Route to best exchange
            if not order_request.exchange:
                order_request.exchange = self._route_order(order_request)
            
            # 4. Execute order via exchange connector
            execution_result = self._execute_order(order_request, order_id)
            
            # 5. Update order status
            if execution_result.success:
                self.order_manager.update_order_status(
                    order_id,
                    OrderStatus.FILLED if execution_result.filled_quantity == order_request.quantity else OrderStatus.PARTIALLY_FILLED,
                    execution_result.filled_quantity,
                    execution_result.avg_fill_price,
                    execution_result.exchange_order_id
                )
                
                # 6. Update positions
                if execution_result.filled_quantity > 0:
                    self._record_trade_execution(order_request, execution_result, order_id)
            else:
                self.order_manager.update_order_status(order_id, OrderStatus.REJECTED)
            
            # Track performance
            execution_time_ms = (time.time() - start_time) * 1000
            self.order_latency_ms.append(execution_time_ms)
            
            logger.info(f"Order execution completed in {execution_time_ms:.2f}ms")
            
            return OrderResult(
                success=execution_result.success,
                order_id=order_id,
                exchange_order_id=execution_result.exchange_order_id,
                message=execution_result.message,
                filled_quantity=execution_result.filled_quantity,
                avg_fill_price=execution_result.avg_fill_price,
                commission=execution_result.commission,
                commission_asset=execution_result.commission_asset
            )
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return OrderResult(
                success=False,
                message=f"Order execution error: {e}"
            )
    
    def _route_order(self, order_request: OrderRequest) -> str:
        """Smart order routing to select best exchange"""
        # Simplified routing - in production would consider:
        # - Liquidity depth
        # - Fees (maker/taker rates)
        # - Current spread
        # - Available balance
        
        # For now, prefer Binance for liquidity
        if "binance" in self.exchanges:
            return "binance"
        return self.exchanges[0]
    
    def _execute_order(self, order_request: OrderRequest, order_id: str) -> OrderResult:
        """Execute order via exchange connector"""
        try:
            # Get exchange connector
            connector = self._get_connector(order_request.exchange)
            
            # For now, simulate execution
            # In production, would call connector's place_order method
            return self._simulate_order_execution(order_request)
            
        except Exception as e:
            logger.error(f"Error executing order on {order_request.exchange}: {e}")
            return OrderResult(
                success=False,
                message=f"Exchange execution error: {e}"
            )
    
    def _simulate_order_execution(self, order_request: OrderRequest) -> OrderResult:
        """Simulate order execution for testing"""
        # Simulate realistic execution
        filled_quantity = order_request.quantity
        
        # Get current market price (simulated)
        if order_request.order_type == OrderType.MARKET:
            # Market order - fill at "current" price with small slippage
            base_price = Decimal("45000") if "BTC" in order_request.symbol else Decimal("3000")
            slippage = Decimal("0.001")  # 0.1% slippage
            if order_request.side == OrderSide.BUY:
                fill_price = base_price * (1 + slippage)
            else:
                fill_price = base_price * (1 - slippage)
        else:
            # Limit order - fill at limit price
            fill_price = order_request.price
        
        # Calculate commission (0.1% for simulation)
        commission = filled_quantity * fill_price * Decimal("0.001")
        
        return OrderResult(
            success=True,
            exchange_order_id=f"SIM_{int(time.time() * 1000)}",
            message="Order executed successfully (simulated)",
            filled_quantity=filled_quantity,
            avg_fill_price=fill_price,
            commission=commission,
            commission_asset="USDT"
        )
    
    def _record_trade_execution(self, order_request: OrderRequest, 
                              execution_result: OrderResult, order_id: str):
        """Record trade execution and update positions"""
        # Create trade record
        trade = TradingTrade(
            id=str(uuid.uuid4()),
            order_id=order_id,
            symbol=order_request.symbol,
            exchange=order_request.exchange,
            side=order_request.side.value,
            quantity=execution_result.filled_quantity,
            price=execution_result.avg_fill_price,
            notional_value=execution_result.filled_quantity * execution_result.avg_fill_price,
            commission=execution_result.commission,
            commission_asset=execution_result.commission_asset,
            is_maker=False  # Simplified
        )
        
        # Save trade to database
        with get_db_session(provider="zvt", data_schema=TradingTrade) as session:
            session.add(trade)
            session.commit()
        
        # Update position
        self.position_manager.update_position_from_trade(trade)
        
        logger.info(f"Recorded trade: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price}")
    
    def _get_connector(self, exchange: str):
        """Get exchange connector (lazy loading)"""
        if exchange not in self._connectors:
            try:
                from zvt.services.crypto.connectors import (
                    BinanceConnector, OKXConnector, BybitConnector, 
                    CoinbaseConnector, MockCryptoConnector
                )
                
                connector_map = {
                    "binance": BinanceConnector,
                    "okx": OKXConnector,
                    "bybit": BybitConnector,
                    "coinbase": CoinbaseConnector
                }
                
                if exchange in connector_map:
                    self._connectors[exchange] = connector_map[exchange](testnet=True)
                else:
                    self._connectors[exchange] = MockCryptoConnector(exchange_name=exchange)
                    
            except ImportError:
                # Fallback to mock connector
                from zvt.services.crypto.connectors import MockCryptoConnector
                self._connectors[exchange] = MockCryptoConnector(exchange_name=exchange)
        
        return self._connectors[exchange]
    
    def get_positions(self, portfolio_id: str = "default") -> List[PositionInfo]:
        """Get current positions"""
        return self.position_manager.get_positions(portfolio_id)
    
    def get_portfolio_summary(self, portfolio_id: str = "default") -> PortfolioSummary:
        """Get portfolio summary with current values"""
        positions = self.get_positions(portfolio_id)
        
        # Calculate portfolio metrics
        total_value = sum(pos.market_value for pos in positions)
        invested_value = sum(pos.cost_basis for pos in positions)
        daily_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_return = total_value - invested_value
        total_return_pct = float(total_return / invested_value * 100) if invested_value > 0 else 0.0
        
        return PortfolioSummary(
            portfolio_id=portfolio_id,
            total_value=total_value,
            cash_balance=Decimal("10000"),  # Simplified
            invested_value=invested_value,
            daily_pnl=daily_pnl,
            total_return=total_return,
            total_return_pct=total_return_pct,
            positions=positions
        )
    
    def get_order_status(self, order_id: str) -> Optional[CryptoOrder]:
        """Get order status by ID"""
        return self.order_manager.get_order(order_id)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        try:
            order = self.order_manager.get_order(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found")
                return False
            
            if order.status in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value]:
                logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
                return False
            
            # Update order status to cancelled
            self.order_manager.update_order_status(order_id, OrderStatus.CANCELLED)
            
            # TODO: Cancel on exchange if submitted
            
            logger.info(f"Cancelled order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict:
        """Get trading engine performance metrics"""
        return {
            "avg_order_latency_ms": sum(self.order_latency_ms) / len(self.order_latency_ms) if self.order_latency_ms else 0,
            "total_orders": len(self.order_latency_ms),
            "is_running": self.is_running,
            "exchanges": self.exchanges,
            "last_update": datetime.utcnow().isoformat()
        }


# Convenience functions for direct trading operations
def buy_crypto(symbol: str, quantity: Union[float, Decimal], 
               exchange: str = None, portfolio_id: str = "default",
               order_type: OrderType = OrderType.MARKET,
               price: Union[float, Decimal] = None) -> OrderResult:
    """
    Buy cryptocurrency - replacement for empty buy_stocks() function
    """
    # Get or create trading engine instance
    engine = CryptoTradingEngine()
    
    order_request = OrderRequest(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=order_type,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)) if price else None,
        exchange=exchange,
        portfolio_id=portfolio_id,
        strategy_id="manual"
    )
    
    return engine.place_order(order_request)


def sell_crypto(symbol: str, quantity: Union[float, Decimal],
                exchange: str = None, portfolio_id: str = "default", 
                order_type: OrderType = OrderType.MARKET,
                price: Union[float, Decimal] = None) -> OrderResult:
    """
    Sell cryptocurrency - replacement for empty sell_stocks() function
    """
    # Get or create trading engine instance
    engine = CryptoTradingEngine()
    
    order_request = OrderRequest(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=order_type,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)) if price else None,
        exchange=exchange,
        portfolio_id=portfolio_id,
        strategy_id="manual"
    )
    
    return engine.place_order(order_request)


# Export main classes and functions
__all__ = [
    "CryptoTradingEngine",
    "OrderRequest",
    "OrderResult", 
    "PositionInfo",
    "PortfolioSummary",
    "OrderManager",
    "PositionManager", 
    "RiskManager",
    "buy_crypto",
    "sell_crypto"
]