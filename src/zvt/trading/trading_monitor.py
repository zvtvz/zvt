# -*- coding: utf-8 -*-
"""
Trading Engine Monitoring and Performance Metrics
Real-time monitoring, alerting, and performance analytics for the trading system
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import json
import threading

import pandas as pd
import numpy as np

from zvt.utils.time_utils import now_pd_timestamp

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """Trading system alert"""
    alert_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    message: str
    timestamp: datetime
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # HEALTHY, DEGRADED, CRITICAL
    uptime_seconds: float
    cpu_usage_pct: float
    memory_usage_pct: float
    active_orders: int
    orders_per_second: float
    error_rate_pct: float
    avg_latency_ms: float
    last_update: datetime


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=retention_hours * 3600))  # 1 point per second
        self.aggregated_metrics: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        
        # Start background aggregation
        self.aggregation_thread = threading.Thread(target=self._aggregation_loop, daemon=True)
        self.aggregation_thread.start()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        with self.lock:
            self.metrics[name].append(metric)
        
        # Update real-time aggregation
        self._update_realtime_aggregation(name, value)
    
    def get_metrics(self, name: str, start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics within time range"""
        with self.lock:
            metrics = list(self.metrics[name])
        
        if start_time or end_time:
            filtered = []
            for metric in metrics:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                filtered.append(metric)
            return filtered
        
        return metrics
    
    def get_aggregated_metrics(self, name: str, window_minutes: int = 5) -> Dict:
        """Get aggregated metrics for a time window"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_minutes)
        
        metrics = self.get_metrics(name, start_time, end_time)
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "p50": np.percentile(values, 50),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
            "std": np.std(values),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def _update_realtime_aggregation(self, name: str, value: float):
        """Update real-time aggregated metrics"""
        if name not in self.aggregated_metrics:
            self.aggregated_metrics[name] = {
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "last_value": value,
                "last_update": datetime.utcnow()
            }
        
        agg = self.aggregated_metrics[name]
        agg["count"] += 1
        agg["sum"] += value
        agg["min"] = min(agg["min"], value)
        agg["max"] = max(agg["max"], value)
        agg["last_value"] = value
        agg["last_update"] = datetime.utcnow()
    
    def _aggregation_loop(self):
        """Background thread for periodic aggregation"""
        while True:
            try:
                time.sleep(60)  # Aggregate every minute
                self._cleanup_old_metrics()
            except Exception as e:
                logger.error(f"Error in metrics aggregation loop: {e}")
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        with self.lock:
            for name, metrics in self.metrics.items():
                # Remove old metrics
                while metrics and metrics[0].timestamp < cutoff_time:
                    metrics.popleft()


class AlertManager:
    """Manages trading system alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_rules: List[Dict] = []
        self.lock = threading.RLock()
        
        # Configure default alert rules
        self._setup_default_rules()
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert notification handler"""
        self.alert_handlers.append(handler)
        logger.info("Added alert handler")
    
    def create_alert(self, severity: str, title: str, message: str, 
                    source: str = "trading_engine", tags: Dict[str, str] = None) -> str:
        """Create a new alert"""
        alert_id = f"alert_{int(time.time() * 1000)}"
        
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            source=source,
            tags=tags or {}
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        # Notify handlers
        self._notify_handlers(alert)
        
        logger.warning(f"Created {severity} alert: {title}")
        return alert_id
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_timestamp = datetime.utcnow()
                    logger.info(f"Resolved alert {alert_id}")
                    return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        with self.lock:
            active = [a for a in self.alerts if not a.resolved]
            
            if severity:
                active = [a for a in active if a.severity == severity]
            
            return sorted(active, key=lambda x: x.timestamp, reverse=True)
    
    def check_alert_rules(self, metrics: Dict[str, float]):
        """Check metrics against alert rules and create alerts if needed"""
        for rule in self.alert_rules:
            try:
                self._evaluate_rule(rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.get('name', 'unknown')}: {e}")
    
    def _setup_default_rules(self):
        """Set up default alerting rules"""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "metric": "error_rate_pct",
                "condition": "greater_than",
                "threshold": 5.0,
                "severity": "HIGH",
                "title": "High Error Rate",
                "message": "Error rate exceeded 5%"
            },
            {
                "name": "high_latency", 
                "metric": "avg_latency_ms",
                "condition": "greater_than",
                "threshold": 100.0,
                "severity": "MEDIUM",
                "title": "High Latency",
                "message": "Average latency exceeded 100ms"
            },
            {
                "name": "low_order_rate",
                "metric": "orders_per_second",
                "condition": "less_than", 
                "threshold": 0.1,
                "severity": "LOW",
                "title": "Low Order Rate",
                "message": "Order rate dropped below 0.1 orders/second"
            },
            {
                "name": "critical_latency",
                "metric": "avg_latency_ms", 
                "condition": "greater_than",
                "threshold": 500.0,
                "severity": "CRITICAL",
                "title": "Critical Latency",
                "message": "Average latency exceeded 500ms - system severely degraded"
            }
        ]
    
    def _evaluate_rule(self, rule: Dict, metrics: Dict[str, float]):
        """Evaluate a single alert rule"""
        metric_name = rule["metric"]
        condition = rule["condition"]
        threshold = rule["threshold"]
        
        if metric_name not in metrics:
            return
        
        value = metrics[metric_name]
        triggered = False
        
        if condition == "greater_than" and value > threshold:
            triggered = True
        elif condition == "less_than" and value < threshold:
            triggered = True
        elif condition == "equals" and value == threshold:
            triggered = True
        
        if triggered:
            # Check if we already have an active alert for this rule
            active_alerts = self.get_active_alerts()
            rule_alerts = [a for a in active_alerts if a.tags.get("rule_name") == rule["name"]]
            
            if not rule_alerts:  # Only create if no active alert exists
                self.create_alert(
                    severity=rule["severity"],
                    title=rule["title"],
                    message=f"{rule['message']} (current value: {value}, threshold: {threshold})",
                    tags={"rule_name": rule["name"], "metric": metric_name}
                )
    
    def _notify_handlers(self, alert: Alert):
        """Notify all alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")


class TradingMonitor:
    """
    Main trading system monitor
    Collects metrics, manages alerts, and provides system health status
    """
    
    def __init__(self, trading_engine=None):
        self.trading_engine = trading_engine
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        # System state
        self.start_time = datetime.utcnow()
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Performance tracking
        self.order_latencies = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.last_metrics_update = datetime.utcnow()
        
        # Health status
        self.system_health = SystemHealth(
            status="HEALTHY",
            uptime_seconds=0,
            cpu_usage_pct=0,
            memory_usage_pct=0,
            active_orders=0,
            orders_per_second=0,
            error_rate_pct=0,
            avg_latency_ms=0,
            last_update=datetime.utcnow()
        )
        
        logger.info("TradingMonitor initialized")
    
    def start_monitoring(self):
        """Start monitoring the trading system"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Trading monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Trading monitoring stopped")
    
    def record_order_latency(self, latency_ms: float, order_type: str = ""):
        """Record order execution latency"""
        self.order_latencies.append(latency_ms)
        self.metrics_collector.record_metric(
            "order_latency_ms", 
            latency_ms, 
            tags={"order_type": order_type},
            unit="ms"
        )
    
    def record_order_event(self, event_type: str, symbol: str = "", exchange: str = ""):
        """Record order-related events"""
        self.metrics_collector.record_metric(
            f"order_{event_type}_count",
            1,
            tags={"symbol": symbol, "exchange": exchange}
        )
    
    def record_error(self, error_type: str, error_message: str = ""):
        """Record system errors"""
        self.error_counts[error_type] += 1
        self.metrics_collector.record_metric(
            "error_count",
            1,
            tags={"error_type": error_type}
        )
        
        # Create alert for critical errors
        if error_type in ["exchange_connection_failed", "database_error", "order_rejection"]:
            self.alert_manager.create_alert(
                severity="HIGH",
                title=f"System Error: {error_type}",
                message=error_message or f"Error of type {error_type} occurred",
                tags={"error_type": error_type}
            )
    
    def record_trade_execution(self, symbol: str, quantity: float, price: float, 
                             exchange: str, side: str, commission: float = 0):
        """Record successful trade execution"""
        notional_value = quantity * price
        
        self.metrics_collector.record_metric("trade_volume", notional_value, 
                                           tags={"symbol": symbol, "exchange": exchange, "side": side})
        self.metrics_collector.record_metric("trade_count", 1,
                                           tags={"symbol": symbol, "exchange": exchange, "side": side})
        self.metrics_collector.record_metric("commission_paid", commission,
                                           tags={"exchange": exchange})
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        self._update_system_health()
        return self.system_health
    
    def get_performance_dashboard(self) -> Dict:
        """Get comprehensive performance dashboard data"""
        now = datetime.utcnow()
        
        # Get key metrics for the last hour
        latency_stats = self.metrics_collector.get_aggregated_metrics("order_latency_ms", 60)
        trade_volume = self.metrics_collector.get_aggregated_metrics("trade_volume", 60)
        error_stats = self.metrics_collector.get_aggregated_metrics("error_count", 60)
        
        # Active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Order statistics
        order_metrics = {}
        for event_type in ["placed", "filled", "cancelled", "rejected"]:
            metric_name = f"order_{event_type}_count"
            stats = self.metrics_collector.get_aggregated_metrics(metric_name, 60)
            order_metrics[event_type] = stats.get("count", 0)
        
        return {
            "timestamp": now.isoformat(),
            "system_health": {
                "status": self.system_health.status,
                "uptime_hours": round(self.system_health.uptime_seconds / 3600, 2),
                "active_orders": self.system_health.active_orders,
                "orders_per_second": round(self.system_health.orders_per_second, 2),
                "error_rate_pct": round(self.system_health.error_rate_pct, 2),
                "avg_latency_ms": round(self.system_health.avg_latency_ms, 2)
            },
            "performance": {
                "latency": latency_stats,
                "trade_volume": trade_volume,
                "error_rate": error_stats
            },
            "orders": order_metrics,
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len([a for a in active_alerts if a.severity == "CRITICAL"]),
                "high_count": len([a for a in active_alerts if a.severity == "HIGH"]),
                "recent_alerts": [
                    {
                        "severity": alert.severity,
                        "title": alert.title,
                        "timestamp": alert.timestamp.isoformat(),
                        "source": alert.source
                    }
                    for alert in active_alerts[:5]  # Last 5 alerts
                ]
            },
            "exchanges": self._get_exchange_status(),
            "top_symbols": self._get_top_trading_symbols()
        }
    
    def get_alerts(self, severity: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get system alerts"""
        alerts = self.alert_manager.get_active_alerts(severity)[:limit]
        
        return [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "tags": alert.tags,
                "resolved": alert.resolved
            }
            for alert in alerts
        ]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID"""
        return self.alert_manager.resolve_alert(alert_id)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add custom alert handler"""
        self.alert_manager.add_alert_handler(handler)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._collect_system_metrics()
                self._update_system_health()
                self._check_alerts()
                time.sleep(5)  # Monitor every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Back off on error
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        now = datetime.utcnow()
        
        # System uptime
        uptime_seconds = (now - self.start_time).total_seconds()
        self.metrics_collector.record_metric("uptime_seconds", uptime_seconds)
        
        # Order latency metrics
        if self.order_latencies:
            avg_latency = sum(self.order_latencies) / len(self.order_latencies)
            self.metrics_collector.record_metric("avg_latency_ms", avg_latency)
        
        # Order rate (orders per second)
        recent_orders = self.metrics_collector.get_aggregated_metrics("order_placed_count", 1)
        orders_per_second = recent_orders.get("count", 0) / 60.0  # Per minute to per second
        self.metrics_collector.record_metric("orders_per_second", orders_per_second)
        
        # Error rate
        recent_errors = self.metrics_collector.get_aggregated_metrics("error_count", 5)
        recent_orders_5min = self.metrics_collector.get_aggregated_metrics("order_placed_count", 5)
        
        total_operations = recent_orders_5min.get("count", 0)
        total_errors = recent_errors.get("count", 0)
        error_rate_pct = (total_errors / max(total_operations, 1)) * 100
        self.metrics_collector.record_metric("error_rate_pct", error_rate_pct)
        
        # Trading engine specific metrics
        if self.trading_engine:
            active_orders = len(self.trading_engine.order_manager.pending_orders)
            self.metrics_collector.record_metric("active_orders", active_orders)
        
        self.last_metrics_update = now
    
    def _update_system_health(self):
        """Update system health status"""
        now = datetime.utcnow()
        
        # Get recent metrics
        latency_stats = self.metrics_collector.get_aggregated_metrics("avg_latency_ms", 5)
        error_stats = self.metrics_collector.get_aggregated_metrics("error_rate_pct", 5)
        order_stats = self.metrics_collector.get_aggregated_metrics("orders_per_second", 1)
        
        # Update health object
        self.system_health.uptime_seconds = (now - self.start_time).total_seconds()
        self.system_health.avg_latency_ms = latency_stats.get("mean", 0)
        self.system_health.error_rate_pct = error_stats.get("mean", 0)
        self.system_health.orders_per_second = order_stats.get("mean", 0)
        self.system_health.last_update = now
        
        if self.trading_engine:
            self.system_health.active_orders = len(self.trading_engine.order_manager.pending_orders)
        
        # Determine overall health status
        if self.system_health.error_rate_pct > 10 or self.system_health.avg_latency_ms > 500:
            self.system_health.status = "CRITICAL"
        elif self.system_health.error_rate_pct > 5 or self.system_health.avg_latency_ms > 200:
            self.system_health.status = "DEGRADED"
        else:
            self.system_health.status = "HEALTHY"
    
    def _check_alerts(self):
        """Check current metrics against alert rules"""
        current_metrics = {
            "avg_latency_ms": self.system_health.avg_latency_ms,
            "error_rate_pct": self.system_health.error_rate_pct,
            "orders_per_second": self.system_health.orders_per_second,
            "active_orders": self.system_health.active_orders
        }
        
        self.alert_manager.check_alert_rules(current_metrics)
    
    def _get_exchange_status(self) -> Dict:
        """Get status of connected exchanges"""
        # Placeholder - would integrate with exchange connectors
        exchanges = ["binance", "okx", "bybit", "coinbase"]
        
        status = {}
        for exchange in exchanges:
            # Get recent metrics for this exchange
            volume_stats = self.metrics_collector.get_aggregated_metrics("trade_volume", 60)
            status[exchange] = {
                "status": "connected",  # Would check actual connection
                "volume_1h": volume_stats.get("sum", 0),
                "trades_1h": self.metrics_collector.get_aggregated_metrics("trade_count", 60).get("count", 0)
            }
        
        return status
    
    def _get_top_trading_symbols(self) -> List[Dict]:
        """Get most actively traded symbols"""
        # Placeholder - would aggregate by symbol from metrics
        return [
            {"symbol": "BTC/USDT", "volume_1h": 150000, "trades_1h": 45},
            {"symbol": "ETH/USDT", "volume_1h": 85000, "trades_1h": 32},
            {"symbol": "BNB/USDT", "volume_1h": 25000, "trades_1h": 18}
        ]


# Default alert handlers
def console_alert_handler(alert: Alert):
    """Simple console alert handler"""
    print(f"[{alert.severity}] {alert.title}: {alert.message}")


def log_alert_handler(alert: Alert):
    """Log-based alert handler"""
    level = logging.ERROR if alert.severity in ["CRITICAL", "HIGH"] else logging.WARNING
    logger.log(level, f"Alert [{alert.severity}] {alert.title}: {alert.message}")


# Export main classes
__all__ = [
    "TradingMonitor",
    "MetricsCollector",
    "AlertManager", 
    "PerformanceMetric",
    "Alert",
    "SystemHealth",
    "console_alert_handler",
    "log_alert_handler"
]