# -*- coding: utf-8 -*-
"""
Order Status Tracking and Execution Reporting
Real-time order lifecycle management and execution analytics
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

import pandas as pd
from sqlalchemy.orm import Session

from zvt.contract.api import get_db_session
from zvt.domain.crypto import CryptoOrder, TradingTrade, OrderStatus
from zvt.utils.time_utils import now_pd_timestamp

logger = logging.getLogger(__name__)


@dataclass
class OrderStatusUpdate:
    """Order status update event"""
    order_id: str
    old_status: OrderStatus
    new_status: OrderStatus
    timestamp: datetime
    filled_quantity: float = 0
    avg_fill_price: Optional[float] = None
    remaining_quantity: float = 0
    exchange_order_id: Optional[str] = None
    message: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """Trade execution report"""
    order_id: str
    trade_id: str
    symbol: str
    exchange: str
    side: str
    quantity: float
    price: float
    commission: float
    commission_asset: str
    execution_timestamp: datetime
    is_maker: bool = False
    liquidity_flag: str = ""
    market_impact: Optional[float] = None
    slippage: Optional[float] = None


@dataclass
class OrderPerformanceMetrics:
    """Order execution performance metrics"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    requested_price: Optional[float]
    avg_execution_price: float
    total_commission: float
    execution_time_ms: float
    slippage_bps: Optional[float] = None
    market_impact_bps: Optional[float] = None
    fill_rate: float = 1.0  # Percentage filled
    venue_breakdown: Dict[str, float] = field(default_factory=dict)


class OrderTracker:
    """
    Tracks order lifecycle and generates execution reports
    Provides real-time order status monitoring and performance analytics
    """
    
    def __init__(self, trading_engine=None):
        self.trading_engine = trading_engine
        self.active_orders: Dict[str, CryptoOrder] = {}
        self.order_history: Dict[str, List[OrderStatusUpdate]] = {}
        self.execution_reports: List[ExecutionReport] = []
        
        # Event handlers
        self.status_update_handlers: List[Callable] = []
        self.execution_handlers: List[Callable] = []
        
        # Performance tracking
        self.performance_metrics: Dict[str, OrderPerformanceMetrics] = {}
        self.daily_stats = {
            "total_orders": 0,
            "successful_orders": 0,
            "cancelled_orders": 0,
            "rejected_orders": 0,
            "avg_execution_time_ms": 0,
            "total_volume": 0,
            "total_commission": 0
        }
        
        logger.info("OrderTracker initialized")
    
    def register_order(self, order: CryptoOrder):
        """Register a new order for tracking"""
        order_id = order.id
        self.active_orders[order_id] = order
        self.order_history[order_id] = []
        
        # Create initial status update
        initial_update = OrderStatusUpdate(
            order_id=order_id,
            old_status=None,
            new_status=OrderStatus(order.status),
            timestamp=order.created_timestamp or datetime.utcnow(),
            message="Order registered for tracking"
        )
        
        self.order_history[order_id].append(initial_update)
        self._notify_status_handlers(initial_update)
        
        logger.info(f"Registered order {order_id} for tracking: {order.symbol} {order.side} {order.quantity}")
    
    def update_order_status(self, order_id: str, new_status: OrderStatus,
                          filled_quantity: float = 0,
                          avg_fill_price: Optional[float] = None,
                          remaining_quantity: Optional[float] = None,
                          exchange_order_id: Optional[str] = None,
                          message: str = "",
                          metadata: Dict = None):
        """Update order status and create status update event"""
        
        if order_id not in self.active_orders:
            logger.warning(f"Order {order_id} not found in active orders")
            return
        
        order = self.active_orders[order_id]
        old_status = OrderStatus(order.status)
        
        # Create status update event
        status_update = OrderStatusUpdate(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.utcnow(),
            filled_quantity=filled_quantity,
            avg_fill_price=avg_fill_price,
            remaining_quantity=remaining_quantity or float(order.remaining_quantity or 0),
            exchange_order_id=exchange_order_id,
            message=message,
            metadata=metadata or {}
        )
        
        # Update order record
        order.status = new_status.value
        order.filled_quantity = filled_quantity
        order.avg_fill_price = avg_fill_price
        order.remaining_quantity = remaining_quantity
        if exchange_order_id:
            order.exchange_order_id = exchange_order_id
        
        # Update timestamps
        if new_status == OrderStatus.SUBMITTED:
            order.submitted_timestamp = datetime.utcnow()
        elif new_status == OrderStatus.FILLED:
            order.filled_timestamp = datetime.utcnow()
        elif new_status == OrderStatus.CANCELLED:
            order.cancelled_timestamp = datetime.utcnow()
        
        # Store status update
        self.order_history[order_id].append(status_update)
        
        # Update daily stats
        self._update_daily_stats(order, old_status, new_status)
        
        # Notify handlers
        self._notify_status_handlers(status_update)
        
        # Move to completed if order is terminal
        if new_status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            self._finalize_order(order_id)
        
        logger.info(f"Updated order {order_id} status: {old_status.value} -> {new_status.value}")
    
    def record_trade_execution(self, trade: TradingTrade, market_data: Dict = None):
        """Record trade execution and generate execution report"""
        
        # Create execution report
        execution_report = ExecutionReport(
            order_id=trade.order_id,
            trade_id=trade.id,
            symbol=trade.symbol,
            exchange=trade.exchange,
            side=trade.side,
            quantity=float(trade.quantity),
            price=float(trade.price),
            commission=float(trade.commission or 0),
            commission_asset=trade.commission_asset or "",
            execution_timestamp=trade.execution_timestamp or datetime.utcnow(),
            is_maker=trade.is_maker or False,
            liquidity_flag=trade.liquidity_flag or ""
        )
        
        # Calculate market impact and slippage if market data provided
        if market_data:
            execution_report.market_impact = self._calculate_market_impact(trade, market_data)
            execution_report.slippage = self._calculate_slippage(trade, market_data)
        
        self.execution_reports.append(execution_report)
        
        # Update performance metrics
        self._update_performance_metrics(trade.order_id, execution_report)
        
        # Notify execution handlers
        self._notify_execution_handlers(execution_report)
        
        logger.info(f"Recorded execution: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price}")
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get current order status and history"""
        if order_id not in self.order_history:
            return None
        
        order = self.active_orders.get(order_id)
        if not order:
            # Try to load from database
            with get_db_session(provider="zvt", data_schema=CryptoOrder) as session:
                order = session.query(CryptoOrder).filter_by(id=order_id).first()
        
        if not order:
            return None
        
        history = self.order_history[order_id]
        current_status = history[-1] if history else None
        
        return {
            "order_id": order_id,
            "symbol": order.symbol,
            "exchange": order.exchange,
            "side": order.side,
            "order_type": order.order_type,
            "quantity": float(order.quantity),
            "price": float(order.price) if order.price else None,
            "current_status": current_status.new_status.value if current_status else order.status,
            "filled_quantity": float(order.filled_quantity or 0),
            "remaining_quantity": float(order.remaining_quantity or 0),
            "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
            "commission": float(order.commission or 0),
            "created_timestamp": order.created_timestamp.isoformat() if order.created_timestamp else None,
            "updated_timestamp": current_status.timestamp.isoformat() if current_status else None,
            "exchange_order_id": order.exchange_order_id,
            "status_history": [
                {
                    "status": update.new_status.value,
                    "timestamp": update.timestamp.isoformat(),
                    "message": update.message,
                    "filled_quantity": update.filled_quantity,
                    "avg_fill_price": update.avg_fill_price
                }
                for update in history
            ]
        }
    
    def get_execution_reports(self, order_id: Optional[str] = None, 
                            symbol: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[Dict]:
        """Get execution reports with optional filtering"""
        
        reports = self.execution_reports
        
        # Apply filters
        if order_id:
            reports = [r for r in reports if r.order_id == order_id]
        if symbol:
            reports = [r for r in reports if r.symbol == symbol]
        if start_date:
            reports = [r for r in reports if r.execution_timestamp >= start_date]
        if end_date:
            reports = [r for r in reports if r.execution_timestamp <= end_date]
        
        # Convert to dictionaries
        return [
            {
                "order_id": report.order_id,
                "trade_id": report.trade_id,
                "symbol": report.symbol,
                "exchange": report.exchange,
                "side": report.side,
                "quantity": report.quantity,
                "price": report.price,
                "commission": report.commission,
                "commission_asset": report.commission_asset,
                "execution_timestamp": report.execution_timestamp.isoformat(),
                "is_maker": report.is_maker,
                "market_impact": report.market_impact,
                "slippage": report.slippage,
                "liquidity_flag": report.liquidity_flag
            }
            for report in reports
        ]
    
    def get_performance_metrics(self, order_id: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """Get order execution performance metrics"""
        
        if order_id:
            metrics = self.performance_metrics.get(order_id)
            if not metrics:
                return None
            
            return {
                "order_id": metrics.order_id,
                "symbol": metrics.symbol,
                "side": metrics.side,
                "order_type": metrics.order_type,
                "quantity": metrics.quantity,
                "requested_price": metrics.requested_price,
                "avg_execution_price": metrics.avg_execution_price,
                "total_commission": metrics.total_commission,
                "execution_time_ms": metrics.execution_time_ms,
                "slippage_bps": metrics.slippage_bps,
                "market_impact_bps": metrics.market_impact_bps,
                "fill_rate": metrics.fill_rate,
                "venue_breakdown": metrics.venue_breakdown
            }
        else:
            # Return all metrics
            return [
                {
                    "order_id": metrics.order_id,
                    "symbol": metrics.symbol,
                    "side": metrics.side,
                    "avg_execution_price": metrics.avg_execution_price,
                    "execution_time_ms": metrics.execution_time_ms,
                    "slippage_bps": metrics.slippage_bps,
                    "fill_rate": metrics.fill_rate
                }
                for metrics in self.performance_metrics.values()
            ]
    
    def get_daily_statistics(self, date: Optional[datetime] = None) -> Dict:
        """Get daily trading statistics"""
        # For now, return current daily stats
        # In production, would filter by date and calculate from database
        
        stats = self.daily_stats.copy()
        
        # Calculate derived metrics
        if stats["total_orders"] > 0:
            stats["success_rate"] = stats["successful_orders"] / stats["total_orders"]
            stats["cancellation_rate"] = stats["cancelled_orders"] / stats["total_orders"]
            stats["rejection_rate"] = stats["rejected_orders"] / stats["total_orders"]
        else:
            stats["success_rate"] = 0
            stats["cancellation_rate"] = 0
            stats["rejection_rate"] = 0
        
        # Add aggregated performance metrics
        if self.performance_metrics:
            execution_times = [m.execution_time_ms for m in self.performance_metrics.values()]
            slippages = [m.slippage_bps for m in self.performance_metrics.values() if m.slippage_bps is not None]
            
            stats["avg_execution_time_ms"] = sum(execution_times) / len(execution_times) if execution_times else 0
            stats["p95_execution_time_ms"] = sorted(execution_times)[int(0.95 * len(execution_times))] if execution_times else 0
            stats["avg_slippage_bps"] = sum(slippages) / len(slippages) if slippages else 0
        
        return stats
    
    def add_status_update_handler(self, handler: Callable[[OrderStatusUpdate], None]):
        """Add handler for order status updates"""
        self.status_update_handlers.append(handler)
        logger.info("Added order status update handler")
    
    def add_execution_handler(self, handler: Callable[[ExecutionReport], None]):
        """Add handler for trade executions"""
        self.execution_handlers.append(handler)
        logger.info("Added trade execution handler")
    
    def _notify_status_handlers(self, status_update: OrderStatusUpdate):
        """Notify all status update handlers"""
        for handler in self.status_update_handlers:
            try:
                handler(status_update)
            except Exception as e:
                logger.error(f"Error in status update handler: {e}")
    
    def _notify_execution_handlers(self, execution_report: ExecutionReport):
        """Notify all execution handlers"""
        for handler in self.execution_handlers:
            try:
                handler(execution_report)
            except Exception as e:
                logger.error(f"Error in execution handler: {e}")
    
    def _finalize_order(self, order_id: str):
        """Finalize order when it reaches terminal status"""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            
            # Calculate final performance metrics
            self._calculate_final_metrics(order_id)
            
            # Remove from active orders (keep in history)
            del self.active_orders[order_id]
            
            logger.info(f"Finalized order {order_id}")
    
    def _update_daily_stats(self, order: CryptoOrder, old_status: OrderStatus, new_status: OrderStatus):
        """Update daily statistics based on status change"""
        
        # Increment counters on first status change from PENDING
        if old_status == OrderStatus.PENDING and new_status != OrderStatus.PENDING:
            self.daily_stats["total_orders"] += 1
        
        # Track terminal states
        if new_status == OrderStatus.FILLED:
            self.daily_stats["successful_orders"] += 1
            self.daily_stats["total_volume"] += float(order.quantity * (order.avg_fill_price or 0))
        elif new_status == OrderStatus.CANCELLED:
            self.daily_stats["cancelled_orders"] += 1
        elif new_status == OrderStatus.REJECTED:
            self.daily_stats["rejected_orders"] += 1
    
    def _update_performance_metrics(self, order_id: str, execution_report: ExecutionReport):
        """Update performance metrics for an order"""
        
        if order_id not in self.performance_metrics:
            # Get order details
            order = self.active_orders.get(order_id)
            if not order:
                return
            
            # Initialize performance metrics
            self.performance_metrics[order_id] = OrderPerformanceMetrics(
                order_id=order_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=float(order.quantity),
                requested_price=float(order.price) if order.price else None,
                avg_execution_price=execution_report.price,
                total_commission=execution_report.commission,
                execution_time_ms=0,  # Will be calculated on finalization
                venue_breakdown={execution_report.exchange: execution_report.quantity}
            )
        else:
            # Update existing metrics
            metrics = self.performance_metrics[order_id]
            
            # Update weighted average execution price
            total_qty = sum(metrics.venue_breakdown.values()) + execution_report.quantity
            metrics.avg_execution_price = (
                (metrics.avg_execution_price * sum(metrics.venue_breakdown.values()) + 
                 execution_report.price * execution_report.quantity) / total_qty
            )
            
            # Update commission
            metrics.total_commission += execution_report.commission
            
            # Update venue breakdown
            if execution_report.exchange in metrics.venue_breakdown:
                metrics.venue_breakdown[execution_report.exchange] += execution_report.quantity
            else:
                metrics.venue_breakdown[execution_report.exchange] = execution_report.quantity
    
    def _calculate_market_impact(self, trade: TradingTrade, market_data: Dict) -> Optional[float]:
        """Calculate market impact of the trade"""
        # Simplified market impact calculation
        # In production, would use more sophisticated models
        
        if "mid_price_before" in market_data and "mid_price_after" in market_data:
            mid_before = market_data["mid_price_before"]
            mid_after = market_data["mid_price_after"]
            
            if trade.side.upper() == "BUY":
                impact = (mid_after - mid_before) / mid_before * 10000  # basis points
            else:
                impact = (mid_before - mid_after) / mid_before * 10000  # basis points
            
            return impact
        
        return None
    
    def _calculate_slippage(self, trade: TradingTrade, market_data: Dict) -> Optional[float]:
        """Calculate slippage relative to benchmark price"""
        
        if "benchmark_price" in market_data:
            benchmark = market_data["benchmark_price"]
            execution_price = float(trade.price)
            
            if trade.side.upper() == "BUY":
                slippage = (execution_price - benchmark) / benchmark * 10000  # basis points
            else:
                slippage = (benchmark - execution_price) / benchmark * 10000  # basis points
            
            return slippage
        
        return None
    
    def _calculate_final_metrics(self, order_id: str):
        """Calculate final performance metrics when order is complete"""
        
        if order_id not in self.performance_metrics:
            return
        
        metrics = self.performance_metrics[order_id]
        order_history = self.order_history.get(order_id, [])
        
        if len(order_history) >= 2:
            # Calculate execution time from first to last status update
            start_time = order_history[0].timestamp
            end_time = order_history[-1].timestamp
            metrics.execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Calculate fill rate
        total_executed = sum(metrics.venue_breakdown.values())
        metrics.fill_rate = total_executed / metrics.quantity if metrics.quantity > 0 else 0
        
        # Calculate slippage if we have both requested and executed prices
        if metrics.requested_price and metrics.avg_execution_price:
            if metrics.side.upper() == "BUY":
                metrics.slippage_bps = (metrics.avg_execution_price - metrics.requested_price) / metrics.requested_price * 10000
            else:
                metrics.slippage_bps = (metrics.requested_price - metrics.avg_execution_price) / metrics.requested_price * 10000


# Export main classes
__all__ = [
    "OrderTracker",
    "OrderStatusUpdate",
    "ExecutionReport", 
    "OrderPerformanceMetrics"
]