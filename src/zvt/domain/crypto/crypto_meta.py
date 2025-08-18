# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract import TradableEntity
from zvt.contract.register import register_schema, register_entity

CryptoMetaBase = declarative_base()


#: Base cryptocurrency asset (BTC, ETH, etc.)
@register_entity(entity_type="crypto")
class CryptoAsset(CryptoMetaBase, TradableEntity):
    __tablename__ = "crypto_asset"
    
    #: Symbol (BTC, ETH, USDT, etc.)
    symbol = Column(String(length=32))
    #: Full name (Bitcoin, Ethereum, etc.)
    full_name = Column(String(length=128))
    #: Max supply (21M for BTC, null for ETH)
    max_supply = Column(Float)
    #: Circulating supply
    circulating_supply = Column(Float)
    #: Total supply
    total_supply = Column(Float)
    #: Market cap in USD
    market_cap = Column(Float)
    #: Is stablecoin flag
    is_stablecoin = Column(Boolean, default=False)
    #: Consensus mechanism (PoW, PoS, etc.)
    consensus_mechanism = Column(String(length=64))
    
    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None):
        """Crypto trades 24/7 - all dates are trading dates"""
        import pandas as pd
        return pd.date_range(start_date, end_date, freq="D")
    
    @classmethod
    def get_trading_intervals(cls, include_bidding_time=False):
        """Crypto trades 24/7 - always in trading time"""
        return [("00:00", "24:00")]


#: Cryptocurrency spot trading pair (BTC/USDT, ETH/BTC, etc.)
@register_entity(entity_type="cryptopair")
class CryptoPair(CryptoMetaBase, TradableEntity):
    __tablename__ = "crypto_pair"
    
    #: Base asset symbol (BTC in BTC/USDT)
    base_symbol = Column(String(length=32))
    #: Quote asset symbol (USDT in BTC/USDT)
    quote_symbol = Column(String(length=32))
    #: Base asset ID reference
    base_asset_id = Column(String(length=128))
    #: Quote asset ID reference  
    quote_asset_id = Column(String(length=128))
    
    #: Trading precision and constraints
    #: Minimum price increment (tick size)
    price_step = Column(Float)
    #: Minimum quantity increment (lot size)
    qty_step = Column(Float)
    #: Minimum notional value for orders
    min_notional = Column(Float)
    #: Maximum order size
    max_order_size = Column(Float)
    
    #: Fee structure
    #: Maker fee rate (negative means rebate)
    maker_fee = Column(Float)
    #: Taker fee rate
    taker_fee = Column(Float)
    
    #: Trading status
    is_active = Column(Boolean, default=True)
    #: Is margin trading enabled
    margin_enabled = Column(Boolean, default=False)
    
    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None):
        """Crypto trades 24/7 - all dates are trading dates"""
        import pandas as pd
        return pd.date_range(start_date, end_date, freq="D")
    
    @classmethod
    def get_trading_intervals(cls, include_bidding_time=False):
        """Crypto trades 24/7 - always in trading time"""
        return [("00:00", "24:00")]


#: Cryptocurrency perpetual futures contract
@register_entity(entity_type="cryptoperp")  
class CryptoPerp(CryptoMetaBase, TradableEntity):
    __tablename__ = "crypto_perp"
    
    #: Underlying asset symbol (BTC in BTCUSDT-PERP)
    underlying_symbol = Column(String(length=32))
    #: Settlement asset symbol (USDT)
    settlement_symbol = Column(String(length=32))
    #: Underlying asset ID reference
    underlying_asset_id = Column(String(length=128))
    #: Settlement asset ID reference
    settlement_asset_id = Column(String(length=128))
    
    #: Contract specifications
    #: Contract size (usually 1 for crypto perps)
    contract_size = Column(Float, default=1.0)
    #: Price precision
    price_step = Column(Float)
    #: Quantity precision  
    qty_step = Column(Float)
    #: Minimum notional value
    min_notional = Column(Float)
    #: Maximum order size
    max_order_size = Column(Float)
    
    #: Fee structure
    maker_fee = Column(Float)
    taker_fee = Column(Float)
    
    #: Perpetual-specific fields
    #: Funding interval in hours (usually 8)
    funding_interval_hours = Column(Integer, default=8)
    #: Maximum leverage allowed
    max_leverage = Column(Float)
    #: Default leverage
    default_leverage = Column(Float, default=1.0)
    #: Position modes supported (one-way, hedge, both)
    position_modes = Column(String(length=64), default="both")
    
    #: Risk management
    #: Maintenance margin rate
    maintenance_margin_rate = Column(Float)
    #: Initial margin rate
    initial_margin_rate = Column(Float)
    
    #: Trading status
    is_active = Column(Boolean, default=True)
    
    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None):
        """Crypto trades 24/7 - all dates are trading dates"""
        import pandas as pd
        return pd.date_range(start_date, end_date, freq="D")
    
    @classmethod
    def get_trading_intervals(cls, include_bidding_time=False):
        """Crypto trades 24/7 - always in trading time"""
        return [("00:00", "24:00")]


# Register the schema with providers - will be updated as providers are added
register_schema(
    providers=["binance", "okx", "bybit", "coinbase", "ccxt"], 
    db_name="crypto_meta", 
    schema_base=CryptoMetaBase
)

# Export all entities
__all__ = ["CryptoAsset", "CryptoPair", "CryptoPerp"]