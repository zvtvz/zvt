====================
Intro
====================
This is a short introduction to zvt, you would learn the basic usage and
glance a global view here.


Rethink market and programming
------------------------------
For practical trading, complex algorithm is fragile, complex algorithm building
on complex facility is more fragile, complex algorithm building on complex
facility by a complex team is more and more fragile.

zvt want to provide a simple facility for building straightforward algorithm, it
should be:

* use the most basic programming concepts
* concise abstraction of the market
* correctness is obvious

Core concepts building zvt
------------------------------
Technologies come and technologies go, but market insight is forever.
The core concepts is about market insight.Below would introduce them by usage.

entity
------------------------------
The existence described by itself, classification of existential concepts.

In the world of zvt, there are two kinds of entities, one is :ref:`tradable entity <intro.tradable_entity>`,
and the other is :ref:`actor entity <intro.tradable_entity>`. Data is the event happened on them.

.. _intro.tradable_entity:

tradable entity
------------------------------
:class:`~.zvt.contract.schema.TradableEntity` is anything could be traded, it could be :class:`~.zvt.domain.meta.stock_meta.Stock`,
:class:`~.zvt.domain.meta.stock_meta.Etf`, :class:`~.zvt.domain.meta.stock_meta.Index`, future,
or any valuable thing.

record and query stock:
::

    >>> from zvt.domain import Stock
    >>> Stock.record_data()
    >>> df = Stock.query_data()
    >>> print(df)
                       id        entity_id  timestamp entity_type exchange    code   name  list_date end_date
    0     stock_sh_600651  stock_sh_600651 1986-09-26       stock       sh  600651  *ST飞乐 1986-09-26     None
    1     stock_sz_000004  stock_sz_000004 1990-12-01       stock       sz  000004   国华网安 1990-12-01     None
    2     stock_sz_000005  stock_sz_000005 1990-12-10       stock       sz  000005   世纪星源 1990-12-10     None
    3     stock_sh_600601  stock_sh_600601 1990-12-19       stock       sh  600601   方正科技 1990-12-19     None
    4     stock_sh_600602  stock_sh_600602 1990-12-19       stock       sh  600602   云赛智联 1990-12-19     None
    ...               ...              ...        ...         ...      ...     ...    ...        ...      ...
    4615  stock_sh_603176  stock_sh_603176 2021-12-31       stock       sh  603176   汇通集团 2021-12-31     None
    4616  stock_sh_600941  stock_sh_600941 2022-01-05       stock       sh  600941   中国移动 2022-01-05     None
    4617  stock_sh_688262  stock_sh_688262 2022-01-06       stock       sh  688262   国芯科技 2022-01-06     None
    4618  stock_sh_688176  stock_sh_688176 2022-01-07       stock       sh  688176   亚虹医药 2022-01-07     None
    4619  stock_sz_301159  stock_sz_301159 2022-01-07       stock       sz  301159    N三维 2022-01-07     None

    [4620 rows x 9 columns]

record and query stockus:
::

    >>> from zvt.domain import Stockus
    >>> Stockus.record_data()
    >>> df = Stockus.query_data()
    >>> print(df)
                           id            entity_id timestamp entity_type exchange  code                             name list_date end_date
    0     stockus_nasdaq_CMII  stockus_nasdaq_CMII      None     stockus   nasdaq  CMII        CM Life Sciences II Inc-A      None     None
    1     stockus_nasdaq_CBLI  stockus_nasdaq_CBLI      None     stockus   nasdaq  CBLI                      Cytocom Inc      None     None
    2       stockus_nyse_XPOw    stockus_nyse_XPOw      None     stockus     nyse  XPOw             XPO Logistics Inc WI      None     None
    3        stockus_nyse_WRI     stockus_nyse_WRI      None     stockus     nyse   WRI                        魏因加滕房地产投资      None     None
    4       stockus_nyse_PROS    stockus_nyse_PROS      None     stockus     nyse  PROS              ProSight Global Inc      None     None
    ...                   ...                  ...       ...         ...      ...   ...                              ...       ...      ...
    6345    stockus_nyse_FATH    stockus_nyse_FATH      None     stockus     nyse  FATH  Fathom Digital Manufacturing Co      None     None
    6346    stockus_nyse_LOCL    stockus_nyse_LOCL      None     stockus     nyse  LOCL                Local Bounti Corp      None     None
    6347     stockus_nyse_VLD     stockus_nyse_VLD      None     stockus     nyse   VLD                       Velo3D Inc      None     None
    6348     stockus_nyse_AHI     stockus_nyse_AHI      None     stockus     nyse   AHI   Advanced Human Imaging Ltd ADR      None     None
    6349    stockus_nyse_HLGN    stockus_nyse_HLGN      None     stockus     nyse  HLGN                     Heliogen Inc      None     None

what about other tradable entities?
::

    >>> from zvt.contract import zvt_context
    >>> zvt_context.tradable_schema_map
    {'stockus': zvt.domain.meta.stockus_meta.Stockus,
     'stockhk': zvt.domain.meta.stockhk_meta.Stockhk,
     'index': zvt.domain.meta.index_meta.Index,
     'etf': zvt.domain.meta.etf_meta.Etf,
     'stock': zvt.domain.meta.stock_meta.Stock,
     'block': zvt.domain.meta.block_meta.Block,
     'fund': zvt.domain.meta.fund_meta.Fund}

From intuition, stockhk should be stock of hongkong:
::

    >>> from zvt.domain import Stockhk
    >>> Stockhk.record_data()
    >>> df = Stockhk.query_data(index='code')
    >>> print(df)

                         id         entity_id timestamp entity_type exchange   code    name list_date end_date
    code
    00001  stockhk_hk_00001  stockhk_hk_00001       NaT     stockhk       hk  00001      长和      None     None
    00002  stockhk_hk_00002  stockhk_hk_00002       NaT     stockhk       hk  00002    中电控股      None     None
    00003  stockhk_hk_00003  stockhk_hk_00003       NaT     stockhk       hk  00003  香港中华煤气      None     None
    00004  stockhk_hk_00004  stockhk_hk_00004       NaT     stockhk       hk  00004   九龙仓集团      None     None
    00005  stockhk_hk_00005  stockhk_hk_00005       NaT     stockhk       hk  00005    汇丰控股      None     None
    ...                 ...               ...       ...         ...      ...    ...     ...       ...      ...
    09996  stockhk_hk_09996  stockhk_hk_09996       NaT     stockhk       hk  09996  沛嘉医疗-B      None     None
    09997  stockhk_hk_09997  stockhk_hk_09997       NaT     stockhk       hk  09997    康基医疗      None     None
    09998  stockhk_hk_09998  stockhk_hk_09998       NaT     stockhk       hk  09998    光荣控股      None     None
    09999  stockhk_hk_09999  stockhk_hk_09999       NaT     stockhk       hk  09999    网易-S      None     None
    80737  stockhk_hk_80737  stockhk_hk_80737       NaT     stockhk       hk  80737  湾区发展-R      None     None

    [2597 rows x 9 columns]

    >>> df[df.code=='00700']

                        id         entity_id timestamp entity_type exchange   code  name list_date end_date
    2112  stockhk_hk_00700  stockhk_hk_00700      None     stockhk       hk  00700  腾讯控股      None     None

From intuition, other tradable entities could be added to the system and used in the same way.

Below is current registered entity_type and its schema.
::

    >>> from zvt.contract import *
    >>> zvt_context.tradable_schema_map
    {'stockus': zvt.domain.meta.stockus_meta.Stockus,
     'stockhk': zvt.domain.meta.stockhk_meta.Stockhk,
     'index': zvt.domain.meta.index_meta.Index,
     'etf': zvt.domain.meta.etf_meta.Etf,
     'stock': zvt.domain.meta.stock_meta.Stock,
     'block': zvt.domain.meta.block_meta.Block,
     'fund': zvt.domain.meta.fund_meta.Fund}

.. _intro.actor_entity:

actor entity
------------------------------
:class:`~.zvt.contract.schema.ActorEntity` is the beings acting in the market, it could be government,
company, fund or individual.

::

    >>> from zvt.domain import StockInstitutionalInvestorHolder
    >>> entity_ids = ["stock_sz_000338", "stock_sz_000001"]
    >>> StockInstitutionalInvestorHolder.record_data(entity_ids=entity_ids)
    >>> df = StockInstitutionalInvestorHolder.query_data(entity_ids=entity_ids)
    >>> print(df)
                                                          id        entity_id  timestamp    code  name                 actor_id   actor_type actor_code         actor_name report_period report_date  holding_numbers  holding_ratio  holding_values
    0       stock_sz_000001_1998-06-30_raised_fund_cn_184688  stock_sz_000001 1998-06-30  000001  平安银行    raised_fund_cn_184688  raised_fund     184688               基金开元     half_year  1998-06-30     1.896697e+06       0.001771    3.269906e+07
    1       stock_sz_000001_1998-09-30_raised_fund_cn_184688  stock_sz_000001 1998-09-30  000001  平安银行    raised_fund_cn_184688  raised_fund     184688               基金开元       season3  1998-09-30     2.634093e+06       0.002460    4.151331e+07
    2       stock_sz_000001_1998-12-31_raised_fund_cn_184688  stock_sz_000001 1998-12-31  000001  平安银行    raised_fund_cn_184688  raised_fund     184688               基金开元          year  1998-12-31     2.673900e+06       0.002497    3.992133e+07
    3       stock_sz_000001_1999-03-31_raised_fund_cn_184688  stock_sz_000001 1999-03-31  000001  平安银行    raised_fund_cn_184688  raised_fund     184688               基金开元       season1  1999-03-31     2.378977e+06       0.002221    3.256820e+07
    4       stock_sz_000001_1999-06-30_raised_fund_cn_500005  stock_sz_000001 1999-06-30  000001  平安银行    raised_fund_cn_500005  raised_fund     500005               基金汉盛     half_year  1999-06-30     4.989611e+06       0.004659    1.386613e+08
    ...                                                  ...              ...        ...     ...   ...                      ...          ...        ...                ...           ...         ...              ...            ...             ...
    22463      stock_sz_000338_2021-09-30_broker_cn_71067063  stock_sz_000338 2021-09-30  000338  潍柴动力       broker_cn_71067063       broker   71067063          东方红信和添安4号       season3  2021-09-30     5.000000e+04       0.000012    8.580000e+05
    22464  stock_sz_000338_2021-09-30_corporation_cn_1003...  stock_sz_000338 2021-09-30  000338  潍柴动力  corporation_cn_10030838  corporation   10030838         潍柴控股集团有限公司       season3  2021-09-30     1.422551e+09       0.018071    2.441097e+10
    22465  stock_sz_000338_2021-09-30_corporation_cn_1067...  stock_sz_000338 2021-09-30  000338  潍柴动力  corporation_cn_10671586  corporation   10671586         香港中央结算有限公司       season3  2021-09-30     4.992710e+08       0.117713    8.567490e+09
    22466  stock_sz_000338_2021-09-30_corporation_cn_1019...  stock_sz_000338 2021-09-30  000338  潍柴动力  corporation_cn_10196008  corporation   10196008       中国证券金融股份有限公司       season3  2021-09-30     1.636089e+08       0.038574    2.807529e+09
    22467  stock_sz_000338_2021-09-30_corporation_cn_1008...  stock_sz_000338 2021-09-30  000338  潍柴动力  corporation_cn_10086358  corporation   10086358  奥地利IVM技术咨询维也纳有限公司       season3  2021-09-30     1.139387e+08       0.026863    1.955188e+09

    [22468 rows x 14 columns]

schema
------------------------------
Data structure describing :class:`~.zvt.contract.schema.TradableEntity`, :class:`~.zvt.contract.schema.ActorEntity` or events happen on them.
Physically it's table with columns in sql database. One schema could have multiple storage
with different providers.

From specific to general, all zvt schema usage is in the same way.

* import
* record_data
* query_data

::

    >>> from zvt.domain import *
    >>> entity_ids = ["stock_sz_000338", "stock_sz_000001"]
    >>> Stock1dHfqKdata.record_data(entity_ids=entity_ids, provider="em")
    >>> df = Stock1dHfqKdata.query_data(entity_ids=entity_ids, provider="em")
    >>> print(df)

                                   id        entity_id  timestamp provider    code  name level     open    close     high      low     volume      turnover  change_pct  turnover_rate
    0      stock_sz_000001_1991-04-03  stock_sz_000001 1991-04-03       em  000001  平安银行    1d    49.00    49.00    49.00    49.00        1.0  5.000000e+03      0.2250         0.0000
    1      stock_sz_000001_1991-04-04  stock_sz_000001 1991-04-04       em  000001  平安银行    1d    48.76    48.76    48.76    48.76        3.0  1.500000e+04     -0.0049         0.0000
    2      stock_sz_000001_1991-04-05  stock_sz_000001 1991-04-05       em  000001  平安银行    1d    48.52    48.52    48.52    48.52        2.0  1.000000e+04     -0.0049         0.0000
    3      stock_sz_000001_1991-04-06  stock_sz_000001 1991-04-06       em  000001  平安银行    1d    48.28    48.28    48.28    48.28        7.0  3.400000e+04     -0.0049         0.0000
    4      stock_sz_000001_1991-04-08  stock_sz_000001 1991-04-08       em  000001  平安银行    1d    48.04    48.04    48.04    48.04        2.0  1.000000e+04     -0.0050         0.0000
    ...                           ...              ...        ...      ...     ...   ...   ...      ...      ...      ...      ...        ...           ...         ...            ...
    10859  stock_sz_000338_2022-01-10  stock_sz_000338 2022-01-10       em  000338  潍柴动力    1d   314.38   314.38   320.37   312.69   956271.0  1.735153e+09      0.0149         0.0190
    10860  stock_sz_000001_2022-01-11  stock_sz_000001 2022-01-11       em  000001  平安银行    1d  2974.07  2998.45  3019.58  2954.57  1581999.0  2.752485e+09      0.0121         0.0082
    10861  stock_sz_000338_2022-01-11  stock_sz_000338 2022-01-11       em  000338  潍柴动力    1d   312.69   307.01   314.23   306.70   812187.0  1.444640e+09     -0.0234         0.0161
    10862  stock_sz_000001_2022-01-12  stock_sz_000001 2022-01-12       em  000001  平安银行    1d  2998.45  2931.82  3004.95  2915.56  1502164.0  2.561266e+09     -0.0222         0.0077
    10863  stock_sz_000338_2022-01-12  stock_sz_000338 2022-01-12       em  000338  潍柴动力    1d   307.01   305.78   309.62   302.86   882165.0  1.542044e+09     -0.0040         0.0175

    [10864 rows x 15 columns]

The data of the schema is recorded in local database by default and could be updated incrementally.

Find them in this way:
::

    >>> Stock1dHfqKdata.get_storages()
    [Engine(sqlite:////Users/foolcage/zvt-home/data/joinquant_stock_1d_hfq_kdata.db?check_same_thread=False),
     Engine(sqlite:////Users/foolcage/zvt-home/data/em_stock_1d_hfq_kdata.db?check_same_thread=False)]

level
------------------------------
:class:`~.zvt.contract.IntervalLevel` is repeated fixed time interval, e.g, 5m, 1d.
It's used in candlestick for describing time window.


::

    >>> from zvt.contract import *
    >>> for level in IntervalLevel:
    >>>     print(level.value)
    tick
    1m
    5m
    15m
    30m
    1h
    4h
    1d
    1wk
    1mon

Kdata(Quote)
------------------------------
the candlestick data with OHLC.

the :class:`~.zvt.contract.schema.TradableEntity` quote schema name follows below rules:

::

    {entity_shema}{level}{adjust_type}Kdata

* entity_schema

TradableEntity class，e.g. Stock,Stockus.

* level

IntervalLevel value, e.g. 1d,1wk.

* adjust type

pre adjusted(qfq), post adjusted(hfq), or not adjusted(bfq).

::

    >>> for adjust_type in AdjustType:
    >>>     print(adjust_type.value)

.. note:
    In order to be compatible with historical data, the qfq is an exception, {adjust_type} is left empty

The pre defined kdata schema could be in :module:`~.zvt.domain.quotes`, it's seperated by
entity_schema, level, and adjust type.

Normal data
------------------------------
the pandas dataframe with multiple index which level 0 named entity_id and level 1 named timestamp:

===============                 ==========        =====   =====   =====   =====
entity_id                       timestamp         col1    col2    col3    col4
===============                 ==========        =====   =====   =====   =====
stock_sz_000338                 2020-05-05        1.2     0.5     0.3     a
...                             2020-05-06        1.0     0.7     0.2     b
stock_sz_000778                 2020-05-05        1.2     0.5     0.3     a
...                             2020-05-06        1.0     0.7     0.2     b
===============                 ==========        =====   =====   =====   =====


Factor
------------------------------
Data describing market. It reads data from Schema, use Transformer, Accumulator
or your custom logic to compute, and save the result if need.

* Transformer

Computing factor which depends on input data only.

Below is an example computing ma factor:

::

    class MaTransformer(Transformer):
        def __init__(self, windows=None, cal_change_pct=False) -> None:
            super().__init__()
            if windows is None:
                windows = [5, 10]
            self.windows = windows
            self.cal_change_pct = cal_change_pct

        def transform(self, input_df: pd.DataFrame) -> pd.DataFrame:
            if self.cal_change_pct:
                group_pct = group_by_entity_id(input_df["close"]).pct_change()
                input_df["change_pct"] = normalize_group_compute_result(group_pct)

            for window in self.windows:
                col = "ma{}".format(window)
                self.indicators.append(col)

                group_ma = group_by_entity_id(input_df["close"]).rolling(window=window, min_periods=window).mean()
                input_df[col] = normalize_group_compute_result(group_ma)

            return input_df

* Accumulator

Computing factor which depends on input data and previous state of the factor.

Below is an example computing ma states:

::

    class MaStatsAccumulator(Accumulator):
        def __init__(self, acc_window: int = 250, windows=None, vol_windows=None) -> None:
            super().__init__(acc_window)
            self.windows = windows
            self.vol_windows = vol_windows

        def acc_one(self, entity_id, df: pd.DataFrame, acc_df: pd.DataFrame, state: dict) -> (pd.DataFrame, dict):
            self.logger.info(f"acc_one:{entity_id}")
            if pd_is_not_null(acc_df):
                df = df[df.index > acc_df.index[-1]]
                if pd_is_not_null(df):
                    self.logger.info(f'compute from {df.iloc[0]["timestamp"]}')
                    acc_df = pd.concat([acc_df, df])
                else:
                    self.logger.info("no need to compute")
                    return acc_df, state
            else:
                acc_df = df

            for window in self.windows:
                col = "ma{}".format(window)
                self.indicators.append(col)

                ma_df = acc_df["close"].rolling(window=window, min_periods=window).mean()
                acc_df[col] = ma_df

            acc_df["live"] = (acc_df["ma5"] > acc_df["ma10"]).apply(lambda x: live_or_dead(x))
            acc_df["distance"] = (acc_df["ma5"] - acc_df["ma10"]) / acc_df["close"]

            live = acc_df["live"]
            acc_df["count"] = live * (live.groupby((live != live.shift()).cumsum()).cumcount() + 1)

            acc_df["bulk"] = (live != live.shift()).cumsum()
            area_df = acc_df[["distance", "bulk"]]
            acc_df["area"] = area_df.groupby("bulk").cumsum()

            for vol_window in self.vol_windows:
                col = "vol_ma{}".format(vol_window)
                self.indicators.append(col)

                vol_ma_df = acc_df["turnover"].rolling(window=vol_window, min_periods=vol_window).mean()
                acc_df[col] = vol_ma_df

            acc_df = acc_df.set_index("timestamp", drop=False)
            return acc_df, state


TargetSelector
------------------------------
the class select targets according to Factor.

Trader
------------------------------
the backtest engine using TargetSelector, MLMachine or free style.

Tagger
------------------------------
classify TradableEntity by different dimensions, could be used as ml category feature.

MLMachine
------------------------------
the ml engine.