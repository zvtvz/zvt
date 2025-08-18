# -*- coding: utf-8 -*-
import pytest
from datetime import datetime
from zvt.domain.crypto import Crypto, CryptoDetail
from zvt.contract import IntervalLevel


def test_crypto_entity_creation():
    """Test basic crypto entity creation and validation"""
    crypto = Crypto(
        id="crypto_binance_BTC",
        entity_id="crypto_binance_BTC", 
        entity_type="crypto",
        exchange="binance",
        code="BTC",
        name="Bitcoin",
        timestamp=datetime(2009, 1, 3),
        list_date=datetime(2009, 1, 3)
    )
    
    assert crypto.entity_type == "crypto"
    assert crypto.code == "BTC"
    assert crypto.name == "Bitcoin"
    assert crypto.exchange == "binance"


def test_crypto_market_cap_validation():
    """Test market cap calculations and validation"""
    crypto = Crypto(
        id="crypto_binance_BTC",
        entity_id="crypto_binance_BTC",
        entity_type="crypto", 
        exchange="binance",
        code="BTC",
        name="Bitcoin",
        total_cap=1000000000000.0,  # 1T USD
        circulating_cap=800000000000.0,  # 800B USD
        timestamp=datetime.now()
    )
    
    assert crypto.total_cap == 1000000000000.0
    assert crypto.circulating_cap == 800000000000.0
    assert crypto.circulating_cap <= crypto.total_cap


def test_crypto_trading_time_24_7():
    """Test that crypto markets are always trading (24/7)"""
    crypto = Crypto()
    
    # Crypto markets trade 24/7, so these should always return True for trading
    assert crypto.in_trading_time(timestamp="2024-01-01 00:00:00") is True
    assert crypto.in_trading_time(timestamp="2024-01-01 12:00:00") is True  
    assert crypto.in_trading_time(timestamp="2024-12-25 23:59:59") is True  # Christmas
    assert crypto.in_trading_time(timestamp="2024-01-01 06:30:00") is True  # Weekend
    
    # Never before or after trading time since it's 24/7
    assert crypto.before_trading_time(timestamp="2024-01-01 00:00:00") is False
    assert crypto.after_trading_time(timestamp="2024-01-01 23:59:59") is False


def test_crypto_symbol_normalization():
    """Test crypto symbol pair normalization"""
    btc_usd = Crypto(
        id="crypto_binance_BTCUSD",
        entity_id="crypto_binance_BTCUSD",
        entity_type="crypto",
        exchange="binance", 
        code="BTCUSD",
        name="Bitcoin/USD"
    )
    
    eth_btc = Crypto(
        id="crypto_binance_ETHBTC", 
        entity_id="crypto_binance_ETHBTC",
        entity_type="crypto",
        exchange="binance",
        code="ETHBTC", 
        name="Ethereum/Bitcoin"
    )
    
    assert btc_usd.code == "BTCUSD"
    assert eth_btc.code == "ETHBTC"


def test_crypto_detail_metadata():
    """Test crypto detail metadata storage"""
    detail = CryptoDetail(
        id="crypto_binance_BTC",
        entity_id="crypto_binance_BTC",
        entity_type="crypto",
        exchange="binance",
        code="BTC", 
        name="Bitcoin",
        contract_address=None,  # Native blockchain asset
        blockchain="bitcoin",
        consensus="proof_of_work",
        max_supply=21000000.0,
        total_supply=19000000.0,
        market_rank=1,
        description="Digital currency and payment system"
    )
    
    assert detail.blockchain == "bitcoin"
    assert detail.consensus == "proof_of_work"
    assert detail.max_supply == 21000000.0
    assert detail.market_rank == 1
    assert detail.contract_address is None


def test_crypto_stablecoin_properties():
    """Test stablecoin specific properties"""
    usdc = CryptoDetail(
        id="crypto_binance_USDC",
        entity_id="crypto_binance_USDC", 
        entity_type="crypto",
        exchange="binance",
        code="USDC",
        name="USD Coin",
        contract_address="0xa0b86a33e6c83bb0b2c5686ce1c3c8d4c9e6b1a2",
        blockchain="ethereum", 
        consensus="proof_of_stake",
        is_stablecoin=True,
        peg_currency="USD",
        collateral_type="fiat"
    )
    
    assert usdc.is_stablecoin is True
    assert usdc.peg_currency == "USD"
    assert usdc.collateral_type == "fiat"
    assert usdc.contract_address is not None


def test_crypto_defi_token_properties():
    """Test DeFi token specific properties"""
    uni = CryptoDetail(
        id="crypto_binance_UNI",
        entity_id="crypto_binance_UNI",
        entity_type="crypto", 
        exchange="binance",
        code="UNI",
        name="Uniswap",
        contract_address="0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        blockchain="ethereum",
        token_type="governance",
        protocol="uniswap",
        category="defi"
    )
    
    assert uni.token_type == "governance"
    assert uni.protocol == "uniswap" 
    assert uni.category == "defi"


def test_crypto_interval_level_support():
    """Test that crypto supports all interval levels including tick data"""
    crypto = Crypto()
    
    # Crypto should support all interval levels
    supported_levels = [
        IntervalLevel.LEVEL_TICK,
        IntervalLevel.LEVEL_1MIN, 
        IntervalLevel.LEVEL_5MIN,
        IntervalLevel.LEVEL_15MIN,
        IntervalLevel.LEVEL_30MIN,
        IntervalLevel.LEVEL_1HOUR,
        IntervalLevel.LEVEL_4HOUR,
        IntervalLevel.LEVEL_1DAY,
        IntervalLevel.LEVEL_1WEEK
    ]
    
    for level in supported_levels:
        assert crypto.support_interval(level) is True