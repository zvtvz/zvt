# src/zvt/trading/exceptions.py
"""
Trading System Exceptions
Custom exception classes for the ZVT crypto trading platform

These exceptions provide specific error handling for trading operations,
risk management, and position management scenarios.
"""


class TradingError(Exception):
    """Base exception for all trading-related errors"""
    pass


class OrderError(TradingError):
    """Base exception for order-related errors"""
    pass


class NoAvailableExchangeError(OrderError):
    """Raised when no exchange is available for trading a symbol"""
    
    def __init__(self, symbol: str, message: str = None):
        self.symbol = symbol
        if message is None:
            message = f"No exchanges available for trading {symbol}"
        super().__init__(message)


class InsufficientBalanceError(OrderError):
    """Raised when account has insufficient balance for an order"""
    
    def __init__(self, currency: str, required: str, available: str, message: str = None):
        self.currency = currency
        self.required = required
        self.available = available
        if message is None:
            message = f"Insufficient {currency} balance. Required: {required}, Available: {available}"
        super().__init__(message)


class OrderValidationError(OrderError):
    """Raised when an order fails validation checks"""
    
    def __init__(self, errors: list, message: str = None):
        self.errors = errors
        if message is None:
            message = f"Order validation failed: {', '.join(errors)}"
        super().__init__(message)


class OrderNotFoundError(OrderError):
    """Raised when trying to access a non-existent order"""
    
    def __init__(self, order_id: str, message: str = None):
        self.order_id = order_id
        if message is None:
            message = f"Order not found: {order_id}"
        super().__init__(message)


class OrderCancellationError(OrderError):
    """Raised when order cancellation fails"""
    
    def __init__(self, order_id: str, reason: str, message: str = None):
        self.order_id = order_id
        self.reason = reason
        if message is None:
            message = f"Failed to cancel order {order_id}: {reason}"
        super().__init__(message)


class OrderModificationError(OrderError):
    """Raised when order modification fails"""
    
    def __init__(self, order_id: str, reason: str, message: str = None):
        self.order_id = order_id
        self.reason = reason
        if message is None:
            message = f"Failed to modify order {order_id}: {reason}"
        super().__init__(message)


# Position Management Exceptions

class PositionError(TradingError):
    """Base exception for position-related errors"""
    pass


class InsufficientPositionError(PositionError):
    """Raised when trying to sell more than the available position"""
    
    def __init__(self, symbol: str, requested: str, available: str, message: str = None):
        self.symbol = symbol
        self.requested = requested
        self.available = available
        if message is None:
            message = f"Insufficient position in {symbol}. Requested: {requested}, Available: {available}"
        super().__init__(message)


class PositionNotFoundError(PositionError):
    """Raised when trying to access a non-existent position"""
    
    def __init__(self, symbol: str, message: str = None):
        self.symbol = symbol
        if message is None:
            message = f"Position not found: {symbol}"
        super().__init__(message)


class PositionLimitExceededError(PositionError):
    """Raised when a trade would exceed position limits"""
    
    def __init__(self, symbol: str, current: str, limit: str, additional: str, message: str = None):
        self.symbol = symbol
        self.current = current
        self.limit = limit
        self.additional = additional
        if message is None:
            message = f"Position limit exceeded for {symbol}. Current: {current}, Limit: {limit}, Attempting to add: {additional}"
        super().__init__(message)


# Risk Management Exceptions

class RiskError(TradingError):
    """Base exception for risk management errors"""
    pass


class ConcentrationLimitError(RiskError):
    """Raised when portfolio concentration limits are exceeded"""
    
    def __init__(self, symbol: str, current_pct: str, limit_pct: str, message: str = None):
        self.symbol = symbol
        self.current_pct = current_pct
        self.limit_pct = limit_pct
        if message is None:
            message = f"Concentration limit exceeded for {symbol}. Current: {current_pct}%, Limit: {limit_pct}%"
        super().__init__(message)


class LeverageLimitError(RiskError):
    """Raised when leverage limits are exceeded"""
    
    def __init__(self, current_leverage: str, max_leverage: str, message: str = None):
        self.current_leverage = current_leverage
        self.max_leverage = max_leverage
        if message is None:
            message = f"Leverage limit exceeded. Current: {current_leverage}x, Maximum: {max_leverage}x"
        super().__init__(message)


class MarginCallError(RiskError):
    """Raised when account is in margin call"""
    
    def __init__(self, margin_level: str, call_level: str, message: str = None):
        self.margin_level = margin_level
        self.call_level = call_level
        if message is None:
            message = f"Margin call triggered. Current level: {margin_level}%, Call level: {call_level}%"
        super().__init__(message)


class DailyLossLimitError(RiskError):
    """Raised when daily loss limits are exceeded"""
    
    def __init__(self, current_loss: str, limit_loss: str, message: str = None):
        self.current_loss = current_loss
        self.limit_loss = limit_loss
        if message is None:
            message = f"Daily loss limit exceeded. Current loss: {current_loss}, Limit: {limit_loss}"
        super().__init__(message)


class VaRLimitError(RiskError):
    """Raised when Value at Risk limits are exceeded"""
    
    def __init__(self, current_var: str, limit_var: str, confidence: str = "95%", message: str = None):
        self.current_var = current_var
        self.limit_var = limit_var
        self.confidence = confidence
        if message is None:
            message = f"VaR limit exceeded. Current {confidence} VaR: {current_var}, Limit: {limit_var}"
        super().__init__(message)


# Exchange and Connectivity Exceptions

class ExchangeError(TradingError):
    """Base exception for exchange-related errors"""
    pass


class ExchangeConnectionError(ExchangeError):
    """Raised when exchange connection fails"""
    
    def __init__(self, exchange: str, reason: str, message: str = None):
        self.exchange = exchange
        self.reason = reason
        if message is None:
            message = f"Failed to connect to {exchange}: {reason}"
        super().__init__(message)


class ExchangeAPIError(ExchangeError):
    """Raised when exchange API returns an error"""
    
    def __init__(self, exchange: str, api_error: str, error_code: str = None, message: str = None):
        self.exchange = exchange
        self.api_error = api_error
        self.error_code = error_code
        if message is None:
            message = f"{exchange} API error"
            if error_code:
                message += f" ({error_code})"
            message += f": {api_error}"
        super().__init__(message)


class RateLimitExceededError(ExchangeError):
    """Raised when exchange rate limits are exceeded"""
    
    def __init__(self, exchange: str, retry_after: int = None, message: str = None):
        self.exchange = exchange
        self.retry_after = retry_after
        if message is None:
            message = f"Rate limit exceeded for {exchange}"
            if retry_after:
                message += f". Retry after {retry_after} seconds"
        super().__init__(message)


class InsufficientLiquidityError(ExchangeError):
    """Raised when exchange has insufficient liquidity for an order"""
    
    def __init__(self, exchange: str, symbol: str, requested_amount: str, available_liquidity: str, message: str = None):
        self.exchange = exchange
        self.symbol = symbol
        self.requested_amount = requested_amount
        self.available_liquidity = available_liquidity
        if message is None:
            message = f"Insufficient liquidity on {exchange} for {symbol}. Requested: {requested_amount}, Available: {available_liquidity}"
        super().__init__(message)


# Data and Market Exceptions

class MarketDataError(TradingError):
    """Base exception for market data errors"""
    pass


class PriceDataNotAvailableError(MarketDataError):
    """Raised when price data is not available for a symbol"""
    
    def __init__(self, symbol: str, exchange: str = None, message: str = None):
        self.symbol = symbol
        self.exchange = exchange
        if message is None:
            message = f"Price data not available for {symbol}"
            if exchange:
                message += f" on {exchange}"
        super().__init__(message)


class StaleDataError(MarketDataError):
    """Raised when market data is too old to be reliable"""
    
    def __init__(self, symbol: str, data_age: str, max_age: str, message: str = None):
        self.symbol = symbol
        self.data_age = data_age
        self.max_age = max_age
        if message is None:
            message = f"Stale data for {symbol}. Data age: {data_age}, Max allowed: {max_age}"
        super().__init__(message)


# Configuration and System Exceptions

class ConfigurationError(TradingError):
    """Raised when there are configuration errors"""
    pass


class SystemError(TradingError):
    """Raised for system-level trading errors"""
    pass


class MaintenanceModeError(SystemError):
    """Raised when system is in maintenance mode"""
    
    def __init__(self, message: str = "Trading system is in maintenance mode"):
        super().__init__(message)


class CircuitBreakerError(SystemError):
    """Raised when circuit breaker is triggered"""
    
    def __init__(self, reason: str, message: str = None):
        self.reason = reason
        if message is None:
            message = f"Circuit breaker triggered: {reason}"
        super().__init__(message)


# Portfolio and Analytics Exceptions

class PortfolioError(TradingError):
    """Base exception for portfolio-related errors"""
    pass


class CurrencyConversionError(PortfolioError):
    """Raised when currency conversion fails"""
    
    def __init__(self, from_currency: str, to_currency: str, message: str = None):
        self.from_currency = from_currency
        self.to_currency = to_currency
        if message is None:
            message = f"Failed to convert from {from_currency} to {to_currency}"
        super().__init__(message)


class BenchmarkDataError(PortfolioError):
    """Raised when benchmark data is not available"""
    
    def __init__(self, benchmark: str, message: str = None):
        self.benchmark = benchmark
        if message is None:
            message = f"Benchmark data not available for {benchmark}"
        super().__init__(message)


# Strategy and Algorithm Exceptions

class StrategyError(TradingError):
    """Base exception for trading strategy errors"""
    pass


class StrategyValidationError(StrategyError):
    """Raised when strategy validation fails"""
    
    def __init__(self, strategy_name: str, errors: list, message: str = None):
        self.strategy_name = strategy_name
        self.errors = errors
        if message is None:
            message = f"Strategy validation failed for {strategy_name}: {', '.join(errors)}"
        super().__init__(message)


class BacktestError(StrategyError):
    """Raised when backtesting fails"""
    
    def __init__(self, strategy_name: str, reason: str, message: str = None):
        self.strategy_name = strategy_name
        self.reason = reason
        if message is None:
            message = f"Backtest failed for {strategy_name}: {reason}"
        super().__init__(message)


class SignalGenerationError(StrategyError):
    """Raised when strategy signal generation fails"""
    
    def __init__(self, strategy_name: str, symbol: str, reason: str, message: str = None):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.reason = reason
        if message is None:
            message = f"Signal generation failed for {strategy_name} on {symbol}: {reason}"
        super().__init__(message)