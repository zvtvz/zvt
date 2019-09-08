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