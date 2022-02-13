====================
Core concepts
====================

Entity
    the existence described by itself, classification of existential concepts.

EntityEvent
    the event happened on the entity.

TradableEntity
    the Entity could be traded, e.g, Stock, Future.

ActorEntity
    the Entity acting in market, e.g, Fund, Individual, Government.

IntervalLevel
    repeated fixed time interval, e.g, 5m, 1d.

Schema
    the data structure with fields, one schema could have multiple storage with different Providers.

Kdata(Quote)
    the candlestick data with OHLC.

Provider
    the data provider.

Storage
    the sql database, e.g, sqlite, mysql.

Recorder
    class for recording data for Schema.

Factor
    data describing market.It's computed from from Schema, and save as new Schema if need.

TargetSelector
    the class select targets according to Factor.

Trader
    the backtest engine using TargetSelector, MLMachine or free style.

Tagger
    classify TradableEntity by different dimensions, could be used as ml category feature.

MLMachine
    the ml engine.

TradingSignal
    the signal contains information about how to trade.

Drawer
    the class for draw charts.

Intent
    what do you want to do, e.g. compare, distribute, composite.

Normal data
    the pandas dataframe with multiple index which level 0 is entity_id and level 1 is timestamp:

===============                 ==========        =====   =====   =====   =====
entity_id                       timestamp         col1    col2    col3    col4
===============                 ==========        =====   =====   =====   =====
stock_sz_000338                 2020-05-05        1.2     0.5     0.3     a
...                             2020-05-06        1.0     0.7     0.2     b
stock_sz_000778                 2020-05-05        1.2     0.5     0.3     a
...                             2020-05-06        1.0     0.7     0.2     b
===============                 ==========        =====   =====   =====   =====
