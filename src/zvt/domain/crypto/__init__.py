# -*- coding: utf-8 -*-
# ZVT Crypto Domain Module
# This file contains all crypto-related entities and schemas

from .crypto_meta import CryptoAsset, CryptoPair, CryptoPerp
from .crypto_kdata_common import CryptoKdataCommon, CryptoTickCommon
from .crypto_tick import CryptoTrade, CryptoOrderbook, CryptoFunding
from .crypto_trading import (
    OrderSide, OrderType, OrderStatus, PositionSide,
    CryptoOrder, CryptoPosition, CryptoTrade as TradingTrade,
    CryptoPortfolio, CryptoRiskLimit
)

# Auto-generated kdata schemas (will be populated by schema generator)
# CryptoPair kdata schemas
# CryptoPerp kdata schemas

__all__ = [
    # Meta entities
    "CryptoAsset", 
    "CryptoPair", 
    "CryptoPerp",
    # Common schemas
    "CryptoKdataCommon",
    "CryptoTickCommon", 
    # Tick-level schemas
    "CryptoTrade",
    "CryptoOrderbook", 
    "CryptoFunding",
    # Trading enums
    "OrderSide",
    "OrderType", 
    "OrderStatus",
    "PositionSide",
    # Trading entities
    "CryptoOrder",
    "CryptoPosition", 
    "TradingTrade",  # Renamed to avoid conflict with CryptoTrade
    "CryptoPortfolio",
    "CryptoRiskLimit"
]