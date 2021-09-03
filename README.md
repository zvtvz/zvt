[![github](https://img.shields.io/github/stars/zvtvz/zvt.svg)](https://github.com/zvtvz/zvt)
[![image](https://img.shields.io/pypi/v/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/pyversions/zvt.svg)](https://pypi.org/project/zvt/)
[![build](https://github.com/zvtvz/zvt/actions/workflows/build.yaml/badge.svg)](https://github.com/zvtvz/zvt/actions/workflows/build.yml)
[![package](https://github.com/zvtvz/zvt/actions/workflows/package.yaml/badge.svg)](https://github.com/zvtvz/zvt/actions/workflows/package.yaml)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
[![Downloads](https://pepy.tech/badge/zvt/month)](https://pepy.tech/project/zvt)

**Read this in other languages: [English](README-en.md).**  

## 开始之前

zvt将市场抽象为如下的模型:

<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/view.png'/></p>

* TradableEntity (交易标的)
* ActorEntity (市场参与者)
* EntityEvent (交易标的 和 市场参与者 发生的事件)

基于一些 **简单自然** 的规则，你可以方便的组合，设计，创造自己的世界。比如：
* 数据是可以 **记录** 和 **查询** 的
* 数据是可以有多个 **提供商** 的
* 数据是可以 **增量更新** 的
* 数据的 **分类** 是明确的
* **策略** 是容易组合验证的
* 不同 **空间** 的 **样本** 是容易生成的

## 快速开始

### 安装
```
python3 -m pip install -U zvt
```

### 数据

```
>>> from zvt.domain import *
```
#### A股交易标的
```
>>> Stock.record_data()
>>> df = Stock.query_data(index='code')
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

#### 美股交易标的
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

#### 港股交易标的
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


#### 行情数据
前复权
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
后复权
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

#### 财务数据
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

### 跑个策略
```
>>> from zvt.samples import *
>>> t = MyMaTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01', end_timestamp='2021-06-30', trader_name='000338_ma_trader',provider='em')
>>> t.run()
```

## 2. 📝环境设置
项目支持多环境切换,默认情况下，不设置环境变量TESTING_ZVT即为正式环境
 ```
In [1]: from zvt import *
{'data_path': '/Users/xuanqi/zvt-home/data',
 'domain_module': 'zvt.domain',
 'email_password': '',
 'email_username': '',
 'http_proxy': '127.0.0.1:1087',
 'https_proxy': '127.0.0.1:1087',
 'jq_password': '',
 'jq_username': '',
 'log_path': '/Users/xuanqi/zvt-home/logs',
 'smtp_host': 'smtpdm.aliyun.com',
 'smtp_port': '80',
 'ui_path': '/Users/xuanqi/zvt-home/ui',
 'wechat_app_id': '',
 'wechat_app_secrect': '',
 'zvt_home': '/Users/xuanqi/zvt-home'}
 ```

>如果你不想使用使用默认的zvt_home目录,请设置环境变量ZVT_HOME再运行。

所有操作跟测试环境是一致的，只是操作的目录不同。

### 2.1 配置（可选）
在zvt_home目录中找到config.json进行配置：

#### 使用聚宽数据需要设置：
* jq_username 聚宽数据用户名
* jq_password 聚宽数据密码

#### 使用邮箱推送需要设置：
* smtp_host 邮件服务器host
* smtp_port 邮件服务器端口
* email_username smtp邮箱账户
* email_password smtp邮箱密码

#### 使用微信公众号推送需要设置：
* wechat_app_id
* wechat_app_secrect

### 2.2 下载历史数据（可选）
百度网盘: https://pan.baidu.com/s/1kHAxGSxx8r5IBHe5I7MAmQ 提取码: yb6c

google drive: https://drive.google.com/drive/folders/17Bxijq-PHJYrLDpyvFAm5P6QyhKL-ahn?usp=sharing

里面包含joinquant的日/周线后复权数据，个股估值，基金及其持仓数据，eastmoney的财务等数据。

把下载的数据解压到正式环境的data_path（所有db文件放到该目录下，没有层级结构）

数据的更新是增量的，下载历史数据只是为了节省时间，全部自己更新也是可以的。

### 2.3 注册聚宽(可选)
项目数据支持多provider，在数据schema一致性的基础上，可根据需要进行选择和扩展，目前支持新浪，东财，交易所等免费数据。

#### 数据的设计上是让provider来适配schema,而不是反过来，这样即使某provider不可用了，换一个即可，不会影响整个系统的使用。

但免费数据的缺点是显而易见的:不稳定，爬取清洗数据耗时耗力，维护代价巨大，且随时可能不可用。  
个人建议：如果只是学习研究，可以使用免费数据；如果是真正有意投身量化，还是选一家可靠的数据提供商。

项目支持聚宽的数据，可戳以下链接申请使用（目前可免费使用一年）  
https://www.joinquant.com/default/index/sdk?channelId=953cbf5d1b8683f81f0c40c9d4265c0d

> 项目中大部分的免费数据目前都是比较稳定的，且做过严格测试，特别是东财的数据，可放心使用

> 添加其他数据提供商， 请参考[数据扩展教程](https://zvtvz.github.io/zvt/#/data_extending)

## 3. 数据
下面介绍如何用一种**统一**的方式来回答三个问题：**有什么数据？如何更新数据？如何查询数据？**

### 3.1 有什么数据?
```
In [1]: from zvt.contract import zvt_context
In [2]: from zvt.domain import *
In [3]: zvt_context.schemas
[zvt.domain.dividend_financing.DividendFinancing,
 zvt.domain.dividend_financing.DividendDetail,
 zvt.domain.dividend_financing.SpoDetail...]
```
zvt_context.schemas为系统支持的schema,schema即表结构，即数据，其字段含义的查看方式如下：

* 源码

[domain](https://github.com/zvtvz/zvt/tree/master/zvt/domain)里的文件为schema的定义，查看相应字段的注释即可。

* help

输入schema.按tab提示其包含的字段，或者.help()
```
In [4]: FinanceFactor.help()
```

### 3.2 如何更新数据?
#### 只需要一个方法：record_data()

```
#股票列表
In [2]: Stock.record_data(provider='eastmoney')
#财务指标
In [3]: FinanceFactor.record_data(codes=['000338'])
#资产负债表
In [4]: BalanceSheet.record_data(codes=['000338'])
#利润表
In [5]: IncomeStatement.record_data(codes=['000338'])
#现金流量表
In [5]: CashFlowStatement.record_data(codes=['000338'])
```

其他数据依样画葫芦即可。

> 标准流程就是: Schema.record_data(provoder='your provoder',codes='the codes')

注意可选参数provider，其代表数据提供商，一个schema可以有多个provider,这是系统稳定的基石。

查看**已实现**的provider
```
In [12]: Stock.provider_map_recorder
Out[12]:
{'joinquant': zvt.recorders.joinquant.meta.china_stock_meta_recorder.JqChinaStockRecorder,
 'exchange': zvt.recorders.exchange.china_stock_list_spider.ExchangeChinaStockListRecorder,
 'eastmoney': zvt.recorders.eastmoney.meta.china_stock_meta_recorder.EastmoneyChinaStockListRecorder}
```
你可以使用任意一个provider来获取数据，默认使用第一个。


再举个例子，股票板块数据获取：
```
In [13]: Block.provider_map_recorder
Out[13]:
{'eastmoney': zvt.recorders.eastmoney.meta.china_stock_category_recorder.EastmoneyChinaBlockRecorder,
 'sina': zvt.recorders.sina.meta.sina_china_stock_category_recorder.SinaChinaBlockRecorder}

In [14]: Block.record_data(provider='sina')
Block registered recorders:{'eastmoney': <class 'zvt.recorders.eastmoney.meta.china_stock_category_recorder.EastmoneyChinaBlockRecorder'>, 'sina': <class 'zvt.recorders.sina.meta.sina_china_stock_category_recorder.SinaChinaBlockRecorder'>}
2020-03-04 23:56:48,931  INFO  MainThread  finish record sina blocks:industry
2020-03-04 23:56:49,450  INFO  MainThread  finish record sina blocks:concept
```

再多了解一点record_data：
* 参数codes代表需要抓取的股票代码
* 不传入codes则是全市场抓取
* 该方法会把数据存储到本地并只做增量更新

定时任务的方式更新可参考[东财数据定时更新](https://github.com/zvtvz/zvt/blob/master/examples/recorders/eastmoney_data_runner1.py)

### 3.3 如何查询数据？
#### 只需要一个方法：query_data()

2018年年报 roe>8% 营收增长>8% 的前20个股
```
In [38]: df=FinanceFactor.query_data(filters=[FinanceFactor.roe>0.08,FinanceFactor.report_period=='year',FinanceFactor.op_income_growth_yoy>0.08],start_timestamp='2019-01-01',order=FinanceFactor.roe.desc(),limit=20,columns=["code"]+FinanceFactor.important_cols(),index='code')

In [39]: df
Out[39]:
          code  basic_eps  total_op_income    net_profit  op_income_growth_yoy  net_profit_growth_yoy     roe    rota  gross_profit_margin  net_margin  timestamp
code
000048  000048     1.1193     3.437000e+09  4.374000e+08                1.2179                 3.8122  0.5495  0.0989               0.4286      0.1308 2019-04-15
000629  000629     0.3598     1.516000e+10  3.090000e+09                0.6068                 2.5796  0.5281  0.2832               0.2752      0.2086 2019-03-26
000672  000672     1.8100     5.305000e+09  1.472000e+09                0.1563                 0.8596  0.5047  0.2289               0.4670      0.2803 2019-04-11
000912  000912     0.3500     4.405000e+09  3.516000e+08                0.1796                 1.2363  4.7847  0.0539               0.2175      0.0795 2019-03-20
000932  000932     2.2483     9.137000e+10  6.780000e+09                0.1911                 0.6453  0.4866  0.1137               0.1743      0.0944 2019-03-28
002607  002607     0.2200     6.237000e+09  1.153000e+09                0.5472                 1.1967  0.7189  0.2209               0.5908      0.1848 2019-04-09
002959  002959     2.0611     2.041000e+09  1.855000e+08                0.2396                 0.2657  0.5055  0.2075               0.3251      0.0909 2019-07-15
300107  300107     1.1996     1.418000e+09  6.560000e+08                1.6467                 6.5338  0.5202  0.4661               0.6379      0.4625 2019-03-15
300618  300618     3.6900     2.782000e+09  7.076000e+08                0.8994                 0.5746  0.4965  0.2504               0.4530      0.2531 2019-04-26
300776  300776     3.3900     3.649000e+08  1.679000e+08                1.2059                 1.5013  0.7122  0.2651               0.6207      0.4602 2019-02-18
300792  300792     2.7100     1.013000e+09  1.626000e+08                0.4378                 0.1799  0.4723  0.3797               0.4259      0.1606 2019-09-16
600399  600399     2.0100     5.848000e+09  2.607000e+09                0.1732                 2.9493  9.6467  0.2979               0.1453      0.4459 2019-03-29
600408  600408     0.8100     8.816000e+09  8.202000e+08                0.3957                 3.9094  0.7501  0.1681               0.1535      0.1020 2019-03-22
600423  600423     0.9000     2.009000e+09  3.903000e+08                0.0975                 5.3411  1.6695  0.1264               0.1404      0.1871 2019-03-19
600507  600507     2.0800     1.729000e+10  2.927000e+09                0.2396                 0.1526  0.5817  0.3216               0.3287      0.1696 2019-02-22
600678  600678     0.0900     4.240000e+08  3.168000e+07                1.2925                 0.0948  0.7213  0.0689               0.2183      0.0742 2019-03-14
600793  600793     1.6568     1.293000e+09  1.745000e+08                0.1164                 0.8868  0.7490  0.0486               0.1622      0.1350 2019-04-30
600870  600870     0.0087     3.096000e+07  4.554000e+06                0.7773                 1.3702  0.7458  0.0724               0.2688      0.1675 2019-03-30
601003  601003     1.7987     4.735000e+10  4.610000e+09                0.1394                 0.7420  0.5264  0.1920               0.1439      0.0974 2019-03-29
603379  603379     2.9400     4.454000e+09  1.108000e+09                0.1423                 0.1609  0.5476  0.3547               0.3959      0.2488 2019-03-13
```

以上，基本上就可以应付大部分日常数据的使用了。  
如果你想扩展数据，可以参考详细文档里的数据部分。
## 4. 数据即策略
在介绍系统设计的二维索引多标的计算模型之前，我们先来介绍一种自由(solo)的策略模式。
所谓策略回测，无非就是，重复以下过程：
### 在某时间点，找到符合条件的标的，对其进行买卖，看其表现。
因为系统所有的数据都是时间序列数据，有着统一的查询方式，通过query_data可以快速得到符合条件的标的，所以，即使只会query_data,也可以solo一把了。

[例子](https://github.com/zvtvz/zvt/blob/master/examples/trader/solo_traders.py)
```
class MySoloTrader(StockTrader):
    def on_time(self, timestamp):
        # 增持5000股以上,买买买
        long_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                            filters=[ManagerTrading.volume > 5000], columns=[ManagerTrading.entity_id],
                                            order=ManagerTrading.volume.desc(), limit=10)
        # 减持5000股以上，闪闪闪
        short_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                             filters=[ManagerTrading.volume < -5000],
                                             columns=[ManagerTrading.entity_id],
                                             order=ManagerTrading.volume.asc(), limit=10)
        if pd_is_not_null(long_df) or pd_is_not_null(short_df):
            try:
                self.trade_the_targets(due_timestamp=timestamp, happen_timestamp=timestamp,
                                       long_selected=set(long_df['entity_id'].to_list()),
                                       short_selected=set(short_df['entity_id'].to_list()))
            except Exception as e:
                self.logger.error(e)
```
你可以发挥想象力，社保重仓买买买，外资重仓买买买，董事长跟小姨子跑了卖卖卖......

然后，刷新一下[http://127.0.0.1:8050/](http://127.0.0.1:8050/)，看你运行策略的performance

更多可参考[策略例子](https://github.com/zvtvz/zvt/tree/master/examples/trader)

## 5. 计算
简单的计算可以通过query_data来完成，这里说的是系统设计的二维索引多标的计算模型。

下面以技术因子为例对**计算流程**进行说明:
```
In [7]: from zvt.factors.technical_factor import *
In [8]: factor = BullFactor(codes=['000338','601318'],start_timestamp='2019-01-01',end_timestamp='2019-06-10', transformer=MacdTransformer())
```
### data_df
data_df为factor的原始数据，即通过query_data从数据库读取到的数据,为一个**二维索引**DataFrame
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
factor_df为transformer对data_df进行计算后得到的数据，设计因子即对[transformer](https://github.com/zvtvz/zvt/blob/master/zvt/factors/factor.py#L18)进行扩展，例子中用的是MacdTransformer()。

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
result_df为可用于选股器的**二维索引**DataFrame，通过对data_df或factor_df计算来实现。
该例子在计算macd之后，利用factor_df,黄白线在0轴上为True,否则为False，[具体代码](https://github.com/zvtvz/zvt/blob/master/zvt/factors/technical_factor.py#L56)

```
In [14]: factor.result_df
Out[14]:
                            score
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

不同类型Factor的result_df格式如下：

* filter类型
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/filter_factor.png'/></p>

* score类型
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/score_factor.png'/></p>

结合选股器和回测，整个流程如下：
<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/flow.png'/></p>

## 5. 🚀开发

### 5.1 clone代码

```
git clone https://github.com/zvtvz/zvt.git
```

设置项目的virtual env(python>=3.6),安装依赖
```
pip3 install -r requirements.txt
pip3 install pytest
```

### 5.2 测试案例
pycharm导入工程(推荐,你也可以使用其他ide)，然后pytest跑测试案例

<p align="center"><img src='https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/pytest.jpg'/></p>

大部分功能使用都可以从tests里面参考

## 💡贡献
期待能有更多的开发者参与到 zvt 的开发中来，我会保证尽快 Reivew PR 并且及时回复。但提交 PR 请确保

先看一下[1分钟代码规范](https://github.com/zvtvz/zvt/blob/master/code_of_conduct.md)

1. 通过所有单元测试，如若是新功能，请为其新增单元测试
2. 遵守开发规范
3. 如若需要，请更新相对应的文档

也非常欢迎开发者能为 zvt 提供更多的示例，共同来完善文档。

## 💌请作者喝杯咖啡

如果你觉得项目对你有帮助,可以请作者喝杯咖啡  
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/alipay-cn.png" width="25%" alt="Alipay">　　　　　
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/wechat-cn.png" width="25%" alt="Wechat">

## 🤝联系方式  

加微信进群:foolcage 添加暗号:zvt  
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/wechat.jpeg" width="25%" alt="Wechat">

------
微信公众号:  
<img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/gongzhonghao.jpg" width="25%" alt="Wechat">

知乎专栏:  
https://zhuanlan.zhihu.com/automoney

## Thanks
<p><a href=https://www.jetbrains.com/?from=zvt><img src="https://raw.githubusercontent.com/zvtvz/zvt/master/docs/imgs/jetbrains.png" width="25%" alt="jetbrains"></a></p>
