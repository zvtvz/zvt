# ZVT Event-Driven Architecture with Hatchet Workflow Engine
*Version: 1.0.0*
*Date: August 20, 2025*
*Status: ARCHITECTURAL BLUEPRINT FOR IMPLEMENTATION*

## 🚀 **Executive Summary**

This specification outlines the transformation of ZVT's current synchronous trading engine architecture into a **scalable, resilient, event-driven platform** powered by **Hatchet workflow engine**. This evolution enables horizontal scaling, improved fault tolerance, and sophisticated workflow orchestration while maintaining the exceptional performance achieved in TDD Cycle 1.

### **Strategic Objectives** 🎯

1. **Scalability**: Enable horizontal scaling across multiple nodes and regions
2. **Resilience**: Fault-tolerant workflow execution with automatic recovery
3. **Observability**: Complete visibility into trading workflows and performance
4. **Maintainability**: Loosely coupled components with clear separation of concerns
5. **Performance**: Maintain <50ms order execution and <100ms position updates

---

## 📊 **Current vs. Target Architecture**

### **Current Architecture (TDD Cycle 1)** ✅
```python
# Synchronous method calls
def place_order(order_request: OrderRequest) -> OrderResult:
    # 1. Risk validation
    is_valid = self.risk_manager.validate_order(order_request)
    # 2. Create order record  
    order_id = self.order_manager.create_order(order_request)
    # 3. Route to best exchange
    exchange = self.routing_strategy.select_best_exchange(...)
    # 4. Execute order
    result = self._execute_order(order_request, order_id)
    # 5. Update positions
    self.position_manager.update_position_from_trade(trade)
```

### **Target Architecture (Event-Driven + Hatchet)** 🎯
```python
# Event-driven workflow orchestration
@hatchet.workflow("trading.place_order")
class PlaceOrderWorkflow:
    @hatchet.step("validate_risk")
    def validate_risk(self, context: WorkflowContext) -> RiskValidationEvent
    
    @hatchet.step("create_order") 
    def create_order(self, context: WorkflowContext) -> OrderCreatedEvent
    
    @hatchet.step("route_exchange")
    def route_exchange(self, context: WorkflowContext) -> ExchangeRoutedEvent
    
    @hatchet.step("execute_order")
    def execute_order(self, context: WorkflowContext) -> OrderExecutedEvent
    
    @hatchet.step("update_positions")
    def update_positions(self, context: WorkflowContext) -> PositionUpdatedEvent
```

---

## 🏗️ **Event-Driven Architecture Overview**

### **Core Architecture Principles** 📋

1. **Event Sourcing**: All state changes captured as immutable events
2. **CQRS (Command Query Responsibility Segregation)**: Separate read/write models
3. **Saga Pattern**: Distributed transactions managed by workflows
4. **Event Streaming**: Real-time event processing with Apache Kafka/Redis Streams
5. **Workflow Orchestration**: Complex business processes managed by Hatchet

### **Event Architecture Layers** 🔄

```
┌─────────────────────────────────────────────────────────────────┐
│                    HATCHET WORKFLOW ENGINE                     │
│  (Orchestration, State Management, Fault Tolerance)            │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                      EVENT PROCESSING LAYER                    │
│  Event Bus │ Event Store │ Saga Coordinator │ State Manager   │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                     DOMAIN SERVICE LAYER                       │
│  Trading │ Risk │ Portfolio │ Exchange │ Notification Services │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                     DATA & INFRASTRUCTURE LAYER                │
│  Event Store │ Time Series DB │ Cache │ Message Queue         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 **Event Schema & Message Formats**

### **Core Event Types** 🔄

#### **Trading Events**
```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    ORDER_REQUESTED = "order.requested"
    ORDER_VALIDATED = "order.validated" 
    ORDER_REJECTED = "order.rejected"
    ORDER_CREATED = "order.created"
    EXCHANGE_ROUTED = "exchange.routed"
    ORDER_EXECUTED = "order.executed"
    ORDER_FAILED = "order.failed"
    POSITION_UPDATED = "position.updated"
    PORTFOLIO_UPDATED = "portfolio.updated"
    RISK_BREACHED = "risk.breached"
    ALERT_TRIGGERED = "alert.triggered"

@dataclass
class BaseEvent:
    """Base event class with common fields"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    correlation_id: str  # Links related events
    causation_id: str    # Direct cause event
    version: int = 1
    metadata: Dict[str, Any] = None

@dataclass
class OrderRequestedEvent(BaseEvent):
    """Order placement request initiated"""
    order_request: Dict[str, Any]
    user_id: str
    strategy_id: Optional[str] = None
    
@dataclass
class OrderValidatedEvent(BaseEvent):
    """Order passed risk validation"""
    order_id: str
    validation_result: Dict[str, Any]
    risk_score: Decimal
    
@dataclass
class OrderRejectedEvent(BaseEvent):
    """Order failed validation or execution"""
    order_id: str
    rejection_reason: str
    risk_violations: List[str]
    
@dataclass
class ExchangeRoutedEvent(BaseEvent):
    """Order routed to optimal exchange"""
    order_id: str
    selected_exchange: str
    routing_reason: str
    routing_metrics: Dict[str, Any]
    
@dataclass
class OrderExecutedEvent(BaseEvent):
    """Order successfully executed"""
    order_id: str
    exchange_order_id: str
    executed_price: Decimal
    executed_quantity: Decimal
    commission: Decimal
    execution_time_ms: float
    
@dataclass
class PositionUpdatedEvent(BaseEvent):
    """Position updated after trade execution"""
    position_id: str
    symbol: str
    exchange: str
    quantity_change: Decimal
    new_quantity: Decimal
    new_avg_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
```

#### **Market Data Events**
```python
@dataclass
class PriceUpdateEvent(BaseEvent):
    """Real-time price update"""
    symbol: str
    exchange: str
    price: Decimal
    volume: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    
@dataclass
class OrderBookUpdateEvent(BaseEvent):
    """Order book depth update"""
    symbol: str
    exchange: str
    bids: List[Tuple[Decimal, Decimal]]
    asks: List[Tuple[Decimal, Decimal]]
    
@dataclass
class TradeTickEvent(BaseEvent):
    """Individual trade execution"""
    symbol: str
    exchange: str
    price: Decimal
    quantity: Decimal
    side: str
    trade_id: str
```

#### **Risk & Portfolio Events**
```python
@dataclass
class RiskLimitBreachedEvent(BaseEvent):
    """Risk limit violation detected"""
    limit_type: str
    current_value: Decimal
    limit_value: Decimal
    portfolio_id: str
    symbol: Optional[str] = None
    
@dataclass
class PortfolioRebalanceEvent(BaseEvent):
    """Portfolio rebalancing triggered"""
    portfolio_id: str
    rebalance_type: str
    target_weights: Dict[str, Decimal]
    current_weights: Dict[str, Decimal]
```

---

## 🔄 **Hatchet Workflow Definitions**

### **Core Trading Workflows** ⚙️

#### **1. Order Placement Workflow**
```python
from hatchet_sdk import Hatchet
from hatchet_sdk.workflow import WorkflowContext
from typing import Dict, Any

@hatchet.workflow("trading.place_order", timeout="30s")
class PlaceOrderWorkflow:
    """
    Orchestrates the complete order placement lifecycle
    Performance Target: <50ms end-to-end execution
    """
    
    @hatchet.step("validate_request", timeout="5s")
    def validate_request(self, context: WorkflowContext) -> Dict[str, Any]:
        """Validate order request and basic requirements"""
        order_request = context.workflow_input()["order_request"]
        
        # Emit event
        self.emit_event(OrderRequestedEvent(
            event_id=generate_event_id(),
            event_type=EventType.ORDER_REQUESTED,
            timestamp=datetime.utcnow(),
            correlation_id=context.workflow_run_id(),
            causation_id=context.workflow_run_id(),
            order_request=order_request,
            user_id=order_request.get("user_id")
        ))
        
        # Basic validation logic
        return {"valid": True, "order_request": order_request}
    
    @hatchet.step("check_risk_limits", timeout="10s", retries=3)
    def check_risk_limits(self, context: WorkflowContext) -> Dict[str, Any]:
        """Comprehensive risk validation"""
        prev_result = context.step_output("validate_request")
        order_request = prev_result["order_request"]
        
        # Risk validation logic
        risk_service = self.get_service("risk_manager")
        validation_result = risk_service.validate_order_async(order_request)
        
        if validation_result.is_valid:
            self.emit_event(OrderValidatedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_VALIDATED,
                timestamp=datetime.utcnow(),
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id=validation_result.order_id,
                validation_result=validation_result.to_dict(),
                risk_score=validation_result.risk_score
            ))
            return {"validated": True, "order_id": validation_result.order_id}
        else:
            self.emit_event(OrderRejectedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_REJECTED,
                timestamp=datetime.utcnow(),
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id=validation_result.order_id,
                rejection_reason=validation_result.rejection_reason,
                risk_violations=validation_result.violations
            ))
            raise Exception(f"Risk validation failed: {validation_result.rejection_reason}")
    
    @hatchet.step("create_order_record", timeout="5s")
    def create_order_record(self, context: WorkflowContext) -> Dict[str, Any]:
        """Create persistent order record"""
        validation_result = context.step_output("check_risk_limits")
        order_id = validation_result["order_id"]
        
        order_service = self.get_service("order_manager")
        order_record = order_service.create_order_record(order_id, context.workflow_input())
        
        self.emit_event(OrderCreatedEvent(
            event_id=generate_event_id(),
            event_type=EventType.ORDER_CREATED,
            timestamp=datetime.utcnow(),
            correlation_id=context.workflow_run_id(),
            causation_id=context.step_run_id(),
            order_id=order_id,
            order_record=order_record.to_dict()
        ))
        
        return {"order_created": True, "order_id": order_id}
    
    @hatchet.step("route_to_exchange", timeout="10s", retries=2)
    def route_to_exchange(self, context: WorkflowContext) -> Dict[str, Any]:
        """Select optimal exchange for execution"""
        order_result = context.step_output("create_order_record")
        order_id = order_result["order_id"]
        
        routing_service = self.get_service("exchange_router")
        routing_result = routing_service.select_best_exchange_async(
            order_request=context.workflow_input()["order_request"]
        )
        
        self.emit_event(ExchangeRoutedEvent(
            event_id=generate_event_id(),
            event_type=EventType.EXCHANGE_ROUTED,
            timestamp=datetime.utcnow(),
            correlation_id=context.workflow_run_id(),
            causation_id=context.step_run_id(),
            order_id=order_id,
            selected_exchange=routing_result.selected_exchange,
            routing_reason=routing_result.routing_reason,
            routing_metrics=routing_result.metrics
        ))
        
        return {
            "exchange_selected": True,
            "selected_exchange": routing_result.selected_exchange,
            "routing_metrics": routing_result.metrics
        }
    
    @hatchet.step("execute_on_exchange", timeout="15s", retries=3)
    def execute_on_exchange(self, context: WorkflowContext) -> Dict[str, Any]:
        """Execute order on selected exchange"""
        routing_result = context.step_output("route_to_exchange")
        order_result = context.step_output("create_order_record")
        
        execution_service = self.get_service("order_executor")
        execution_result = execution_service.execute_order_async(
            order_id=order_result["order_id"],
            exchange=routing_result["selected_exchange"],
            order_request=context.workflow_input()["order_request"]
        )
        
        if execution_result.success:
            self.emit_event(OrderExecutedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_EXECUTED,
                timestamp=datetime.utcnow(),
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id=order_result["order_id"],
                exchange_order_id=execution_result.exchange_order_id,
                executed_price=execution_result.executed_price,
                executed_quantity=execution_result.executed_quantity,
                commission=execution_result.commission,
                execution_time_ms=execution_result.execution_time_ms
            ))
            return {
                "executed": True,
                "execution_result": execution_result.to_dict()
            }
        else:
            self.emit_event(OrderFailedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_FAILED,
                timestamp=datetime.utcnow(),
                correlation_id=context.workflow_run_id(),
                causation_id=context.step_run_id(),
                order_id=order_result["order_id"],
                failure_reason=execution_result.error_message
            ))
            raise Exception(f"Order execution failed: {execution_result.error_message}")
    
    @hatchet.step("update_portfolio", timeout="10s")
    def update_portfolio(self, context: WorkflowContext) -> Dict[str, Any]:
        """Update positions and portfolio after execution"""
        execution_result = context.step_output("execute_on_exchange")
        order_result = context.step_output("create_order_record")
        
        portfolio_service = self.get_service("portfolio_manager")
        position_update = portfolio_service.update_position_from_execution(
            order_id=order_result["order_id"],
            execution_result=execution_result["execution_result"]
        )
        
        self.emit_event(PositionUpdatedEvent(
            event_id=generate_event_id(),
            event_type=EventType.POSITION_UPDATED,
            timestamp=datetime.utcnow(),
            correlation_id=context.workflow_run_id(),
            causation_id=context.step_run_id(),
            position_id=position_update.position_id,
            symbol=position_update.symbol,
            exchange=position_update.exchange,
            quantity_change=position_update.quantity_change,
            new_quantity=position_update.new_quantity,
            new_avg_price=position_update.new_avg_price,
            realized_pnl=position_update.realized_pnl,
            unrealized_pnl=position_update.unrealized_pnl
        ))
        
        return {"portfolio_updated": True}

    def emit_event(self, event: BaseEvent):
        """Emit event to event bus"""
        event_bus = self.get_service("event_bus")
        event_bus.publish(event)
```

#### **2. Portfolio Rebalancing Workflow**
```python
@hatchet.workflow("portfolio.rebalance", timeout="60s")
class PortfolioRebalanceWorkflow:
    """
    Orchestrates portfolio rebalancing across multiple positions
    Handles complex multi-step rebalancing with rollback capabilities
    """
    
    @hatchet.step("calculate_rebalance_targets")
    def calculate_rebalance_targets(self, context: WorkflowContext) -> Dict[str, Any]:
        """Calculate target allocations and required trades"""
        portfolio_id = context.workflow_input()["portfolio_id"]
        rebalance_strategy = context.workflow_input()["strategy"]
        
        portfolio_service = self.get_service("portfolio_manager")
        rebalance_plan = portfolio_service.calculate_rebalance_plan(
            portfolio_id, rebalance_strategy
        )
        
        return {"rebalance_plan": rebalance_plan.to_dict()}
    
    @hatchet.step("validate_rebalance_plan")
    def validate_rebalance_plan(self, context: WorkflowContext) -> Dict[str, Any]:
        """Validate rebalancing plan against risk limits"""
        rebalance_plan = context.step_output("calculate_rebalance_targets")["rebalance_plan"]
        
        risk_service = self.get_service("risk_manager")
        validation = risk_service.validate_rebalance_plan(rebalance_plan)
        
        if not validation.is_valid:
            raise Exception(f"Rebalance plan validation failed: {validation.errors}")
            
        return {"validated": True}
    
    @hatchet.step("execute_rebalance_trades", timeout="120s")
    def execute_rebalance_trades(self, context: WorkflowContext) -> Dict[str, Any]:
        """Execute all trades required for rebalancing"""
        rebalance_plan = context.step_output("calculate_rebalance_targets")["rebalance_plan"]
        
        # Spawn child workflows for each trade
        trade_workflows = []
        for trade in rebalance_plan["trades"]:
            child_workflow = context.spawn_workflow(
                "trading.place_order",
                {"order_request": trade}
            )
            trade_workflows.append(child_workflow)
        
        # Wait for all trades to complete
        results = []
        for workflow in trade_workflows:
            result = workflow.result(timeout=60)
            results.append(result)
        
        return {"trades_executed": len(results), "results": results}
```

#### **3. Risk Monitoring Workflow**
```python
@hatchet.workflow("risk.monitor_portfolio", timeout="infinite")
class RiskMonitoringWorkflow:
    """
    Continuous risk monitoring with real-time limit checks
    Runs as long-lived workflow with periodic risk assessments
    """
    
    @hatchet.step("initialize_monitoring")
    def initialize_monitoring(self, context: WorkflowContext) -> Dict[str, Any]:
        """Set up risk monitoring parameters"""
        portfolio_id = context.workflow_input()["portfolio_id"]
        monitoring_config = context.workflow_input()["config"]
        
        return {
            "portfolio_id": portfolio_id,
            "config": monitoring_config,
            "monitoring_active": True
        }
    
    @hatchet.step("periodic_risk_check", timeout="30s")
    def periodic_risk_check(self, context: WorkflowContext) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        config = context.step_output("initialize_monitoring")
        
        risk_service = self.get_service("risk_manager")
        risk_assessment = risk_service.assess_portfolio_risk(
            portfolio_id=config["portfolio_id"]
        )
        
        # Check for risk limit breaches
        if risk_assessment.has_breaches():
            for breach in risk_assessment.breaches:
                self.emit_event(RiskLimitBreachedEvent(
                    event_id=generate_event_id(),
                    event_type=EventType.RISK_BREACHED,
                    timestamp=datetime.utcnow(),
                    correlation_id=context.workflow_run_id(),
                    causation_id=context.step_run_id(),
                    limit_type=breach.limit_type,
                    current_value=breach.current_value,
                    limit_value=breach.limit_value,
                    portfolio_id=config["portfolio_id"],
                    symbol=breach.symbol
                ))
                
                # Trigger emergency actions if critical
                if breach.severity == "critical":
                    context.spawn_workflow(
                        "risk.emergency_action",
                        {"breach": breach.to_dict()}
                    )
        
        # Sleep and repeat
        context.sleep(config["config"]["check_interval_seconds"])
        return context.step_output("periodic_risk_check")  # Loop back
```

---

## 🔧 **Service Integration Layer**

### **Event-Driven Service Architecture** ⚙️

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import asyncio

class EventDrivenService(ABC):
    """Base class for all event-driven services"""
    
    def __init__(self, event_bus: 'EventBus', service_name: str):
        self.event_bus = event_bus
        self.service_name = service_name
        self.event_handlers: Dict[EventType, callable] = {}
        
    def register_handler(self, event_type: EventType, handler: callable):
        """Register event handler for specific event type"""
        self.event_handlers[event_type] = handler
        self.event_bus.subscribe(event_type, handler)
    
    async def emit_event(self, event: BaseEvent):
        """Emit event to event bus"""
        await self.event_bus.publish(event)
    
    @abstractmethod
    async def initialize(self):
        """Initialize service and register event handlers"""
        pass

class EventDrivenRiskManager(EventDrivenService):
    """Risk management service with event-driven architecture"""
    
    async def initialize(self):
        """Register event handlers"""
        self.register_handler(EventType.ORDER_REQUESTED, self.handle_order_request)
        self.register_handler(EventType.POSITION_UPDATED, self.handle_position_update)
        self.register_handler(EventType.PRICE_UPDATE, self.handle_price_update)
    
    async def handle_order_request(self, event: OrderRequestedEvent):
        """Validate order against risk limits"""
        order_request = event.order_request
        
        # Perform risk validation
        validation_result = await self.validate_order_async(order_request)
        
        if validation_result.is_valid:
            await self.emit_event(OrderValidatedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_VALIDATED,
                timestamp=datetime.utcnow(),
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                order_id=validation_result.order_id,
                validation_result=validation_result.to_dict(),
                risk_score=validation_result.risk_score
            ))
        else:
            await self.emit_event(OrderRejectedEvent(
                event_id=generate_event_id(),
                event_type=EventType.ORDER_REJECTED,
                timestamp=datetime.utcnow(),
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                order_id=validation_result.order_id,
                rejection_reason=validation_result.rejection_reason,
                risk_violations=validation_result.violations
            ))
    
    async def handle_position_update(self, event: PositionUpdatedEvent):
        """Recalculate risk metrics after position change"""
        # Update portfolio risk metrics
        portfolio_id = event.portfolio_id
        risk_metrics = await self.calculate_portfolio_risk(portfolio_id)
        
        # Check for limit breaches
        breaches = self.check_risk_limits(risk_metrics)
        for breach in breaches:
            await self.emit_event(RiskLimitBreachedEvent(
                event_id=generate_event_id(),
                event_type=EventType.RISK_BREACHED,
                timestamp=datetime.utcnow(),
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                limit_type=breach.limit_type,
                current_value=breach.current_value,
                limit_value=breach.limit_value,
                portfolio_id=portfolio_id,
                symbol=event.symbol
            ))

class EventDrivenPortfolioManager(EventDrivenService):
    """Portfolio management with real-time event processing"""
    
    async def initialize(self):
        """Register event handlers"""
        self.register_handler(EventType.ORDER_EXECUTED, self.handle_order_execution)
        self.register_handler(EventType.PRICE_UPDATE, self.handle_price_update)
    
    async def handle_order_execution(self, event: OrderExecutedEvent):
        """Update positions after order execution"""
        position_update = await self.update_position_from_execution(
            order_id=event.order_id,
            executed_price=event.executed_price,
            executed_quantity=event.executed_quantity
        )
        
        await self.emit_event(PositionUpdatedEvent(
            event_id=generate_event_id(),
            event_type=EventType.POSITION_UPDATED,
            timestamp=datetime.utcnow(),
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            position_id=position_update.position_id,
            symbol=position_update.symbol,
            exchange=position_update.exchange,
            quantity_change=position_update.quantity_change,
            new_quantity=position_update.new_quantity,
            new_avg_price=position_update.new_avg_price,
            realized_pnl=position_update.realized_pnl,
            unrealized_pnl=position_update.unrealized_pnl
        ))
    
    async def handle_price_update(self, event: PriceUpdateEvent):
        """Update position valuations with real-time prices"""
        # Calculate updated PnL for all positions in this symbol
        positions = await self.get_positions_by_symbol(event.symbol, event.exchange)
        
        for position in positions:
            updated_pnl = self.calculate_unrealized_pnl(
                position, event.price
            )
            
            # Emit portfolio value update
            await self.emit_event(PortfolioUpdatedEvent(
                event_id=generate_event_id(),
                event_type=EventType.PORTFOLIO_UPDATED,
                timestamp=datetime.utcnow(),
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                portfolio_id=position.portfolio_id,
                symbol=position.symbol,
                unrealized_pnl=updated_pnl,
                market_value=position.quantity * event.price
            ))
```

### **Event Bus Implementation** 🚌

```python
import asyncio
from typing import Dict, List, Callable
import redis.asyncio as redis
import json

class EventBus:
    """High-performance event bus with Redis Streams backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_store = EventStore(self.redis)
        
    async def publish(self, event: BaseEvent):
        """Publish event to all subscribers"""
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
            "data": json.dumps(event.__dict__, default=str)
        }
        
        await self.redis.xadd(stream_key, event_data)
        
        # Notify local subscribers
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                asyncio.create_task(handler(event))
    
    async def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events of specific type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        
        # Start Redis stream consumer for this event type
        stream_key = f"events:{event_type.value}"
        asyncio.create_task(
            self._consume_stream(stream_key, handler)
        )
    
    async def _consume_stream(self, stream_key: str, handler: Callable):
        """Consume events from Redis stream"""
        consumer_group = f"group:{self.service_name}"
        consumer_name = f"consumer:{asyncio.current_task().get_name()}"
        
        try:
            await self.redis.xgroup_create(
                stream_key, consumer_group, id="0", mkstream=True
            )
        except:
            pass  # Group already exists
        
        while True:
            try:
                messages = await self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_key: ">"},
                    count=10,
                    block=1000
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        event_data = json.loads(fields[b"data"])
                        event = self._deserialize_event(event_data)
                        
                        try:
                            await handler(event)
                            await self.redis.xack(stream_key, consumer_group, msg_id)
                        except Exception as e:
                            # Log error and potentially retry
                            print(f"Error processing event {msg_id}: {e}")
                            
            except Exception as e:
                print(f"Stream consumer error: {e}")
                await asyncio.sleep(1)

class EventStore:
    """Persistent event storage for audit and replay"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def store_event(self, event: BaseEvent):
        """Store event permanently"""
        event_key = f"event_store:{event.event_id}"
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "data": json.dumps(event.__dict__, default=str),
            "version": event.version
        }
        
        await self.redis.hset(event_key, mapping=event_data)
        
        # Add to correlation stream for event sourcing
        correlation_key = f"correlation:{event.correlation_id}"
        await self.redis.xadd(correlation_key, {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat()
        })
    
    async def get_events_by_correlation(self, correlation_id: str) -> List[BaseEvent]:
        """Get all events for a correlation ID (workflow)"""
        correlation_key = f"correlation:{correlation_id}"
        events = await self.redis.xrange(correlation_key)
        
        result = []
        for event_id, fields in events:
            event_key = f"event_store:{fields[b'event_id'].decode()}"
            event_data = await self.redis.hgetall(event_key)
            result.append(self._deserialize_event(event_data))
        
        return result
```

---

## 📊 **Performance & Scalability**

### **Performance Targets** ⚡

| Metric | Current (Sync) | Target (Event-Driven) | Method |
|--------|---------------|----------------------|---------|
| Order Execution | <50ms | <75ms | Workflow orchestration overhead |
| Position Updates | <100ms | <50ms | Async event processing |
| Throughput | 1K orders/sec | 10K orders/sec | Horizontal scaling |
| Event Latency | N/A | <10ms | Redis Streams + local cache |
| Workflow Recovery | N/A | <1s | Hatchet state persistence |

### **Scalability Architecture** 📈

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCER / API GATEWAY                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│              HATCHET WORKFLOW ENGINE CLUSTER                   │
│  Worker Node 1 │ Worker Node 2 │ Worker Node 3 │ Worker Node N │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                   REDIS CLUSTER (Event Bus)                    │
│     Primary     │    Replica 1   │   Replica 2   │   Shard N  │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│               SERVICE CLUSTER (Auto-Scaling)                   │
│  Risk Service │ Portfolio Svc │ Exchange Svc │ Notification  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Implementation Plan**

### **Phase 1: Foundation (2-3 weeks)** 🏗️

1. **Event Schema Implementation**
   - Define all event types and data structures
   - Implement event serialization/deserialization
   - Create event validation framework

2. **Event Bus Setup**
   - Redis Streams infrastructure
   - Event routing and subscription logic
   - Event store implementation

3. **Hatchet Integration**
   - Hatchet SDK setup and configuration
   - Basic workflow templates
   - Workflow state management

### **Phase 2: Core Workflows (3-4 weeks)** ⚙️

1. **Order Placement Workflow**
   - Convert existing sync order placement to workflow
   - Implement all workflow steps
   - Add error handling and retries

2. **Service Event Integration**
   - Convert RiskManager to event-driven
   - Convert PortfolioManager to event-driven
   - Convert OrderManager to event-driven

3. **Testing & Validation**
   - Maintain 16/17 test success rate
   - Performance benchmarking
   - Load testing

### **Phase 3: Advanced Features (2-3 weeks)** 🚀

1. **Complex Workflows**
   - Portfolio rebalancing workflow
   - Risk monitoring workflow
   - Market data processing workflow

2. **Performance Optimization**
   - Event processing optimization
   - Workflow execution tuning
   - Cache implementation

3. **Monitoring & Observability**
   - Workflow execution metrics
   - Event flow monitoring
   - Performance dashboards

---

## 🎯 **Success Metrics**

### **Migration Success Criteria** ✅

1. **Functional Compatibility**: 16/17 tests still passing
2. **Performance**: <75ms order execution (vs. <50ms current)
3. **Scalability**: Support 10x throughput (10K orders/sec)
4. **Reliability**: 99.9% workflow success rate
5. **Observability**: Complete workflow and event visibility

### **Business Benefits** 💼

1. **Horizontal Scalability**: Support growing trading volume
2. **Fault Tolerance**: Automatic recovery from failures
3. **Feature Velocity**: Faster development with modular architecture
4. **Operational Excellence**: Better monitoring and debugging
5. **Future-Proofing**: Platform ready for AI/ML and advanced analytics

---

## 🚀 **Conclusion**

This event-driven architecture with Hatchet workflow orchestration transforms ZVT from a monolithic synchronous system into a scalable, resilient platform capable of institutional-grade performance. The migration maintains existing functionality while enabling future innovation through loosely coupled, event-driven services.

**The architecture positions ZVT for the next phase of growth**, supporting advanced features like AI-powered trading strategies, real-time risk management, and enterprise-scale deployment while maintaining the exceptional performance standards established in TDD Cycle 1.

---

*Next Steps: Begin Phase 1 implementation with event schema and infrastructure setup*