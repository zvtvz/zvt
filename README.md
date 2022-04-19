[![github](https://img.shields.io/github/stars/zvtvz/zvt.svg)](https://github.com/zvtvz/zvt)
[![image](https://img.shields.io/pypi/v/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/pyversions/zvt.svg)](https://pypi.org/project/zvt/)
[![build](https://github.com/zvtvz/zvt/actions/workflows/build.yaml/badge.svg)](https://github.com/zvtvz/zvt/actions/workflows/build.yml)
[![package](https://github.com/zvtvz/zvt/actions/workflows/package.yaml/badge.svg)](https://github.com/zvtvz/zvt/actions/workflows/package.yaml)
[![Documentation Status](https://readthedocs.org/projects/zvt/badge/?version=latest)](https://zvt.readthedocs.io/en/latest/?badge=latest)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
[![Downloads](https://pepy.tech/badge/zvt/month)](https://pepy.tech/project/zvt)


**Read this in other languages: [中文](README-cn.md).**  

**Read the docs:[https://zvt.readthedocs.io/en/latest/](https://zvt.readthedocs.io/en/latest/)**

### Install
```
python3 -m pip install -U zvt
```

### Main ui

After the installation is complete, enter zvt on the command line
```shell
zvt
```
open [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

> The example shown here relies on data, factor, trader, please read [docs](https://zvt.readthedocs.io/en/latest/)

<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/zvt-factor.png'/></p>
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/zvt-trader.png'/></p>

> The core concept of the system is visual, and the name of the interface corresponds to it one-to-one, so it is also uniform and extensible.

> You can write and run the strategy in your favorite ide, and then view its related targets, factor, signal and performance on the UI.

### Behold, the power of zvt:
```
>>> from zvt.domain import Stock, Stock1dHfqKdata
>>> from zvt.ml import MaStockMLMachine
>>> Stock.record_data(provider="em")
>>> entity_ids = ["stock_sz_000001", "stock_sz_000338", "stock_sh_601318"]
>>> Stock1dHfqKdata.record_data(provider="em", entity_ids=entity_ids, sleeping_time=1)
>>> machine = MaStockMLMachine(entity_ids=["stock_sz_000001"], data_provider="em")
>>> machine.train()
>>> machine.predict()
>>> machine.draw_result(entity_id="stock_sz_000001")
```
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/pred_close.png'/></p>

> The few lines of code above has done: data capture, persistence, incremental update, machine learning, prediction, and display results.
> Once you are familiar with the core concepts of the system, you can apply it to any target in the market.

### Data

#### China stock
```
>>> from zvt.domain import *
>>> Stock.record_data(provider="em")
>>> df = Stock.query_data(provider="em", index='code')
>>> print(df)

                     id        entity_id  timestamp entity_type exchange    code   name  list_date end_date
code
000001  stock_sz_000001  stock_sz_000001 1991-04-03       stock       sz  000001   平安银行 1991-04-03     None
000002  stock_sz_000002  stock_sz_000002 1991-01-29       stock       sz  000002  万  科Ａ 1991-01-29     None
000004  stock_sz_000004  stock_sz_000004 1990-12-01       stock       sz  000004   国华网安 1990-12-01     None
000005  stock_sz_000005  stock_sz_000005 1990-12-10       stock       sz  000005   世纪星源 1990-12-10     None
000006  stock_sz_000006  stock_sz_000006 1992-04-27       stock       sz  000006   深振业Ａ 1992-04-27     None
...                 ...              ...        ...         ...      ...     ...    ...        ...      ...
605507  stock_sh_605507  stock_sh_605507 2021-08-02       stock       sh  605507   国邦医药 2021-08-02     None
605577  stock_sh_605577  stock_sh_605577 2021-08-24       stock       sh  605577   龙版传媒 2021-08-24     None
605580  stock_sh_605580  stock_sh_605580 2021-08-19       stock       sh  605580   恒盛能源 2021-08-19     None
605588  stock_sh_605588  stock_sh_605588 2021-08-12       stock       sh  605588   冠石科技 2021-08-12     None
605589  stock_sh_605589  stock_sh_605589 2021-08-10       stock       sh  605589   圣泉集团 2021-08-10     None

[4136 rows x 9 columns]
```

#### USA stock
```
>>> Stockus.record_data()
>>> df = Stockus.query_data(index='code')
>>> print(df)

                       id            entity_id timestamp entity_type exchange  code                         name list_date end_date
code
A          stockus_nyse_A       stockus_nyse_A       NaT     stockus     nyse     A                          安捷伦      None     None
AA        stockus_nyse_AA      stockus_nyse_AA       NaT     stockus     nyse    AA                         美国铝业      None     None
AAC      stockus_nyse_AAC     stockus_nyse_AAC       NaT     stockus     nyse   AAC      Ares Acquisition Corp-A      None     None
AACG  stockus_nasdaq_AACG  stockus_nasdaq_AACG       NaT     stockus   nasdaq  AACG    ATA Creativity Global ADR      None     None
AACG    stockus_nyse_AACG    stockus_nyse_AACG       NaT     stockus     nyse  AACG    ATA Creativity Global ADR      None     None
...                   ...                  ...       ...         ...      ...   ...                          ...       ...      ...
ZWRK  stockus_nasdaq_ZWRK  stockus_nasdaq_ZWRK       NaT     stockus   nasdaq  ZWRK    Z-Work Acquisition Corp-A      None     None
ZY      stockus_nasdaq_ZY    stockus_nasdaq_ZY       NaT     stockus   nasdaq    ZY                 Zymergen Inc      None     None
ZYME    stockus_nyse_ZYME    stockus_nyse_ZYME       NaT     stockus     nyse  ZYME                Zymeworks Inc      None     None
ZYNE  stockus_nasdaq_ZYNE  stockus_nasdaq_ZYNE       NaT     stockus   nasdaq  ZYNE  Zynerba Pharmaceuticals Inc      None     None
ZYXI  stockus_nasdaq_ZYXI  stockus_nasdaq_ZYXI       NaT     stockus   nasdaq  ZYXI                    Zynex Inc      None     None

[5826 rows x 9 columns]

>>> Stockus.query_data(code='AAPL')
                    id            entity_id timestamp entity_type exchange  code name list_date end_date
0  stockus_nasdaq_AAPL  stockus_nasdaq_AAPL      None     stockus   nasdaq  AAPL   苹果      None     None
```

#### Hong Kong stock
```
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

```

#### And more
```
>>> from zvt.contract import *
>>> zvt_context.tradable_schema_map

{'stockus': zvt.domain.meta.stockus_meta.Stockus,
 'stockhk': zvt.domain.meta.stockhk_meta.Stockhk,
 'index': zvt.domain.meta.index_meta.Index,
 'etf': zvt.domain.meta.etf_meta.Etf,
 'stock': zvt.domain.meta.stock_meta.Stock,
 'block': zvt.domain.meta.block_meta.Block,
 'fund': zvt.domain.meta.fund_meta.Fund}
```

The key is tradable entity type, and the value is the schema. The system provides unified **record (record_data)** and **query (query_data)** methods for the schema.

```
>>> Index.record_data()
>>> df=Index.query_data(filters=[Index.category=='scope',Index.exchange='sh'])
>>> print(df)
                 id        entity_id  timestamp entity_type exchange    code    name  list_date end_date publisher category  base_point
0   index_sh_000001  index_sh_000001 1990-12-19       index       sh  000001    上证指数 1991-07-15     None   csindex    scope      100.00
1   index_sh_000002  index_sh_000002 1990-12-19       index       sh  000002    Ａ股指数 1992-02-21     None   csindex    scope      100.00
2   index_sh_000003  index_sh_000003 1992-02-21       index       sh  000003    B股指数 1992-08-17     None   csindex    scope      100.00
3   index_sh_000010  index_sh_000010 2002-06-28       index       sh  000010   上证180 2002-07-01     None   csindex    scope     3299.06
4   index_sh_000016  index_sh_000016 2003-12-31       index       sh  000016    上证50 2004-01-02     None   csindex    scope     1000.00
..              ...              ...        ...         ...      ...     ...     ...        ...      ...       ...      ...         ...
25  index_sh_000020  index_sh_000020 2007-12-28       index       sh  000020    中型综指 2008-05-12     None   csindex    scope     1000.00
26  index_sh_000090  index_sh_000090 2009-12-31       index       sh  000090    上证流通 2010-12-02     None   csindex    scope     1000.00
27  index_sh_930903  index_sh_930903 2012-12-31       index       sh  930903    中证Ａ股 2016-10-18     None   csindex    scope     1000.00
28  index_sh_000688  index_sh_000688 2019-12-31       index       sh  000688    科创50 2020-07-23     None   csindex    scope     1000.00
29  index_sh_931643  index_sh_931643 2019-12-31       index       sh  931643  科创创业50 2021-06-01     None   csindex    scope     1000.00

[30 rows x 12 columns]

```

### EntityEvent
We have tradable entity and then events about them.

#### Market quotes
the TradableEntity quote schema follows the following rules:
```
{entity_shema}{level}{adjust_type}Kdata
```
* entity_schema

TradableEntity class，e.g., Stock,Stockus.

* level
```
>>> for level in IntervalLevel:
        print(level.value)
```

* adjust type
```
>>> for adjust_type in AdjustType:
        print(adjust_type.value)
```

> Note: In order to be compatible with historical data, the pre-reset is an exception, {adjust_type} is left empty

qfq
```
>>> Stock1dKdata.record_data(code='000338', provider='em')
>>> df = Stock1dKdata.query_data(code='000338', provider='em')
>>> print(df)

                              id        entity_id  timestamp provider    code  name level   open  close   high    low     volume      turnover  change_pct  turnover_rate
0     stock_sz_000338_2007-04-30  stock_sz_000338 2007-04-30     None  000338  潍柴动力    1d   2.33   2.00   2.40   1.87   207375.0  1.365189e+09      3.2472         0.1182
1     stock_sz_000338_2007-05-08  stock_sz_000338 2007-05-08     None  000338  潍柴动力    1d   2.11   1.94   2.20   1.87    86299.0  5.563198e+08     -0.0300         0.0492
2     stock_sz_000338_2007-05-09  stock_sz_000338 2007-05-09     None  000338  潍柴动力    1d   1.90   1.81   1.94   1.66    93823.0  5.782065e+08     -0.0670         0.0535
3     stock_sz_000338_2007-05-10  stock_sz_000338 2007-05-10     None  000338  潍柴动力    1d   1.78   1.85   1.98   1.75    47720.0  2.999226e+08      0.0221         0.0272
4     stock_sz_000338_2007-05-11  stock_sz_000338 2007-05-11     None  000338  潍柴动力    1d   1.81   1.73   1.81   1.66    39273.0  2.373126e+08     -0.0649         0.0224
...                          ...              ...        ...      ...     ...   ...   ...    ...    ...    ...    ...        ...           ...         ...            ...
3426  stock_sz_000338_2021-08-27  stock_sz_000338 2021-08-27     None  000338  潍柴动力    1d  19.39  20.30  20.30  19.25  1688497.0  3.370241e+09      0.0601         0.0398
3427  stock_sz_000338_2021-08-30  stock_sz_000338 2021-08-30     None  000338  潍柴动力    1d  20.30  20.09  20.31  19.78  1187601.0  2.377957e+09     -0.0103         0.0280
3428  stock_sz_000338_2021-08-31  stock_sz_000338 2021-08-31     None  000338  潍柴动力    1d  20.20  20.07  20.63  19.70  1143985.0  2.295195e+09     -0.0010         0.0270
3429  stock_sz_000338_2021-09-01  stock_sz_000338 2021-09-01     None  000338  潍柴动力    1d  19.98  19.68  19.98  19.15  1218697.0  2.383841e+09     -0.0194         0.0287
3430  stock_sz_000338_2021-09-02  stock_sz_000338 2021-09-02     None  000338  潍柴动力    1d  19.71  19.85  19.97  19.24  1023545.0  2.012006e+09      0.0086         0.0241

[3431 rows x 15 columns]

>>> Stockus1dKdata.record_data(code='AAPL', provider='em')
>>> df = Stockus1dKdata.query_data(code='AAPL', provider='em')
>>> print(df)

                                  id            entity_id  timestamp provider  code name level    open   close    high     low      volume      turnover  change_pct  turnover_rate
0     stockus_nasdaq_AAPL_1984-09-07  stockus_nasdaq_AAPL 1984-09-07     None  AAPL   苹果    1d   -5.59   -5.59   -5.58   -5.59   2981600.0  0.000000e+00      0.0000         0.0002
1     stockus_nasdaq_AAPL_1984-09-10  stockus_nasdaq_AAPL 1984-09-10     None  AAPL   苹果    1d   -5.59   -5.59   -5.58   -5.59   2346400.0  0.000000e+00      0.0000         0.0001
2     stockus_nasdaq_AAPL_1984-09-11  stockus_nasdaq_AAPL 1984-09-11     None  AAPL   苹果    1d   -5.58   -5.58   -5.58   -5.58   5444000.0  0.000000e+00      0.0018         0.0003
3     stockus_nasdaq_AAPL_1984-09-12  stockus_nasdaq_AAPL 1984-09-12     None  AAPL   苹果    1d   -5.58   -5.59   -5.58   -5.59   4773600.0  0.000000e+00     -0.0018         0.0003
4     stockus_nasdaq_AAPL_1984-09-13  stockus_nasdaq_AAPL 1984-09-13     None  AAPL   苹果    1d   -5.58   -5.58   -5.58   -5.58   7429600.0  0.000000e+00      0.0018         0.0004
...                              ...                  ...        ...      ...   ...  ...   ...     ...     ...     ...     ...         ...           ...         ...            ...
8765  stockus_nasdaq_AAPL_2021-08-27  stockus_nasdaq_AAPL 2021-08-27     None  AAPL   苹果    1d  147.48  148.60  148.75  146.83  55802388.0  8.265452e+09      0.0072         0.0034
8766  stockus_nasdaq_AAPL_2021-08-30  stockus_nasdaq_AAPL 2021-08-30     None  AAPL   苹果    1d  149.00  153.12  153.49  148.61  90956723.0  1.383762e+10      0.0304         0.0055
8767  stockus_nasdaq_AAPL_2021-08-31  stockus_nasdaq_AAPL 2021-08-31     None  AAPL   苹果    1d  152.66  151.83  152.80  151.29  86453117.0  1.314255e+10     -0.0084         0.0052
8768  stockus_nasdaq_AAPL_2021-09-01  stockus_nasdaq_AAPL 2021-09-01     None  AAPL   苹果    1d  152.83  152.51  154.98  152.34  80313711.0  1.235321e+10      0.0045         0.0049
8769  stockus_nasdaq_AAPL_2021-09-02  stockus_nasdaq_AAPL 2021-09-02     None  AAPL   苹果    1d  153.87  153.65  154.72  152.40  71171317.0  1.093251e+10      0.0075         0.0043

[8770 rows x 15 columns]
```

hfq
```
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
```

#### Finance factor
```
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
```

#### Three financial tables
```
>>> BalanceSheet.record_data(code='000338')
>>> IncomeStatement.record_data(code='000338')
>>> CashFlowStatement.record_data(code='000338')
```

#### And more
```
>>> zvt_context.schemas
[zvt.domain.dividend_financing.DividendFinancing,
 zvt.domain.dividend_financing.DividendDetail,
 zvt.domain.dividend_financing.SpoDetail...]
```

All schemas is registered in zvt_context.schemas, **schema** is table, data structure.
The fields and meaning could be checked in following ways:

* help

type the schema. and press tab to show its fields or .help()
```
>>> FinanceFactor.help()
```

* source code

Schemas defined in [domain](https://github.com/zvtvz/zvt/tree/master/zvt/domain)

From above examples, you should know the unified way of recording data:

> Schema.record_data(provider='your provider',codes='the codes')

Note the optional parameter provider, which represents the data provider. 
A schema can have multiple providers, which is the cornerstone of system stability.

Check the provider has been implemented:
```
>>> Stock.provider_map_recorder
{'joinquant': zvt.recorders.joinquant.meta.jq_stock_meta_recorder.JqChinaStockRecorder,
 'exchange': zvt.recorders.exchange.exchange_stock_meta_recorder.ExchangeStockMetaRecorder,
 'em': zvt.recorders.em.meta.em_stock_meta_recorder.EMStockRecorder,
 'eastmoney': zvt.recorders.eastmoney.meta.eastmoney_stock_meta_recorder.EastmoneyChinaStockListRecorder}

```
You can use any provider to get the data, the first one is used by default.

One more example, the stock sector data recording:
```
>>> Block.provider_map_recorder
{'eastmoney': zvt.recorders.eastmoney.meta.eastmoney_block_meta_recorder.EastmoneyChinaBlockRecorder,
 'sina': zvt.recorders.sina.meta.sina_block_recorder.SinaBlockRecorder}

>>> Block.record_data(provider='sina')
Block registered recorders:{'eastmoney': <class 'zvt.recorders.eastmoney.meta.china_stock_category_recorder.EastmoneyChinaBlockRecorder'>, 'sina': <class 'zvt.recorders.sina.meta.sina_china_stock_category_recorder.SinaChinaBlockRecorder'>}
2020-03-04 23:56:48,931  INFO  MainThread  finish record sina blocks:industry
2020-03-04 23:56:49,450  INFO  MainThread  finish record sina blocks:concept
```

Learn more about record_data

* The parameter code[single], codes[multiple] represent the stock codes to be recorded
* Recording the whole market if not set code, codes
* This method will store the data locally and only do incremental updates

Refer to the scheduling recoding way[data runner](https://github.com/zvtvz/zvt/blob/master/examples/data_runner)

#### Market-wide stock selection

After recording the data of the whole market, you can quickly query the required data locally.

An example: the top 20 stocks with roe>8% and revenue growth>8% in the 2018 annual report
```
>>> df=FinanceFactor.query_data(filters=[FinanceFactor.roe>0.08,FinanceFactor.report_period=='year',FinanceFactor.op_income_growth_yoy>0.08],start_timestamp='2019-01-01',order=FinanceFactor.roe.desc(),limit=20,columns=["code"]+FinanceFactor.important_cols(),index='code')

          code  basic_eps  total_op_income    net_profit  op_income_growth_yoy  net_profit_growth_yoy     roe    rota  gross_profit_margin  net_margin  timestamp
code
000048  000048     2.7350     4.919000e+09  1.101000e+09                0.4311                 1.5168  0.7035  0.1988               0.5243      0.2355 2020-04-30
000912  000912     0.3500     4.405000e+09  3.516000e+08                0.1796                 1.2363  4.7847  0.0539               0.2175      0.0795 2019-03-20
002207  002207     0.2200     3.021000e+08  5.189000e+07                0.1600                 1.1526  1.1175  0.1182               0.1565      0.1718 2020-04-27
002234  002234     5.3300     3.276000e+09  1.610000e+09                0.8023                 3.2295  0.8361  0.5469               0.5968      0.4913 2020-04-21
002458  002458     3.7900     3.584000e+09  2.176000e+09                1.4326                 4.9973  0.8318  0.6754               0.6537      0.6080 2020-02-20
...        ...        ...              ...           ...                   ...                    ...     ...     ...                  ...         ...        ...
600701  600701    -3.6858     7.830000e+08 -3.814000e+09                1.3579                -0.0325  1.9498 -0.7012               0.4173     -4.9293 2020-04-29
600747  600747    -1.5600     3.467000e+08 -2.290000e+09                2.1489                -0.4633  3.1922 -1.5886               0.0378     -6.6093 2020-06-30
600793  600793     1.6568     1.293000e+09  1.745000e+08                0.1164                 0.8868  0.7490  0.0486               0.1622      0.1350 2019-04-30
600870  600870     0.0087     3.096000e+07  4.554000e+06                0.7773                 1.3702  0.7458  0.0724               0.2688      0.1675 2019-03-30
688169  688169    15.6600     4.205000e+09  7.829000e+08                0.3781                 1.5452  0.7172  0.4832               0.3612      0.1862 2020-04-28

[20 rows x 11 columns]
```

So, you should be able to answer the following three questions now:
* What data is there?
* How to record data?
* How to query data?

For more advanced usage and extended data, please refer to the data section in the detailed document.

### Write strategy
Now we could write strategy basing on TradableEntity and EntityEvent.
The so-called strategy backtesting is nothing but repeating the following process：

#### At a certain time, find the targets which matching conditions, buy and sell them, and see the performance.

Two modes to write strategy:
* solo (free style)

At a certain time, calculate conditions according to the events, buy and sell

* formal (正式的)

The calculation model of the two-dimensional index and multi-entity

#### a too simple,sometimes naive person (solo)
Well, this strategy is really too simple,sometimes naive, as we do most of the time.
> When the report comes out, I look at the report. 
> If the institution increases its position by more than 5%, I will buy it, and if the institution reduces its position by more than 50%, I will sell it.

Show you the code:
```
# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api import get_recent_report_date
from zvt.contract import ActorType, AdjustType
from zvt.domain import StockActorSummary, Stock1dKdata
from zvt.trader import StockTrader
from zvt.utils import pd_is_not_null, is_same_date, to_pd_timestamp


class FollowIITrader(StockTrader):
    finish_date = None

    def on_time(self, timestamp: pd.Timestamp):
        recent_report_date = to_pd_timestamp(get_recent_report_date(timestamp))
        if self.finish_date and is_same_date(recent_report_date, self.finish_date):
            return
        filters = [StockActorSummary.actor_type == ActorType.raised_fund.value,
                   StockActorSummary.report_date == recent_report_date]

        if self.entity_ids:
            filters = filters + [StockActorSummary.entity_id.in_(self.entity_ids)]

        df = StockActorSummary.query_data(filters=filters)

        if pd_is_not_null(df):
            self.logger.info(f'{df}')
            self.finish_date = recent_report_date

        long_df = df[df['change_ratio'] > 0.05]
        short_df = df[df['change_ratio'] < -0.5]
        try:
            self.trade_the_targets(due_timestamp=timestamp, happen_timestamp=timestamp,
                                   long_selected=set(long_df['entity_id'].to_list()),
                                   short_selected=set(short_df['entity_id'].to_list()))
        except Exception as e:
            self.logger.error(e)


if __name__ == '__main__':
    entity_id = 'stock_sh_600519'
    Stock1dKdata.record_data(entity_id=entity_id, provider='em')
    StockActorSummary.record_data(entity_id=entity_id, provider='em')
    FollowIITrader(start_timestamp='2002-01-01', end_timestamp='2021-01-01', entity_ids=[entity_id],
                   provider='em', adjust_type=AdjustType.qfq, profit_threshold=None).run()
```

So, writing a strategy is not that complicated.
Just use your imagination, find the relation of the price and the events.

Then refresh [http://127.0.0.1:8050/](http://127.0.0.1:8050/)，check the performance of your strategy.

More examples is in [Strategy example](https://github.com/zvtvz/zvt/tree/master/examples/trader)

#### Be serious (formal)
Simple calculation can be done through query_data.
Now it's time to introduce the two-dimensional index multi-entity calculation model.

Takes technical factors as an example to illustrate the **calculation process**:
```
In [7]: from zvt.factors.technical_factor import *
In [8]: factor = BullFactor(codes=['000338','601318'],start_timestamp='2019-01-01',end_timestamp='2019-06-10', transformer=MacdTransformer())
```
### data_df

**two-dimensional index** DataFrame read from the schema by query_data.
```
In [11]: factor.data_df
Out[11]:
                           level   high                          id        entity_id   open    low  timestamp  close
entity_id       timestamp
stock_sh_601318 2019-01-02    1d  54.91  stock_sh_601318_2019-01-02  stock_sh_601318  54.78  53.70 2019-01-02  53.94
                2019-01-03    1d  55.06  stock_sh_601318_2019-01-03  stock_sh_601318  53.91  53.82 2019-01-03  54.42
                2019-01-04    1d  55.71  stock_sh_601318_2019-01-04  stock_sh_601318  54.03  53.98 2019-01-04  55.31
                2019-01-07    1d  55.88  stock_sh_601318_2019-01-07  stock_sh_601318  55.80  54.64 2019-01-07  55.03
                2019-01-08    1d  54.83  stock_sh_601318_2019-01-08  stock_sh_601318  54.79  53.96 2019-01-08  54.54
...                          ...    ...                         ...              ...    ...    ...        ...    ...
stock_sz_000338 2019-06-03    1d  11.04  stock_sz_000338_2019-06-03  stock_sz_000338  10.93  10.74 2019-06-03  10.81
                2019-06-04    1d  10.85  stock_sz_000338_2019-06-04  stock_sz_000338  10.84  10.57 2019-06-04  10.73
                2019-06-05    1d  10.92  stock_sz_000338_2019-06-05  stock_sz_000338  10.87  10.59 2019-06-05  10.59
                2019-06-06    1d  10.71  stock_sz_000338_2019-06-06  stock_sz_000338  10.59  10.49 2019-06-06  10.65
                2019-06-10    1d  11.05  stock_sz_000338_2019-06-10  stock_sz_000338  10.73  10.71 2019-06-10  11.02

[208 rows x 8 columns]
```

### factor_df
**two-dimensional index** DataFrame which calculating using data_df by [transformer](https://github.com/zvtvz/zvt/blob/master/zvt/factors/factor.py#L18)
e.g., MacdTransformer.
```
In [12]: factor.factor_df
Out[12]:
                           level   high                          id        entity_id   open    low  timestamp  close      diff       dea      macd
entity_id       timestamp
stock_sh_601318 2019-01-02    1d  54.91  stock_sh_601318_2019-01-02  stock_sh_601318  54.78  53.70 2019-01-02  53.94       NaN       NaN       NaN
                2019-01-03    1d  55.06  stock_sh_601318_2019-01-03  stock_sh_601318  53.91  53.82 2019-01-03  54.42       NaN       NaN       NaN
                2019-01-04    1d  55.71  stock_sh_601318_2019-01-04  stock_sh_601318  54.03  53.98 2019-01-04  55.31       NaN       NaN       NaN
                2019-01-07    1d  55.88  stock_sh_601318_2019-01-07  stock_sh_601318  55.80  54.64 2019-01-07  55.03       NaN       NaN       NaN
                2019-01-08    1d  54.83  stock_sh_601318_2019-01-08  stock_sh_601318  54.79  53.96 2019-01-08  54.54       NaN       NaN       NaN
...                          ...    ...                         ...              ...    ...    ...        ...    ...       ...       ...       ...
stock_sz_000338 2019-06-03    1d  11.04  stock_sz_000338_2019-06-03  stock_sz_000338  10.93  10.74 2019-06-03  10.81 -0.121336 -0.145444  0.048215
                2019-06-04    1d  10.85  stock_sz_000338_2019-06-04  stock_sz_000338  10.84  10.57 2019-06-04  10.73 -0.133829 -0.143121  0.018583
                2019-06-05    1d  10.92  stock_sz_000338_2019-06-05  stock_sz_000338  10.87  10.59 2019-06-05  10.59 -0.153260 -0.145149 -0.016223
                2019-06-06    1d  10.71  stock_sz_000338_2019-06-06  stock_sz_000338  10.59  10.49 2019-06-06  10.65 -0.161951 -0.148509 -0.026884
                2019-06-10    1d  11.05  stock_sz_000338_2019-06-10  stock_sz_000338  10.73  10.71 2019-06-10  11.02 -0.137399 -0.146287  0.017776

[208 rows x 11 columns]
```

### result_df
**two-dimensional index** DataFrame which calculating using factor_df or(and) data_df.
It's used by TargetSelector.

e.g.,[macd](https://github.com/zvtvz/zvt/blob/master/zvt/factors/technical_factor.py#L56)

```
In [14]: factor.result_df
Out[14]:
                            filter_result
entity_id       timestamp
stock_sh_601318 2019-01-02  False
                2019-01-03  False
                2019-01-04  False
                2019-01-07  False
                2019-01-08  False
...                           ...
stock_sz_000338 2019-06-03  False
                2019-06-04  False
                2019-06-05  False
                2019-06-06  False
                2019-06-10  False

[208 rows x 1 columns]
```

The  format of result_df is as follows:

<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/result_df.png'/></p>

filter_result is True or False, score_result is from 0 to 1

Combining the stock picker and backtesting, the whole process is as follows:
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/flow.png'/></p>

## Env settings（optional）
```
>>> from zvt import *
>>> zvt_env
{'zvt_home': '/Users/foolcage/zvt-home',
 'data_path': '/Users/foolcage/zvt-home/data',
 'tmp_path': '/Users/foolcage/zvt-home/tmp',
 'ui_path': '/Users/foolcage/zvt-home/ui',
 'log_path': '/Users/foolcage/zvt-home/logs'}

>>> zvt_config 
```

* jq_username 聚宽数据用户名
* jq_password 聚宽数据密码
* smtp_host 邮件服务器host
* smtp_port 邮件服务器端口
* email_username smtp邮箱账户
* email_password smtp邮箱密码
* wechat_app_id
* wechat_app_secrect

```
>>> init_config(current_config=zvt_config, jq_username='xxx', jq_password='yyy')
```
>  config others this way: init_config(current_config=zvt_config, **kv)

### History data（optional）
baidu: https://pan.baidu.com/s/1kHAxGSxx8r5IBHe5I7MAmQ code: yb6c

google drive: https://drive.google.com/drive/folders/17Bxijq-PHJYrLDpyvFAm5P6QyhKL-ahn?usp=sharing

It contains daily/weekly post-restoration data, stock valuations, fund and its holdings data, financial data and other data.

Unzip the downloaded data to the data_path of the your environment (all db files are placed in this directory, there is no hierarchical structure)

The data could be updated incrementally. Downloading historical data is just to save time. It is also possible to update all by yourself.

#### Joinquant(optional)
the data could be updated from different provider, this make the system stable.

https://www.joinquant.com/default/index/sdk?channelId=953cbf5d1b8683f81f0c40c9d4265c0d

> add other providers， [Data extension tutorial](https://zvtvz.github.io/zvt/#/data_extending)

## Development

### Clone

```
git clone https://github.com/zvtvz/zvt.git
```

set up virtual env(python>=3.6),install requirements
```
pip3 install -r requirements.txt
pip3 install pytest
```

### Tests
```shell
pytest ./tests
```

<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/pytest.jpg'/></p>

Most of the features can be referenced from the tests

## Contribution

[code of conduct](https://github.com/zvtvz/zvt/blob/master/code_of_conduct.md)

1. Pass all unit tests, if it is a new feature, please add a new unit test for it
2. Compliance with development specifications
3. If necessary, please update the corresponding document

Developers are also very welcome to provide more examples for zvt, and work together to improve the documentation.

## Buy me a coffee

<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/alipay-cn.png" width="25%" alt="Alipay">　　　　　
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/wechat-cn.png" width="25%" alt="Wechat">

## Contact

wechat:foolcage  
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/wechat.jpeg" width="25%" alt="Wechat">

------
wechat subscription:  
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/gongzhonghao.jpg" width="25%" alt="Wechat">

zhihu:  
https://zhuanlan.zhihu.com/automoney

## Thanks
<p><a href=https://www.jetbrains.com/?from=zvt><img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/jetbrains.png" width="25%" alt="jetbrains"></a></p>
