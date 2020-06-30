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

if zvt_env['db_engine'] and zvt_env['db_engine'] == "mysql":
    mysqlsql_engine = create_engine("mysql://zvt:jinniuzvt321@123.103.74.231/zvt", echo=False)

    # provider_dbname -> engine
    db_engine_map = {
        "joinquant_stock_meta": mysqlsql_engine,
        "eastmoney_block_1d_kdata": mysqlsql_engine,
        "joinquant_stock_1mon_kdata": mysqlsql_engine,
        "eastmoney_block_1mon_kdata": mysqlsql_engine,
        "joinquant_stock_1wk_hfq_kdata": mysqlsql_engine,
        "eastmoney_block_1wk_kdata": mysqlsql_engine,
        "joinquant_stock_1wk_kdata": mysqlsql_engine,
        "eastmoney_dividend_financing": mysqlsql_engine,
        "joinquant_stock_30m_hfq_kdata": mysqlsql_engine,
        "eastmoney_finance": mysqlsql_engine,
        "joinquant_stock_30m_kdata": mysqlsql_engine,
        "eastmoney_holder": mysqlsql_engine,
        "joinquant_stock_4h_hfq_kdata": mysqlsql_engine,
        "eastmoney_stock_meta": mysqlsql_engine,
        "joinquant_stock_4h_kdata": mysqlsql_engine,
        "eastmoney_trading": mysqlsql_engine,
        "joinquant_stock_5m_hfq_kdata": mysqlsql_engine,
        "exchange_overall": mysqlsql_engine,
        "joinquant_stock_5m_kdata": mysqlsql_engine,
        "exchange_stock_meta": mysqlsql_engine,
        "joinquant_trade_day": mysqlsql_engine,
        "joinquant_overall": mysqlsql_engine,
        "joinquant_valuation": mysqlsql_engine,
        "joinquant_stock_15m_hfq_kdata": mysqlsql_engine,
        "sina_etf_1d_kdata": mysqlsql_engine,
        "joinquant_stock_15m_kdata": mysqlsql_engine,
        "sina_index_1d_kdata": mysqlsql_engine,
        "joinquant_stock_1d_hfq_kdata": mysqlsql_engine,
        "sina_money_flow": mysqlsql_engine,
        "joinquant_stock_1d_kdata": mysqlsql_engine,
        "sina_stock_meta": mysqlsql_engine,
        "joinquant_stock_1h_hfq_kdata": mysqlsql_engine,
        "zvt_stock_1d_ma_factor": mysqlsql_engine,
        "joinquant_stock_1h_kdata": mysqlsql_engine,
        "zvt_stock_1d_ma_stats": mysqlsql_engine,
        "joinquant_stock_1m_hfq_kdata": mysqlsql_engine,
        "zvt_stock_1d_zen_factor": mysqlsql_engine,
        "joinquant_stock_1m_kdata": mysqlsql_engine,
        "zvt_stock_1wk_ma_stats": mysqlsql_engine,
        "joinquant_stock_1mon_hfq_kdata": mysqlsql_engine,
        "zvt_trader_info": mysqlsql_engine,
    }
else:
    db_engine_map = {}

# provider_dbname -> session
db_session_map = {}

# provider -> [db_name1,db_name2...]
provider_map_dbnames = {
    "joinquant": ["zvt"]

}

# db_name -> [declarative_base1,declarative_base2...]
dbname_map_base = {}

# db_name -> [declarative_meta1,declarative_meta2...]
dbname_map_schemas = {}

# entity_type -> schema
entity_map_schemas = {}
