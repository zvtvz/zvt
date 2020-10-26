# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from zvt import zvt_env

# all registered providers
providers = []

# all registered entity types
entity_types = []

# all registered schemas
schemas = []

# entity_type -> schema
entity_schema_map = {}

# global sessions
sessions = {}

if "db_engine" in zvt_env and zvt_env['db_engine'] == "mysql":
    mysql_engine = create_engine(
        f"mysql://{zvt_env['mysql_username']}:{zvt_env['mysql_password']}@{zvt_env['mysql_server_address']}:"
        f"{zvt_env['mysql_server_port']}/{zvt_env['db_name']}?charset=utf8mb4", pool_recycle=3600, echo=False)

    # provider_dbname -> engine
    db_engine_map = {
        "joinquant_stock_meta": mysql_engine,
        "joinquant_block": mysql_engine,
        "joinquant_block_stock": mysql_engine,
        "joinquant_block_1d_kdata": mysql_engine,
        "joinquant_shares_change": mysql_engine,
        "joinquant_finance": mysql_engine,
        "joinquant_stock_factor": mysql_engine,
        "eastmoney_block_1d_kdata": mysql_engine,
        "eastmoney_holder_trading": mysql_engine,
        "joinquant_holder_trading": mysql_engine,
        "joinquant_stock_1mon_kdata": mysql_engine,
        "eastmoney_block_1mon_kdata": mysql_engine,
        "joinquant_stock_1wk_hfq_kdata": mysql_engine,
        "joinquant_stock_1mon_bfq_kdata": mysql_engine,
        "eastmoney_block_1wk_kdata": mysql_engine,
        "joinquant_stock_1wk_kdata": mysql_engine,
        "eastmoney_dividend_financing": mysql_engine,
        "joinquant_dividend_financing": mysql_engine,
        "emquantapi_dividend_financing": mysql_engine,
        "emquantapi_stock_meta": mysql_engine,
        "emquantapi_finance_qtr": mysql_engine,
        "joinquant_stock_30m_hfq_kdata": mysql_engine,
        "eastmoney_finance": mysql_engine,
        "emquantapi_finance": mysql_engine,
        "joinquant_stock_30m_kdata": mysql_engine,
        "eastmoney_holder": mysql_engine,
        "joinquant_holder": mysql_engine,
        "emquantapi_holder": mysql_engine,
        "eastmoney_manager_trading": mysql_engine,
        "joinquant_stock_4h_hfq_kdata": mysql_engine,
        "eastmoney_stock_meta": mysql_engine,
        "joinquant_stock_4h_kdata": mysql_engine,
        "eastmoney_trading": mysql_engine,
        "joinquant_trading": mysql_engine,
        "emquantapi_trading": mysql_engine,
        "joinquant_stock_5m_hfq_kdata": mysql_engine,
        "exchange_overall": mysql_engine,
        "joinquant_stock_5m_kdata": mysql_engine,
        "exchange_stock_meta": mysql_engine,
        "joinquant_trade_day": mysql_engine,
        "joinquant_overall": mysql_engine,
        "joinquant_valuation": mysql_engine,
        "emquantapi_valuation": mysql_engine,
        "joinquant_stock_15m_hfq_kdata": mysql_engine,
        "sina_etf_1d_kdata": mysql_engine,
        "joinquant_stock_15m_kdata": mysql_engine,
        "sina_index_1d_kdata": mysql_engine,
        "sina_index_1wk_kdata": mysql_engine,
        "sina_index_1mon_kdata": mysql_engine,
        "joinquant_fund_net_value": mysql_engine,

        "joinquant_index_1wk_kdata": mysql_engine,
        "joinquant_index_1mon_kdata": mysql_engine,

        "joinquant_stock_1d_hfq_kdata": mysql_engine,
        "sina_money_flow": mysql_engine,
        "joinquant_stock_1d_kdata": mysql_engine,
        "sina_stock_meta": mysql_engine,
        "joinquant_stock_1h_hfq_kdata": mysql_engine,
        "zvt_stock_1d_ma_factor": mysql_engine,
        "joinquant_stock_1h_kdata": mysql_engine,
        "zvt_stock_1d_ma_stats": mysql_engine,
        "joinquant_stock_1m_hfq_kdata": mysql_engine,
        "zvt_stock_1d_zen_factor": mysql_engine,
        "joinquant_stock_1m_kdata": mysql_engine,
        "zvt_stock_1wk_ma_stats": mysql_engine,
        "joinquant_stock_1mon_hfq_kdata": mysql_engine,
        "zvt_trader_info": mysql_engine,
        "joinquant_index_1d_kdata": mysql_engine,
        "joinquant_stock_1wk_bfq_kdata": mysql_engine,
        "joinquant_stock_1d_bfq_kdata": mysql_engine,
        "joinquant_etf_1d_kdata": mysql_engine,
        "joinquant_etf_1d_bfq_kdata": mysql_engine,
        "joinquant_etf_1d_hfq_kdata": mysql_engine,

        "joinquant_stock_emotion_factor": mysql_engine,
        "joinquant_stock_basics_factor": mysql_engine,
        "joinquant_stock_growth_factor": mysql_engine,
        "joinquant_stock_momentum_factor": mysql_engine,
        "joinquant_stock_pershare_factor": mysql_engine,
        "joinquant_stock_quality_factor": mysql_engine,
        "joinquant_stock_risk_factor": mysql_engine,
        "joinquant_stock_style_factor": mysql_engine,
        "joinquant_stock_technical_factor": mysql_engine,

    }
else:
    db_engine_map = {}

# provider_dbname -> session
db_session_map = {}

# provider -> [db_name1,db_name2...]
provider_map_dbnames = {}

# db_name -> [declarative_base1,declarative_base2...]
dbname_map_base = {}

# db_name -> [declarative_meta1,declarative_meta2...]
dbname_map_schemas = {}

# entity_type -> schema
entity_map_schemas = {}
