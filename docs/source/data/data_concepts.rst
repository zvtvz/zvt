=============
Data concepts
=============


.. _data.tradable_entity:

TradableEntity
------------------------------
:class:`~.zvt.contract.schema.TradableEntity` is anything could be traded, it could be :class:`~.zvt.domain.meta.stock_meta.Stock`,
:class:`~.zvt.domain.meta.etf_meta.Etf`, :class:`~.zvt.domain.meta.index_meta.Index`, future, cryptocurrency, or even a **sports match**.

Let's start with the real world tradable entities: China stock and USA stock ——— the world's most involved trading targets.

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

| what about other tradable entities?
| Show current registered tradable entity type and its schema:

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

The key is **entity_type** and the value is its :ref:`Schema<data.schema>`.

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
Just follow :ref:`Add tradable entity <extending_data.tradable_entity>`

.. _data.actor_entity:

ActorEntity
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

.. note::

    A good actor should know the good or bad actors in history, more importantly,
    the mind behind them.

.. _data.schema:

Schema
------------------------------
Data structure describing :class:`~.zvt.contract.schema.TradableEntity`, :class:`~.zvt.contract.schema.ActorEntity` or events happen on them.
Physically it's table with columns in sql database. One schema could have multiple storage
with different providers.

.. _data.schema_usage:

From specific to general, all zvt schema usage is in the same way.

* from zvt.domain import {Schema}
* {Schema}.record_data
* {Schema}.query_data

Explore :py:mod:`~.zvt.domain` for pre defined schemas. And check :ref:`record_data & query_data details <record_and_query>`

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

    {Schema}.get_storages()

e.g.

::

    >>> Stock1dHfqKdata.get_storages()
    [Engine(sqlite:////Users/foolcage/zvt-home/data/joinquant_stock_1d_hfq_kdata.db?check_same_thread=False),
     Engine(sqlite:////Users/foolcage/zvt-home/data/em_stock_1d_hfq_kdata.db?check_same_thread=False)]

IntervalLevel
------------------------------
:class:`~.zvt.contract.IntervalLevel` is repeated fixed time interval, e.g, 5m, 1d.
It's used in OHLC data for describing time window.

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

Kdata(Quote, OHLC)
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

.. note::

    In order to be compatible with historical data, the qfq is an exception, {adjust_type} is left empty

The pre defined kdata schema could be found in :py:mod:`~.zvt.domain.quotes`, it's separated by
entity_schema, level, and adjust type.

e.g. Stock1dHfqKdata means China Stock daily hfq quotes.

::

    >>> from zvt.domain import Stock1dHfqKdata
    >>> Stock1dHfqKdata.record_data(code='000338', provider='em')
    >>> df = Stock1dHfqKdata.query_data(code='000338', provider='em')
    >>> print(df)

                                  id        entity_id  timestamp provider    code  name level    open   close    high     low     volume      turnover  change_pct  turnover_rate
    0     stock_sz_000338_2007-04-30  stock_sz_000338 2007-04-30     None  000338  潍柴动力    1d   70.00   64.93   71.00   62.88   207375.0  1.365189e+09      2.1720         0.1182
    1     stock_sz_000338_2007-05-08  stock_sz_000338 2007-05-08     None  000338  潍柴动力    1d   66.60   64.00   68.00   62.88    86299.0  5.563198e+08     -0.0143         0.0492
    2     stock_sz_000338_2007-05-09  stock_sz_000338 2007-05-09     None  000338  潍柴动力    1d   63.32   62.00   63.88   59.60    93823.0  5.782065e+08     -0.0313         0.0535
    3     stock_sz_000338_2007-05-10  stock_sz_000338 2007-05-10     None  000338  潍柴动力    1d   61.50   62.49   64.48   61.01    47720.0  2.999226e+08      0.0079         0.0272
    4     stock_sz_000338_2007-05-11  stock_sz_000338 2007-05-11     None  000338  潍柴动力    1d   61.90   60.65   61.90   59.70    39273.0  2.373126e+08     -0.0294         0.0224
    ...                          ...              ...        ...      ...     ...   ...   ...     ...     ...     ...     ...        ...           ...         ...            ...
    3426  stock_sz_000338_2021-08-27  stock_sz_000338 2021-08-27     None  000338  潍柴动力    1d  331.97  345.95  345.95  329.82  1688497.0  3.370241e+09      0.0540         0.0398
    3427  stock_sz_000338_2021-08-30  stock_sz_000338 2021-08-30     None  000338  潍柴动力    1d  345.95  342.72  346.10  337.96  1187601.0  2.377957e+09     -0.0093         0.0280
    3428  stock_sz_000338_2021-08-31  stock_sz_000338 2021-08-31     None  000338  潍柴动力    1d  344.41  342.41  351.02  336.73  1143985.0  2.295195e+09     -0.0009         0.0270
    3429  stock_sz_000338_2021-09-01  stock_sz_000338 2021-09-01     None  000338  潍柴动力    1d  341.03  336.42  341.03  328.28  1218697.0  2.383841e+09     -0.0175         0.0287
    3430  stock_sz_000338_2021-09-02  stock_sz_000338 2021-09-02     None  000338  潍柴动力    1d  336.88  339.03  340.88  329.67  1023545.0  2.012006e+09      0.0078         0.0241

    [3431 rows x 15 columns]


e.g. Stock30mHfqKdata means China Stock 30 minutes hfq quotes.

::

    >>> from zvt.domain import Stock30mHfqKdata
    >>> Stock30mHfqKdata.record_data(code='000338', provider='em')
    >>> df = Stock30mHfqKdata.query_data(code='000338', provider='em')
    >>> print(df)

                                              id        entity_id           timestamp provider    code  name level    open   close    high     low    volume     turnover  change_pct  turnover_rate
    0    stock_sz_000338_2022-01-07T10:00:00.000  stock_sz_000338 2022-01-07 10:00:00       em  000338  潍柴动力   30m  312.23  313.77  317.30  310.70  288036.0  521397671.0      0.0049         0.0057
    1    stock_sz_000338_2022-01-07T10:30:00.000  stock_sz_000338 2022-01-07 10:30:00       em  000338  潍柴动力   30m  313.92  313.77  315.15  312.54  111887.0  201667653.0      0.0000         0.0022
    2    stock_sz_000338_2022-01-07T11:00:00.000  stock_sz_000338 2022-01-07 11:00:00       em  000338  潍柴动力   30m  313.77  314.07  314.69  313.00   80072.0  144303962.0      0.0010         0.0016
    3    stock_sz_000338_2022-01-07T11:30:00.000  stock_sz_000338 2022-01-07 11:30:00       em  000338  潍柴动力   30m  314.23  316.23  316.84  313.61  160797.0  291742498.0      0.0069         0.0032
    4    stock_sz_000338_2022-01-07T13:30:00.000  stock_sz_000338 2022-01-07 13:30:00       em  000338  潍柴动力   30m  316.23  314.07  316.99  314.07  115775.0  210236422.0     -0.0068         0.0023
    ..                                       ...              ...                 ...      ...     ...   ...   ...     ...     ...     ...     ...       ...          ...         ...            ...
    251  stock_sz_000338_2022-02-28T11:30:00.000  stock_sz_000338 2022-02-28 11:30:00       em  000338  潍柴动力   30m  268.15  268.30  268.61  267.99   34581.0   52053276.0      0.0006         0.0007
    252  stock_sz_000338_2022-02-28T13:30:00.000  stock_sz_000338 2022-02-28 13:30:00       em  000338  潍柴动力   30m  268.46  268.46  268.61  268.15   38019.0   57268380.0      0.0006         0.0008
    253  stock_sz_000338_2022-02-28T14:00:00.000  stock_sz_000338 2022-02-28 14:00:00       em  000338  潍柴动力   30m  268.46  269.22  269.53  268.30   41713.0   62994140.0      0.0028         0.0008
    254  stock_sz_000338_2022-02-28T14:30:00.000  stock_sz_000338 2022-02-28 14:30:00       em  000338  潍柴动力   30m  269.22  269.22  269.53  268.61   40815.0   61676966.0      0.0000         0.0008
    255  stock_sz_000338_2022-02-28T15:00:00.000  stock_sz_000338 2022-02-28 15:00:00       em  000338  潍柴动力   30m  269.07  269.84  269.84  268.76   60190.0   91032952.0      0.0023         0.0012

    [256 rows x 15 columns]

FinanceFactor
------------------------------
The usage is same as other entity events.

::

    >>> from zvt.domain import FinanceFactor
    >>> FinanceFactor.record_data(code='000338')
    >>> FinanceFactor.query_data(code='000338',columns=FinanceFactor.important_cols(),index='timestamp')

                basic_eps  total_op_income    net_profit  op_income_growth_yoy  net_profit_growth_yoy     roe    rota  gross_profit_margin  net_margin  timestamp
    timestamp
    2002-12-31        NaN     1.962000e+07  2.471000e+06                   NaN                    NaN     NaN     NaN               0.2068      0.1259 2002-12-31
    2003-12-31       1.27     3.574000e+09  2.739000e+08              181.2022               109.8778  0.7729  0.1783               0.2551      0.0766 2003-12-31
    2004-12-31       1.75     6.188000e+09  5.369000e+08                0.7313                 0.9598  0.3245  0.1474               0.2489      0.0868 2004-12-31
    2005-12-31       0.93     5.283000e+09  3.065000e+08               -0.1463                -0.4291  0.1327  0.0603               0.2252      0.0583 2005-12-31
    2006-03-31       0.33     1.859000e+09  1.079000e+08                   NaN                    NaN     NaN     NaN                  NaN      0.0598 2006-03-31
    ...               ...              ...           ...                   ...                    ...     ...     ...                  ...         ...        ...
    2020-08-28       0.59     9.449000e+10  4.680000e+09                0.0400                -0.1148  0.0983  0.0229               0.1958      0.0603 2020-08-28
    2020-10-31       0.90     1.474000e+11  7.106000e+09                0.1632                 0.0067  0.1502  0.0347               0.1949      0.0590 2020-10-31
    2021-03-31       1.16     1.975000e+11  9.207000e+09                0.1327                 0.0112  0.1919  0.0444               0.1931      0.0571 2021-03-31
    2021-04-30       0.42     6.547000e+10  3.344000e+09                0.6788                 0.6197  0.0622  0.0158               0.1916      0.0667 2021-04-30
    2021-08-31       0.80     1.264000e+11  6.432000e+09                0.3375                 0.3742  0.1125  0.0287               0.1884      0.0653 2021-08-31

    [66 rows x 10 columns]

Three financial tables

::

    >>> BalanceSheet.record_data(code='000338')
    >>> IncomeStatement.record_data(code='000338')
    >>> CashFlowStatement.record_data(code='000338')

.. note::
    Just remember, all :ref:`schema usage <data.schema_usage>` is in the same way.
