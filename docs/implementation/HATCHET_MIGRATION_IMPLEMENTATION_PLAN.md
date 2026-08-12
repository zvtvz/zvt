# Hatchet Event-Driven Architecture Migration - Implementation Plan
*Version: 1.0.0*
*Date: August 20, 2025*
*Status: READY FOR IMPLEMENTATION*

## 🚀 **Implementation Overview**

This document provides a **step-by-step implementation plan** for migrating ZVT's current synchronous trading engine (TDD Cycle 1) to an event-driven architecture powered by Hatchet workflow engine. The migration maintains 16/17 test compatibility while enabling 10x scalability and enterprise-grade fault tolerance.

### **Migration Strategy** 🎯
- **Incremental Migration**: Gradual conversion of components to event-driven architecture
- **Test Compatibility**: Maintain 16/17 test success rate throughout migration
- **Performance Targets**: <75ms workflow execution (vs. <50ms current synchronous)
- **Zero Downtime**: Production systems remain operational during migration

---

## 📋 **Phase 1: Foundation Setup (Weeks 1-3)**

### **Week 1: Infrastructure Setup** 🏗️

#### **1.1 Hatchet SDK Installation & Configuration**
```bash
# Install Hatchet SDK
pip install hatchet-sdk

# Install Redis for event bus
pip install redis[hiredis] aioredis

# Install additional dependencies
pip install asyncio-mqtt pydantic-settings python-dotenv
```

#### **1.2 Environment Configuration**
```python
# config/hatchet_config.py
from hatchet_sdk import Hatchet
from pydantic_settings import BaseSettings
from typing import Optional

class HatchetConfig(BaseSettings):
    """Hatchet workflow engine configuration"""
    hatchet_client_tls_strategy: str = "tls"
    hatchet_client_tls_server_name: str = "cluster.hatchet-tools.com"
    hatchet_client_token: str  # From environment
    hatchet_client_tenant_id: str  # From environment
    
    # Local development settings
    hatchet_client_host: Optional[str] = None
    hatchet_client_port: Optional[int] = None
    
    class Config:
        env_file = ".env"

class RedisConfig(BaseSettings):
    """Redis event bus configuration"""
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 100
    redis_retry_on_timeout: bool = True
    redis_socket_timeout: float = 5.0
    
    class Config:
        env_file = ".env"

# Initialize Hatchet client
def create_hatchet_client() -> Hatchet:
    config = HatchetConfig()
    return Hatchet(
        debug=True,  # Enable for development
        config={
            "tls_strategy": config.hatchet_client_tls_strategy,
            "tls_server_name": config.hatchet_client_tls_server_name,
            "token": config.hatchet_client_token,
            "tenant_id": config.hatchet_client_tenant_id,
        }
    )
```

#### **1.3 Event Schema Implementation**
```python
# src/zvt/events/base.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal
import uuid
import json

class EventType(Enum):
    """All event types in the system"""
    # Trading Events
    ORDER_REQUESTED = "order.requested"
    ORDER_VALIDATED = "order.validated"
    ORDER_REJECTED = "order.rejected"
    ORDER_CREATED = "order.created"
    EXCHANGE_ROUTED = "exchange.routed"
    ORDER_EXECUTED = "order.executed"
    ORDER_FAILED = "order.failed"
    POSITION_UPDATED = "position.updated"
    PORTFOLIO_UPDATED = "portfolio.updated"
    
    # Risk Events
    RISK_BREACHED = "risk.breached"
    RISK_ASSESSED = "risk.assessed"
    
    # Market Data Events
    PRICE_UPDATED = "price.updated"
    ORDERBOOK_UPDATED = "orderbook.updated"
    TRADE_TICK = "trade.tick"

@dataclass
class BaseEvent:
    """Base event class with common fields"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = field(default="")  # Workflow ID
    causation_id: str = field(default="")   # Causing event ID
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else "",
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
            "metadata": self.metadata,
            **{k: v for k, v in self.__dict__.items() 
               if k not in ['event_id', 'event_type', 'timestamp', 'correlation_id', 
                           'causation_id', 'version', 'metadata']}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """Deserialize event from dictionary"""
        event_type = EventType(data.pop('event_type'))
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        return cls(
            event_type=event_type,
            timestamp=timestamp,
            **data
        )

# Trading Events
@dataclass  
class OrderRequestedEvent(BaseEvent):
    """Order placement request initiated"""
    event_type: EventType = field(default=EventType.ORDER_REQUESTED, init=False)
    order_request: Dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    strategy_id: Optional[str] = None

@dataclass
class OrderValidatedEvent(BaseEvent):
    """Order passed risk validation"""
    event_type: EventType = field(default=EventType.ORDER_VALIDATED, init=False)
    order_id: str = ""
    validation_result: Dict[str, Any] = field(default_factory=dict)
    risk_score: Decimal = Decimal("0")

@dataclass
class OrderExecutedEvent(BaseEvent):
    """Order successfully executed"""
    event_type: EventType = field(default=EventType.ORDER_EXECUTED, init=False)
    order_id: str = ""
    exchange_order_id: str = ""
    executed_price: Decimal = Decimal("0")
    executed_quantity: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    execution_time_ms: float = 0.0

@dataclass
class PositionUpdatedEvent(BaseEvent):
    """Position updated after trade execution"""
    event_type: EventType = field(default=EventType.POSITION_UPDATED, init=False)
    position_id: str = ""
    symbol: str = ""
    exchange: str = ""
    quantity_change: Decimal = Decimal("0")
    new_quantity: Decimal = Decimal("0")
    new_avg_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
```

### **Week 2: Event Bus Implementation** 🚌

#### **2.1 Redis Streams Event Bus**
```python
# src/zvt/events/event_bus.py
import asyncio
import json
import logging
from typing import Dict, List, Callable, Any
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor

from .base import BaseEvent, EventType

logger = logging.getLogger(__name__)

class EventBus:
    """High-performance event bus using Redis Streams"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: redis.Redis = None
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.consumer_tasks: List[asyncio.Task] = []
        self.event_store = None
        self.service_name = "zvt_trading_engine"
        
    async def initialize(self):
        """Initialize Redis connection and event store"""
        self.redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=100
        )
        self.event_store = EventStore(self.redis)
        
        # Test connection
        await self.redis.ping()
        logger.info("Event bus initialized successfully")
    
    async def publish(self, event: BaseEvent) -> None:
        """Publish event to Redis stream"""
        try:
            # Store event for audit and replay
            await self.event_store.store_event(event)
            
            # Publish to Redis stream
            stream_key = f"events:{event.event_type.value}"
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "data": json.dumps(event.to_dict(), default=str)
            }
            
            message_id = await self.redis.xadd(stream_key, event_data)
            logger.debug(f"Published event {event.event_id} to stream {stream_key}: {message_id}")
            
            # Notify local subscribers
            await self._notify_local_subscribers(event)
            
        except Exception as e:
            logger.error(f"Error publishing event {event.event_id}: {e}")
            raise
    
    async def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to events of specific type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        
        # Start Redis stream consumer for this event type
        stream_key = f"events:{event_type.value}"
        consumer_task = asyncio.create_task(
            self._consume_stream(stream_key, handler)
        )
        self.consumer_tasks.append(consumer_task)
        
        logger.info(f"Subscribed to {event_type.value} events")
    
    async def _notify_local_subscribers(self, event: BaseEvent) -> None:
        """Notify local subscribers immediately"""
        if event.event_type in self.subscribers:
            tasks = []
            for handler in self.subscribers[event.event_type]:
                tasks.append(asyncio.create_task(handler(event)))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _consume_stream(self, stream_key: str, handler: Callable) -> None:
        """Consume events from Redis stream with consumer groups"""
        consumer_group = f"group:{self.service_name}"
        consumer_name = f"consumer:{asyncio.current_task().get_name()}"
        
        # Create consumer group if it doesn't exist
        try:
            await self.redis.xgroup_create(
                stream_key, consumer_group, id="0", mkstream=True
            )
        except redis.RedisError:
            pass  # Group already exists
        
        logger.info(f"Started consumer {consumer_name} for stream {stream_key}")
        
        while True:
            try:
                # Read messages from stream
                messages = await self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_key: ">"},
                    count=10,
                    block=1000  # 1 second timeout
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            # Deserialize event
                            event_data = json.loads(fields["data"])
                            event = self._deserialize_event(event_data)
                            
                            # Process event
                            await handler(event)
                            
                            # Acknowledge message
                            await self.redis.xack(stream_key, consumer_group, msg_id)
                            
                        except Exception as e:
                            logger.error(f"Error processing event {msg_id}: {e}")
                            # TODO: Implement dead letter queue
                            
            except asyncio.CancelledError:
                logger.info(f"Consumer {consumer_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Stream consumer error: {e}")
                await asyncio.sleep(1)
    
    def _deserialize_event(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Deserialize event from stored data"""
        event_type = EventType(event_data["event_type"])
        
        # Import event classes dynamically
        from . import trading_events
        
        event_class_map = {
            EventType.ORDER_REQUESTED: trading_events.OrderRequestedEvent,
            EventType.ORDER_VALIDATED: trading_events.OrderValidatedEvent,
            EventType.ORDER_EXECUTED: trading_events.OrderExecutedEvent,
            EventType.POSITION_UPDATED: trading_events.PositionUpdatedEvent,
            # Add more mappings as needed
        }
        
        event_class = event_class_map.get(event_type, BaseEvent)
        return event_class.from_dict(event_data)
    
    async def close(self) -> None:
        """Close event bus and cleanup resources"""
        # Cancel all consumer tasks
        for task in self.consumer_tasks:
            task.cancel()
        
        if self.consumer_tasks:
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)
        
        # Close Redis connection
        if self.redis:
            await self.redis.close()
        
        logger.info("Event bus closed")

class EventStore:
    """Persistent event storage for audit and replay"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def store_event(self, event: BaseEvent) -> None:
        """Store event permanently for audit trail"""
        try:
            # Store event details
            event_key = f"event_store:{event.event_id}"
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "data": json.dumps(event.to_dict(), default=str),
                "version": event.version
            }
            
            await self.redis.hset(event_key, mapping=event_data)
            
            # Add to correlation stream for workflow tracking
            if event.correlation_id:
                correlation_key = f"correlation:{event.correlation_id}"
                await self.redis.xadd(correlation_key, {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error storing event {event.event_id}: {e}")
            raise
    
    async def get_events_by_correlation(self, correlation_id: str) -> List[BaseEvent]:
        """Get all events for a correlation ID (workflow)"""
        try:
            correlation_key = f"correlation:{correlation_id}"
            events = await self.redis.xrange(correlation_key)
            
            result = []
            for event_id, fields in events:
                event_key = f"event_store:{fields['event_id']}"
                event_data = await self.redis.hgetall(event_key)
                if event_data:
                    result.append(self._deserialize_event(event_data))
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving events for correlation {correlation_id}: {e}")
            return []
```

### **Week 3: Basic Workflow Setup** ⚙️

#### **3.1 First Hatchet Workflow - Order Placement**
```python
# src/zvt/workflows/trading_workflows.py
import asyncio
import time
from decimal import Decimal
from typing import Dict, Any

from hatchet_sdk import Hatchet
from hatchet_sdk.workflow import WorkflowContext

from ..events.base import EventType
from ..events.trading_events import (
    OrderRequestedEvent, OrderValidatedEvent, OrderRejectedEvent,
    OrderCreatedEvent, OrderExecutedEvent, PositionUpdatedEvent
)
from ..events.event_bus import EventBus

# Global Hatchet client (initialized in main)
hatchet: Hatchet = None
event_bus: EventBus = None

def initialize_workflows(hatchet_client: Hatchet, event_bus_instance: EventBus):
    """Initialize workflow dependencies"""
    global hatchet, event_bus
    hatchet = hatchet_client
    event_bus = event_bus_instance

@hatchet.workflow("trading.place_order", timeout="30s")
class PlaceOrderWorkflow:
    """
    Orchestrates the complete order placement lifecycle
    Performance Target: <75ms end-to-end execution
    """
    
    @hatchet.step("validate_request", timeout="5s")
    async def validate_request(self, context: WorkflowContext) -> Dict[str, Any]:
        """Validate order request and emit ORDER_REQUESTED event"""
        start_time = time.perf_counter()
        order_request = context.workflow_input()["order_request"]
        
        # Emit ORDER_REQUESTED event
        await event_bus.publish(OrderRequestedEvent(
            correlation_id=context.workflow_run_id(),
            causation_id=context.workflow_run_id(),
            order_request=order_request,
            user_id=order_request.get("user_id", ""),
            strategy_id=order_request.get("strategy_id")
        ))
        
        # Basic validation
        if not order_request.get("symbol") or not order_request.get("quantity"):
            raise ValueError("Invalid order request: missing symbol or quantity")
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        return {
            "valid": True, 
            "order_request": order_request,
            "validation_time_ms": execution_time_ms
        }
    
    @hatchet.step("check_risk_limits", timeout="10s", retries=3)
    async def check_risk_limits(self, context: WorkflowContext) -> Dict[str, Any]:
        """Comprehensive risk validation with retry logic"""
        start_time = time.perf_counter()
        prev_result = context.step_output("validate_request")
        order_request = prev_result["order_request"]
        
        # Get risk manager service (injected dependency)
        risk_manager = context.additional_metadata.get("risk_manager")
        if not risk_manager:
            # Fallback to legacy synchronous risk manager for compatibility
            from ..trading.crypto_trading_engine import CryptoTradingEngine
            engine = CryptoTradingEngine()
            risk_manager = engine.risk_manager
        
        # Perform risk validation
        try:
            # Convert order_request dict to OrderRequest object for compatibility
            from ..trading.crypto_trading_engine import OrderRequest, OrderSide, OrderType
            order_req_obj = OrderRequest(
                symbol=order_request["symbol"],
                side=OrderSide(order_request["side"]),
                order_type=OrderType(order_request["order_type"]),
                quantity=Decimal(str(order_request["quantity"])),
                price=Decimal(str(order_request.get("price", 0))) if order_request.get("price") else None,
                exchange=order_request.get("exchange"),
                strategy_id=order_request.get("strategy_id"),
                portfolio_id=order_request.get("portfolio_id", "default")
            )
            
            is_valid, validation_message = risk_manager.validate_order(order_req_obj)
            
            # Generate order ID for tracking
            import uuid
            order_id = str(uuid.uuid4())
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            if is_valid:
                await event_bus.publish(OrderValidatedEvent(
                    correlation_id=context.workflow_run_id(),
                    causation_id=context.step_run_id(),
                    order_id=order_id,
                    validation_result={"message": validation_message},
                    risk_score=Decimal("0.5")  # Placeholder
                ))
                return {
                    "validated": True, 
                    "order_id": order_id,
                    "validation_time_ms": execution_time_ms
                }
            else:
                await event_bus.publish(OrderRejectedEvent(
                    correlation_id=context.workflow_run_id(),
                    causation_id=context.step_run_id(),
                    order_id=order_id,
                    rejection_reason=validation_message,
                    risk_violations=[validation_message]
                ))
                raise Exception(f"Risk validation failed: {validation_message}")
                
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            await event_bus.publish(OrderRejectedEvent(
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id="",
                rejection_reason=str(e),
                risk_violations=[str(e)]
            ))
            raise
    
    @hatchet.step("create_order_record", timeout="5s")
    async def create_order_record(self, context: WorkflowContext) -> Dict[str, Any]:
        """Create persistent order record"""
        start_time = time.perf_counter()
        validation_result = context.step_output("check_risk_limits")
        order_request = context.step_output("validate_request")["order_request"]
        order_id = validation_result["order_id"]
        
        # Get order manager service
        order_manager = context.additional_metadata.get("order_manager")
        if not order_manager:
            # Fallback to legacy synchronous order manager
            from ..trading.crypto_trading_engine import CryptoTradingEngine
            engine = CryptoTradingEngine()
            order_manager = engine.order_manager
        
        try:
            # Create order record using existing order manager
            from ..trading.crypto_trading_engine import OrderRequest, OrderSide, OrderType
            order_req_obj = OrderRequest(
                symbol=order_request["symbol"],
                side=OrderSide(order_request["side"]),
                order_type=OrderType(order_request["order_type"]),
                quantity=Decimal(str(order_request["quantity"])),
                price=Decimal(str(order_request.get("price", 0))) if order_request.get("price") else None,
                exchange=order_request.get("exchange"),
                strategy_id=order_request.get("strategy_id"),
                portfolio_id=order_request.get("portfolio_id", "default")
            )
            
            created_order_id = order_manager.create_order(order_req_obj)
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            await event_bus.publish(OrderCreatedEvent(
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id=created_order_id,
                order_record={"id": created_order_id, "status": "created"}
            ))
            
            return {
                "order_created": True, 
                "order_id": created_order_id,
                "creation_time_ms": execution_time_ms
            }
            
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            raise Exception(f"Order creation failed: {e}")
    
    @hatchet.step("execute_order", timeout="15s", retries=3)
    async def execute_order(self, context: WorkflowContext) -> Dict[str, Any]:
        """Execute order with retry logic and event emission"""
        start_time = time.perf_counter()
        order_result = context.step_output("create_order_record")
        order_request = context.step_output("validate_request")["order_request"]
        order_id = order_result["order_id"]
        
        # Get trading engine for execution
        trading_engine = context.additional_metadata.get("trading_engine")
        if not trading_engine:
            # Fallback to legacy synchronous trading engine
            from ..trading.crypto_trading_engine import CryptoTradingEngine
            trading_engine = CryptoTradingEngine()
        
        try:
            # Execute order using existing trading engine
            from ..trading.crypto_trading_engine import OrderRequest, OrderSide, OrderType
            order_req_obj = OrderRequest(
                symbol=order_request["symbol"],
                side=OrderSide(order_request["side"]),
                order_type=OrderType(order_request["order_type"]),
                quantity=Decimal(str(order_request["quantity"])),
                price=Decimal(str(order_request.get("price", 0))) if order_request.get("price") else None,
                exchange=order_request.get("exchange"),
                strategy_id=order_request.get("strategy_id"),
                portfolio_id=order_request.get("portfolio_id", "default")
            )
            
            # Use existing _execute_order method
            execution_result = trading_engine._execute_order(order_req_obj, order_id)
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            if execution_result.success:
                await event_bus.publish(OrderExecutedEvent(
                    correlation_id=context.workflow_run_id(),
                    causation_id=context.step_run_id(),
                    order_id=order_id,
                    exchange_order_id=execution_result.exchange_order_id or "",
                    executed_price=execution_result.avg_fill_price or Decimal("0"),
                    executed_quantity=execution_result.filled_quantity or Decimal("0"),
                    commission=execution_result.commission or Decimal("0"),
                    execution_time_ms=execution_time_ms
                ))
                
                return {
                    "executed": True,
                    "execution_result": {
                        "success": execution_result.success,
                        "filled_quantity": str(execution_result.filled_quantity),
                        "avg_fill_price": str(execution_result.avg_fill_price),
                        "commission": str(execution_result.commission),
                        "execution_time_ms": execution_time_ms
                    }
                }
            else:
                raise Exception(f"Order execution failed: {execution_result.message}")
                
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            raise Exception(f"Order execution error: {e}")
    
    @hatchet.step("update_portfolio", timeout="10s")
    async def update_portfolio(self, context: WorkflowContext) -> Dict[str, Any]:
        """Update positions and portfolio after execution"""
        start_time = time.perf_counter()
        execution_result = context.step_output("execute_order")
        order_result = context.step_output("create_order_record")
        order_request = context.step_output("validate_request")["order_request"]
        
        # Get position manager service
        position_manager = context.additional_metadata.get("position_manager")
        if not position_manager:
            # Fallback to legacy synchronous position manager
            from ..trading.crypto_trading_engine import CryptoTradingEngine
            engine = CryptoTradingEngine()
            position_manager = engine.position_manager
        
        try:
            # Create trade record for position update
            from ..domain.crypto import TradingTrade, OrderSide
            trade = TradingTrade(
                id=str(uuid.uuid4()),
                order_id=order_result["order_id"],
                symbol=order_request["symbol"],
                exchange=order_request.get("exchange", "binance"),
                side=order_request["side"],
                quantity=Decimal(execution_result["execution_result"]["filled_quantity"]),
                price=Decimal(execution_result["execution_result"]["avg_fill_price"]),
                notional_value=Decimal(execution_result["execution_result"]["filled_quantity"]) * Decimal(execution_result["execution_result"]["avg_fill_price"]),
                commission=Decimal(execution_result["execution_result"]["commission"]),
                commission_asset="USDT",
                is_maker=False
            )
            
            # Update position using existing position manager
            position_manager.update_position_from_trade(trade)
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Get updated position for event
            position = position_manager.get_or_create_position(
                trade.symbol, trade.exchange, "default"
            )
            
            await event_bus.publish(PositionUpdatedEvent(
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                position_id=position.id,
                symbol=position.symbol,
                exchange=position.exchange,
                quantity_change=trade.quantity,
                new_quantity=position.quantity,
                new_avg_price=position.avg_entry_price,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=position.unrealized_pnl
            ))
            
            return {
                "portfolio_updated": True,
                "position_update_time_ms": execution_time_ms
            }
            
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            raise Exception(f"Portfolio update failed: {e}")

# Register workflow with Hatchet
def register_workflows():
    """Register all workflows with Hatchet"""
    hatchet.workflow(PlaceOrderWorkflow)
```

---

## 📋 **Phase 2: Core Migration (Weeks 4-6)**

### **Week 4: Event-Driven Service Conversion** 🔄

#### **4.1 Event-Driven Base Service Class**
```python
# src/zvt/services/event_driven_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable
import asyncio
import logging

from ..events.base import BaseEvent, EventType
from ..events.event_bus import EventBus

logger = logging.getLogger(__name__)

class EventDrivenService(ABC):
    """Base class for all event-driven services"""
    
    def __init__(self, event_bus: EventBus, service_name: str):
        self.event_bus = event_bus
        self.service_name = service_name
        self.event_handlers: Dict[EventType, Callable] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize service and register event handlers"""
        await self._register_event_handlers()
        self.is_initialized = True
        logger.info(f"Event-driven service {self.service_name} initialized")
    
    @abstractmethod
    async def _register_event_handlers(self):
        """Register event handlers for this service"""
        pass
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register event handler for specific event type"""
        self.event_handlers[event_type] = handler
        asyncio.create_task(self.event_bus.subscribe(event_type, handler))
        logger.debug(f"Registered handler for {event_type.value} in {self.service_name}")
    
    async def emit_event(self, event: BaseEvent):
        """Emit event to event bus"""
        await self.event_bus.publish(event)
    
    async def shutdown(self):
        """Cleanup service resources"""
        logger.info(f"Shutting down event-driven service {self.service_name}")
```

#### **4.2 Event-Driven Risk Manager**
```python
# src/zvt/services/event_driven_risk_manager.py
import asyncio
from decimal import Decimal
from typing import Dict, Any

from .event_driven_service import EventDrivenService
from ..events.base import EventType
from ..events.trading_events import (
    OrderRequestedEvent, OrderValidatedEvent, OrderRejectedEvent,
    PositionUpdatedEvent, RiskLimitBreachedEvent
)
from ..trading.crypto_trading_engine import RiskManager

class EventDrivenRiskManager(EventDrivenService):
    """Risk management service with event-driven architecture"""
    
    def __init__(self, event_bus, legacy_risk_manager: RiskManager = None):
        super().__init__(event_bus, "risk_manager")
        self.legacy_risk_manager = legacy_risk_manager or RiskManager(None)
        self.risk_metrics_cache = {}
        
    async def _register_event_handlers(self):
        """Register event handlers"""
        self.register_handler(EventType.ORDER_REQUESTED, self.handle_order_request)
        self.register_handler(EventType.POSITION_UPDATED, self.handle_position_update)
        self.register_handler(EventType.PRICE_UPDATED, self.handle_price_update)
    
    async def handle_order_request(self, event: OrderRequestedEvent):
        """Validate order against risk limits"""
        try:
            # Convert event data to OrderRequest for compatibility
            from ..trading.crypto_trading_engine import OrderRequest, OrderSide, OrderType
            
            order_request = OrderRequest(
                symbol=event.order_request["symbol"],
                side=OrderSide(event.order_request["side"]),
                order_type=OrderType(event.order_request["order_type"]),
                quantity=Decimal(str(event.order_request["quantity"])),
                price=Decimal(str(event.order_request.get("price", 0))) if event.order_request.get("price") else None,
                exchange=event.order_request.get("exchange"),
                strategy_id=event.strategy_id,
                portfolio_id=event.order_request.get("portfolio_id", "default")
            )
            
            # Perform risk validation using legacy risk manager
            is_valid, validation_message = self.legacy_risk_manager.validate_order(order_request)
            
            # Generate order ID for tracking
            import uuid
            order_id = str(uuid.uuid4())
            
            if is_valid:
                await self.emit_event(OrderValidatedEvent(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    order_id=order_id,
                    validation_result={"message": validation_message},
                    risk_score=Decimal("0.5")  # Placeholder for now
                ))
            else:
                await self.emit_event(OrderRejectedEvent(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    order_id=order_id,
                    rejection_reason=validation_message,
                    risk_violations=[validation_message]
                ))
                
        except Exception as e:
            logger.error(f"Error handling order request: {e}")
            await self.emit_event(OrderRejectedEvent(
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                order_id="",
                rejection_reason=f"Risk validation error: {e}",
                risk_violations=[str(e)]
            ))
    
    async def handle_position_update(self, event: PositionUpdatedEvent):
        """Recalculate risk metrics after position change"""
        try:
            # Update portfolio risk metrics
            portfolio_id = event.metadata.get("portfolio_id", "default")
            risk_metrics = await self.calculate_portfolio_risk(portfolio_id)
            
            # Check for limit breaches
            breaches = self.check_risk_limits(risk_metrics)
            for breach in breaches:
                await self.emit_event(RiskLimitBreachedEvent(
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    limit_type=breach["limit_type"],
                    current_value=breach["current_value"],
                    limit_value=breach["limit_value"],
                    portfolio_id=portfolio_id,
                    symbol=event.symbol
                ))
                
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
    
    async def calculate_portfolio_risk(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        # Placeholder implementation
        return {
            "var_95": Decimal("10000"),
            "max_drawdown": Decimal("0.15"),
            "leverage_ratio": Decimal("2.0")
        }
    
    def check_risk_limits(self, risk_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check risk metrics against limits"""
        breaches = []
        
        # Example breach detection
        if risk_metrics["var_95"] > Decimal("50000"):
            breaches.append({
                "limit_type": "var_95",
                "current_value": risk_metrics["var_95"],
                "limit_value": Decimal("50000")
            })
        
        return breaches
```

### **Week 5: Integration Layer** 🔗

#### **5.1 Workflow Service Integration**
```python
# src/zvt/services/workflow_service.py
import asyncio
import time
from typing import Dict, Any, Optional
from decimal import Decimal

from ..config.hatchet_config import create_hatchet_client
from ..events.event_bus import EventBus
from ..workflows.trading_workflows import initialize_workflows
from ..trading.crypto_trading_engine import CryptoTradingEngine, OrderRequest, OrderResult

class WorkflowTradingService:
    """Integration service that bridges workflows and legacy trading engine"""
    
    def __init__(self, legacy_trading_engine: CryptoTradingEngine = None):
        self.hatchet = create_hatchet_client()
        self.event_bus = EventBus()
        self.legacy_engine = legacy_trading_engine or CryptoTradingEngine()
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize workflow service"""
        await self.event_bus.initialize()
        initialize_workflows(self.hatchet, self.event_bus)
        
        # Start Hatchet worker
        self.worker_task = asyncio.create_task(self.hatchet.start())
        
        self.is_initialized = True
        logger.info("Workflow trading service initialized")
    
    async def place_order_workflow(self, order_request: OrderRequest) -> OrderResult:
        """
        Place order using Hatchet workflow
        Maintains compatibility with legacy OrderRequest/OrderResult interface
        """
        start_time = time.perf_counter()
        
        try:
            # Convert OrderRequest to workflow input
            workflow_input = {
                "order_request": {
                    "symbol": order_request.symbol,
                    "side": order_request.side.value,
                    "order_type": order_request.order_type.value,
                    "quantity": str(order_request.quantity),
                    "price": str(order_request.price) if order_request.price else None,
                    "exchange": order_request.exchange,
                    "strategy_id": order_request.strategy_id,
                    "portfolio_id": order_request.portfolio_id,
                    "user_id": "default"  # TODO: Get from context
                }
            }
            
            # Inject legacy services for compatibility
            additional_metadata = {
                "trading_engine": self.legacy_engine,
                "risk_manager": self.legacy_engine.risk_manager,
                "order_manager": self.legacy_engine.order_manager,
                "position_manager": self.legacy_engine.position_manager
            }
            
            # Execute workflow
            workflow_result = await self.hatchet.run_workflow(
                "trading.place_order",
                workflow_input,
                additional_metadata=additional_metadata,
                timeout=30000  # 30 seconds
            )
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Convert workflow result back to OrderResult
            if workflow_result.get("error"):
                return OrderResult(
                    success=False,
                    message=workflow_result["error"]
                )
            
            final_step = workflow_result.get("update_portfolio", {})
            execution_step = workflow_result.get("execute_order", {})
            order_step = workflow_result.get("create_order_record", {})
            
            if final_step.get("portfolio_updated") and execution_step.get("executed"):
                exec_result = execution_step["execution_result"]
                return OrderResult(
                    success=True,
                    order_id=order_step.get("order_id"),
                    exchange_order_id=exec_result.get("exchange_order_id"),
                    message="Order executed successfully via workflow",
                    filled_quantity=Decimal(exec_result.get("filled_quantity", "0")),
                    avg_fill_price=Decimal(exec_result.get("avg_fill_price", "0")),
                    commission=Decimal(exec_result.get("commission", "0")),
                    commission_asset="USDT"
                )
            else:
                return OrderResult(
                    success=False,
                    message="Workflow execution incomplete"
                )
                
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Workflow execution failed in {execution_time_ms:.2f}ms: {e}")
            
            return OrderResult(
                success=False,
                message=f"Workflow execution error: {e}"
            )
    
    async def shutdown(self):
        """Shutdown workflow service"""
        if hasattr(self, 'worker_task'):
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        await self.event_bus.close()
        logger.info("Workflow trading service shutdown complete")
```

### **Week 6: Testing & Validation** ✅

#### **6.1 Workflow Test Adapter**
```python
# tests/workflows/test_workflow_compatibility.py
import asyncio
import pytest
from decimal import Decimal

from src.zvt.services.workflow_service import WorkflowTradingService
from src.zvt.trading.crypto_trading_engine import OrderRequest, OrderSide, OrderType

class TestWorkflowCompatibility:
    """Test workflow implementation maintains compatibility with existing tests"""
    
    @pytest.fixture
    async def workflow_service(self):
        """Create workflow service for testing"""
        service = WorkflowTradingService()
        await service.initialize()
        yield service
        await service.shutdown()
    
    @pytest.mark.asyncio
    async def test_place_order_workflow_compatibility(self, workflow_service):
        """Test that workflow maintains compatibility with existing place_order interface"""
        # Create order request identical to existing tests
        order_request = OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            exchange="binance",
            strategy_id="test_strategy",
            portfolio_id="default"
        )
        
        # Execute via workflow
        result = await workflow_service.place_order_workflow(order_request)
        
        # Verify result matches existing interface
        assert result.success is True
        assert result.order_id is not None
        assert result.filled_quantity == Decimal("0.1")
        assert result.avg_fill_price > 0
        assert result.commission >= 0
    
    @pytest.mark.asyncio 
    async def test_workflow_performance_target(self, workflow_service):
        """Test that workflow execution meets <75ms target"""
        order_request = OrderRequest(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            exchange="binance",
            strategy_id="perf_test",
            portfolio_id="default"
        )
        
        start_time = time.perf_counter()
        result = await workflow_service.place_order_workflow(order_request)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify performance target
        assert execution_time_ms < 75.0, f"Workflow took {execution_time_ms:.2f}ms > 75ms target"
        assert result.success is True

# Legacy test adapter
class LegacyTestAdapter:
    """Adapter to run existing tests against workflow implementation"""
    
    def __init__(self):
        self.workflow_service = None
        
    async def setup(self):
        self.workflow_service = WorkflowTradingService()
        await self.workflow_service.initialize()
    
    async def teardown(self):
        if self.workflow_service:
            await self.workflow_service.shutdown()
    
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        """Synchronous wrapper for workflow execution"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.workflow_service.place_order_workflow(order_request)
        )
```

---

## 📊 **Success Metrics & Validation**

### **Phase 1 Success Criteria** ✅
- [ ] Hatchet SDK integrated and operational
- [ ] Event bus processing 1K+ events/sec
- [ ] Basic order placement workflow executing successfully
- [ ] Event store capturing complete audit trail

### **Phase 2 Success Criteria** ✅
- [ ] 16/17 tests still passing with workflow implementation
- [ ] <75ms average workflow execution time
- [ ] Event-driven services processing events correctly
- [ ] Complete backward compatibility maintained

### **Performance Validation** ⚡
```python
# Performance test script
async def validate_workflow_performance():
    """Validate workflow meets performance targets"""
    service = WorkflowTradingService()
    await service.initialize()
    
    # Execute 100 orders and measure performance
    execution_times = []
    for i in range(100):
        order_request = OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
            exchange="binance"
        )
        
        start_time = time.perf_counter()
        result = await service.place_order_workflow(order_request)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        execution_times.append(execution_time_ms)
        assert result.success, f"Order {i} failed: {result.message}"
    
    avg_time = sum(execution_times) / len(execution_times)
    p95_time = sorted(execution_times)[int(len(execution_times) * 0.95)]
    
    print(f"Average execution time: {avg_time:.2f}ms")
    print(f"95th percentile time: {p95_time:.2f}ms")
    
    assert avg_time < 75.0, f"Average time {avg_time:.2f}ms exceeds 75ms target"
    assert p95_time < 100.0, f"95th percentile {p95_time:.2f}ms exceeds 100ms target"
    
    await service.shutdown()
```

---

## 🚀 **Next Steps - Phase 3 & Beyond**

### **Phase 3: Advanced Workflows (Weeks 7-10)** 🎯
- Portfolio rebalancing workflow implementation
- Risk monitoring workflow (long-running)
- Market data processing workflows
- Performance optimization and horizontal scaling

### **Phase 4: Production Deployment (Weeks 11-12)** 🏭
- Multi-node Hatchet worker deployment
- Production event bus setup with Redis Cluster
- Monitoring and observability implementation
- Load testing and performance validation

### **Epic 2 Integration** 🚀
- Enhanced trading platform features built on event-driven foundation
- Distributed order management across multiple nodes
- Real-time analytics powered by event streams
- AI/ML workflow integration for Epic 3

---

## 📞 **Support & Documentation**

### **Implementation Support** 🛠️
- **Architecture Reviews**: Weekly review sessions during implementation
- **Performance Monitoring**: Continuous performance tracking and optimization
- **Test Compatibility**: Automated validation of test suite compatibility
- **Documentation**: Complete implementation guides and API documentation

### **Troubleshooting Guide** 🔧
- **Common Issues**: Redis connection problems, workflow timeout handling
- **Performance Tuning**: Event bus optimization, workflow step timeouts
- **Error Recovery**: Dead letter queue setup, workflow retry strategies
- **Monitoring**: Event flow monitoring, workflow execution tracking

---

**The event-driven future of ZVT starts with this implementation plan.** 🚀

*Ready to transform ZVT into the world's most scalable cryptocurrency trading platform.*