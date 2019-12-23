## 1. 数据是什么？

没有数据，量化便成了空中楼阁。

那么，在量化中，数据到底是什么？

zvt对量化数据进行了非常简单而统一的抽象：数据就是 **投资标的** 在**某时间点(段)** 所**发生的事情**的描述。

其中，投资标的，叫**entity**；时间点(段)，叫**timestamp**；事情的描述根据事情的不同而具有不同的**属性**。

### 1.1 投资标的(entity)

首先，我们得有投资标的。

而在整个市场里，投资标的一定会有三个属性:

* **证券类型(entity_type)**

股票(stock)，债券(bond)，期货(future)，数字货币(coin)，基金(fund)等

* **交易所(exchange)**

上海证券交易所(sh)，深圳证券交易所(sz)等

* **代码(code)**

000338,601318,BTC/USDT等

所以，zvt里面投资标的的唯一编码(entity_id)为:{entity_type}\_{exchange}\_{code}

[entity基类](https://github.com/zvtvz/zvdata/blob/master/zvdata/__init__.py#L221)定义如下:
```
class EntityMixin(Mixin):
    entity_type = Column(String(length=64))
    exchange = Column(String(length=32))
    code = Column(String(length=64))
    name = Column(String(length=128))
```

### 1.2 投资标的发生的事情

而投资标的发生的事情，一定会有三个属性：
* **entity_id**

投资标的的id

* **timestamp**

发生的时间

* **id**

事件的唯一编码，一般使情况下格式为:{entity_id}_{timestamp}

[entity发生的事情](https://github.com/zvtvz/zvdata/blob/master/zvdata/__init__.py#L128)定义如下:
```
class Mixin(object):
    id = Column(String, primary_key=True)
    entity_id = Column(String)

    # the meaning could be different for different case,most of time it means 'happen time'
    timestamp = Column(DateTime)
```

>注意，上面EntityMixin继承了Mixin，如何理解？
>entity的诞生其实也是一个事件，这时，timestamp就代表其上市日。

## 2. 定义具体的数据
市场没有新鲜事，市场数据更没有新鲜事。

对市场理解越深，就越能定义出稳定的市场数据结构。

而对市场的理解并不是一蹴而就的，这就要求数据结构的设计必须具有可扩展性。

那么,什么是**稳定**并具有**可扩展性**的数据结构？

稳定至少要达到以下的标准:
* **标准的字段**

不管数据来源何处，**确定的语义**在系统里面必须对应**确定的字段**；净资产收益率就叫roe,每股收益就叫eps,毛利率就叫gross_profit_margin。

* **完全分类(正交)**

技术面，基本面，宏观面，消息面等。

* **层次关系**

原始数据和衍生(计算)数据的关系，比如k线数据和各种技术指标；财报和各种财务指标。

而扩展性最重要的就是，**容易添加新数据**，并使得新数据无缝融入到系统中。

数据定义的目录为[domain](https://github.com/zvtvz/zvt/tree/master/zvt/domain)

## 3. 系统都有哪些数据？
```
In [1]: from zvt.domain import *
In [2]: global_schemas
[zvt.domain.dividend_financing.DividendFinancing,
 zvt.domain.dividend_financing.DividendDetail,
 zvt.domain.dividend_financing.SpoDetail...]
```

global_schemas就是系统支持的所有数据，具体含义可以查看相应源码的注释，或者调用相应schema的help方法:
```
In [3]: DividendFinancing.help()
class DividendFinancing(DividendFinancingBase, Mixin):
    __tablename__ = 'dividend_financing'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 分红总额
    dividend_money = Column(Float)

    # 新股
    ipo_issues = Column(Float)
    ipo_raising_fund = Column(Float)

    # 增发
    spo_issues = Column(Float)
    spo_raising_fund = Column(Float)
    # 配股
    rights_issues = Column(Float)
    rights_raising_fund = Column(Float)
```

## 4. 如何查询数据？
所有的schema都有[query_data](https://github.com/zvtvz/zvdata/blob/master/zvdata/__init__.py#L65)方法,你可以用一种统一的方式查询数据。

## 5. 如果更新数据?
所有的schema都有[record_data](https://github.com/zvtvz/zvdata/blob/master/zvdata/__init__.py#L193)方法,你可以用一种统一的方式来做数据的更新。
```
In [17]: FinanceFactor.recorders
Out[17]: [zvt.recorders.eastmoney.finance.china_stock_finance_factor_recorder.ChinaStockFinanceFactorRecorder]

In [18]: FinanceFactor.record_data(codes=['000338'])
FinanceFactor registered recorders:[<class 'zvt.recorders.eastmoney.finance.china_stock_finance_factor_recorder.ChinaStockFinanceFactorRecorder'>]
auth success  ( 如需说明文档请查看：https://url.cn/5oB7EOO，更多问题请联系JQData管理员，微信号：JQData02 )
INFO  MainThread  2019-12-15 18:03:35,493  ChinaStockFinanceFactorRecorder:recorder.py:551  evaluate_start_end_size_timestamps  entity_id:stock_sz_000338,timestamps start:2002-12-31 00:00:00,end:2019-09-30 00:00:00
INFO  MainThread  2019-12-15 18:03:35,509  ChinaStockFinanceFactorRecorder:recorder.py:556  evaluate_start_end_size_timestamps  latest record timestamp:2019-10-31 00:00:00
INFO  MainThread  2019-12-15 18:03:35,510  ChinaStockFinanceFactorRecorder:recorder.py:348  run  entity_id:stock_sz_000338,evaluate_start_end_size_timestamps result:None,None,0,None
INFO  MainThread  2019-12-15 18:03:35,510  ChinaStockFinanceFactorRecorder:recorder.py:357  run  finish recording <class 'zvt.domain.finance.FinanceFactor'> for entity_id:stock_sz_000338,latest_timestamp:None
已退出
```
* codes代表需要抓取的股票代码
* 不传入codes则是全市场抓取
* 所有的schema对应的数据更新，方法是一致的

定时任务的方式更新可参考[runners](https://github.com/zvtvz/zvt/blob/master/zvt/recorders/eastmoney/finance0_runner.py)

## 数据结构

zvt数据最重要的概念如下：
- ### provider

数据提供商

- ### data_schema

数据的定义，对应sql的table

- ### entity_type
实体类型，目前代表各种投资标的

## 查询系统注册数据
数据都是 **自注册** 和 **可扩展** 的，你可以通过下面的方式进行查询:

### 查询注册的provider
```
In [1]: from zvt import *
In [2]: get_providers()
Out[2]: 
['zvdata',
 'zvt',
 'ccxt',
 'eastmoney',
 'exchange',
 'joinquant',
 'sina',
 'netease']
```

### 查询provider提供的schema
```
In [5]: get_schemas(provider='eastmoney')
Out[5]: 
[zvt.domain.dividend_financing.DividendFinancing,
 zvt.domain.dividend_financing.DividendDetail,
 zvt.domain.dividend_financing.SpoDetail,
 zvt.domain.dividend_financing.RightsIssueDetail,
 zvt.domain.finance.BalanceSheet,
 zvt.domain.finance.IncomeStatement,
 zvt.domain.finance.CashFlowStatement,
 zvt.domain.finance.FinanceFactor,
 zvt.domain.holder.TopTenTradableHolder,
 zvt.domain.holder.TopTenHolder,
 zvt.domain.holder.InstitutionalInvestorHolder,
 zvt.domain.stock_meta.StockIndex,
 zvt.domain.stock_meta.Index,
 zvt.domain.stock_meta.Stock,
 zvt.domain.quote.Index1wkKdata,
 zvt.domain.quote.Index1monKdata,
 zvt.domain.trading.ManagerTrading,
 zvt.domain.trading.HolderTrading,
 zvt.domain.trading.BigDealTrading,
 zvt.domain.trading.MarginTrading,
 zvt.domain.trading.DragonAndTiger]
```

schema具体字段的含义目前可以直接查看源码，里面每个字段都有注释。

### 查询注册的entity_type
```
In [2]: get_entity_types()    
Out[2]: ['coin', 'index', 'stock']
```

## 使用数据的方式
有了provider,data_schema和entity_type，我们就可以以一种统一的方式来对数据进行操作。

### 个股K线
```
In [4]: from zvt.api import *
In [5]: get_kdata(provider='joinquant',entity_id='stock_sz_000338')
Out[5]: 
                                    id        entity_id  timestamp   provider    code  name level   open  hfq_open   qfq_open  close  hfq_close  qfq_close   high  hfq_high   qfq_high    low  hfq_low    qfq_low      volume      turnover  change_pct  turnover_rate     factor
timestamp
2007-04-30  stock_sz_000338_2007-04-30  stock_sz_000338 2007-04-30  joinquant  000338  潍柴动力    1d  70.00     70.00   3.649141  64.93      64.93   3.384839  71.00     71.00   3.701272  62.88    62.88   3.277972  20737497.0  1.365189e+09    217.1959        11.8154   1.000000
2007-05-08  stock_sz_000338_2007-05-08  stock_sz_000338 2007-05-08  joinquant  000338  潍柴动力    1d  66.60     66.60   3.471897  64.00      64.00   3.336358  68.00     68.00   3.544880  62.88    62.88   3.277972   8629889.0  5.563198e+08     -1.4323         4.9170   1.000000
2007-05-09  stock_sz_000338_2007-05-09  stock_sz_000338 2007-05-09  joinquant  000338  潍柴动力    1d  63.32     63.32   3.300909  62.00      62.00   3.232097  63.88     63.88   3.330102  59.60    59.60   3.106983   9382251.0  5.782065e+08     -3.1250         5.3456   1.000000
2007-05-10  stock_sz_000338_2007-05-10  stock_sz_000338 2007-05-10  joinquant  000338  潍柴动力    1d  61.50     61.50   3.206031  62.49      62.49   3.257641  64.48     64.48   3.361380  61.01    61.01   3.180487   4772011.0  2.999226e+08      0.7903         2.7189   1.000000
```

### 数字货币k线
```
In [7]: get_kdata(entity_id='coin_binance_EOS/USDT',provider='ccxt')
Out[7]: 
                                          id              entity_id  timestamp provider      code      name level     open    close     high      low       volume turnover
timestamp
2018-05-28  coin_binance_EOS/USDT_2018-05-28  coin_binance_EOS/USDT 2018-05-28     ccxt  EOS/USDT  EOS/USDT    1d  12.4900  11.4788  12.6500  11.2800   3494258.32     None
2018-05-29  coin_binance_EOS/USDT_2018-05-29  coin_binance_EOS/USDT 2018-05-29     ccxt  EOS/USDT  EOS/USDT    1d  11.4853  12.1112  12.4650  10.7000   6709192.34     None
2018-05-30  coin_binance_EOS/USDT_2018-05-30  coin_binance_EOS/USDT 2018-05-30     ccxt  EOS/USDT  EOS/USDT    1d  12.1113  11.8968  12.8200  11.6206   6514864.18     None
2018-05-31  coin_binance_EOS/USDT_2018-05-31  coin_binance_EOS/USDT 2018-05-31     ccxt  EOS/USDT  EOS/USDT    1d  11.8712  12.2353  12.7400  11.8116   6540020.80     None
2018-06-01  coin_binance_EOS/USDT_2018-06-01  coin_binance_EOS/USDT 2018-06-01     ccxt  EOS/USDT  EOS/USDT    1d  12.2351  12.2048  12.3889  11.8354   5946136.88     None

```

### 社保持仓
```
In [11]: from zvt.domain import *
In [12]: df = get_top_ten_tradable_holder(start_timestamp='2018-09-30',filters=[TopTenTradableHolder.holder_name.like('%社保%')],order=TopTenTradableHolder.shareholding_ratio.desc())

In [9]: df.tail()
Out[9]: 
                                                         id        entity_id  timestamp provider    code report_period report_date holder_code  holder_name  shareholding_numbers  shareholding_ratio     change  change_ratio
timestamp
2019-03-31  stock_sz_000778_2019-03-31 00:00:00_全国社保基金四一三组合  stock_sz_000778 2019-03-31     None  000778       season1  2019-03-31    70010413  全国社保基金四一三组合            17800000.0              0.0045        NaN           NaN
2019-03-31  stock_sz_002572_2019-03-31 00:00:00_全国社保基金一零九组合  stock_sz_002572 2019-03-31     None  002572       season1  2019-03-31    70010109  全国社保基金一零九组合             7520000.0              0.0118 -8013000.0       -0.5159
2019-06-30  stock_sz_000778_2019-06-30 00:00:00_全国社保基金五零三组合  stock_sz_000778 2019-06-30     None  000778     half_year  2019-06-30    70010503  全国社保基金五零三组合            60000000.0              0.0153        NaN           NaN
2019-06-30  stock_sz_000338_2019-06-30 00:00:00_全国社保基金一零一组合  stock_sz_000338 2019-06-30     None  000338     half_year  2019-06-30    70010101  全国社保基金一零一组合            35250000.0              0.0057 -1600000.0       -0.0434
2019-06-30  stock_sz_000001_2019-06-30 00:00:00_全国社保基金一零四组合  stock_sz_000001 2019-06-30     None  000001     half_year  2019-06-30    70010104  全国社保基金一零四组合            55170000.0              0.0032        NaN           NaN

```

### 马云持仓 ###
```bash
In [26]: df = get_top_ten_tradable_holder(filters=[TopTenTradableHolder.holder_name=='马云'])
Out[27]: 
   holder_name    code  shareholding_numbers  shareholding_ratio      change  change_ratio
0           马云  002204              460800.0              0.0085         NaN           NaN
1           马云  300027             3912000.0              0.0205         NaN           NaN
2           马云  300027             8319000.0              0.0230         NaN           NaN
3           马云  300027             8319000.0              0.0230         NaN           NaN

22          马云  300027            99780000.0              0.0520         NaN           NaN
23          马云  300027            99780000.0              0.0520         NaN           NaN
24          马云  300027            99780000.0              0.0451         NaN           NaN
```
### 2018年报eps前50
```bash
In [30]: df = get_finance_factor(start_timestamp='2018-12-31',order=FinanceFactor.basic_eps.desc(),limit=50,columns=[FinanceFactor.code,FinanceFactor.timestamp,FinanceFactor.basic_eps])
Out[31]: 
      code  timestamp  basic_eps
0   600519 2018-12-31    28.0200
1   603444 2018-12-31    10.1200
2   601318 2018-12-31     6.0200
3   000661 2018-12-31     5.9200

47  603393 2018-12-31     2.0900
48  601869 2018-12-31     2.0900
49  600507 2018-12-31     2.0800

```

### 统一的方式get_data
以上api的调用最后都是通过get_data来实现的，你也可以直接使用get_data
```
In [13]: df=get_data(provider='eastmoney',data_schema=FinanceFactor,filters=[FinanceFactor.roe>=0.15,FinanceFactor.report_date==pd.Timestamp('2018-12-31')],columns=[FinanceFactor.code,F
    ...: inanceFactor.timestamp,FinanceFactor.report_date,FinanceFactor.roe])

In [14]: df
Out[14]: 
              code  timestamp report_date     roe
timestamp                                        
2019-01-30  000055 2019-01-30  2018-12-31  0.5317
2019-01-31  600738 2019-01-31  2018-12-31  0.6221
2019-02-01  300748 2019-02-01  2018-12-31  0.1620
2019-02-02  603225 2019-02-02  2018-12-31  0.1924
2019-02-16  600276 2019-02-16  2018-12-31  0.2360
2019-02-18  300776 2019-02-18  2018-12-31  0.7122

```


filters参数的使用请参考[*sqlalchemy*](https://docs.sqlalchemy.org/en/13/orm/query.html),SQL能做的查询都能做

## SQL查询
你也可以直接使用项目中的sqlite数据库,利用你熟悉的工具,语言来进行研究

比如:查看某段时间整个市场的高管增持减持
```
select * from manager_trading where volume < 0 and timestamp > '2018-01-01';
select count(id) from manager_trading where volume < 0 and timestamp > '2018-01-01';

select * from manager_trading where volume > 0 and timestamp > '2018-01-01';
select count(id) from manager_trading where volume > 0 and timestamp > '2018-01-01'
```
<p align="center"><img src='./imgs/sql-usage.gif'/></p>

库都给你了,SQL大神,请开始你的表演