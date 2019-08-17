**Read this in other languages: [English](README-en.md).**  

# 1. data schema and api
### 社保持仓 ###
```bash
In [20]: df = get_top_ten_tradable_holder(start_timestamp='2018-09-30',filters=[TopTenTradableHolder.holder_name.like('%社保%')],order=TopTenTradableHolder.shareholding_ratio.desc())
Out[21]: 
              holder_name    code  shareholding_numbers  shareholding_ratio      change  change_ratio
0             全国社保基金一零三组合  600511            20000000.0              0.0720   5000000.0        0.3333
1             全国社保基金一零三组合  002061            39990000.0              0.0715 -15000000.0       -0.2728
2             全国社保基金六零四组合  002539            38600000.0              0.0637  32500000.0        5.3271
3             全国社保基金六零四组合  002539            38600000.0              0.0637         NaN           NaN

779           全国社保基金一一三组合  601088             9258000.0              0.0005         NaN           NaN
780           全国社保基金四零七组合  601628            10950000.0              0.0004   1500000.0        0.1587
781           全国社保基金四零七组合  601628             9450000.0              0.0003         NaN           NaN

[782 rows x 6 columns]
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
里面包含很多数据,api用法都是一致的,掌握了一种,就掌握了所有.  
具体查看代码:  
[*data schema*](./zvt/domain/)  
[*data api*](./zvt/api/)  
# 2. recorder
如果你要扩展数据,可以通过继承[*recorder*](./zvt/recorders/recorder)里面的基类来实现.  
项目一部分的数据源以开源的方式直接提供,一部分闭源,只提供最终数据库文件(会发布在dropbox和qq群).

<p align="center"><img src='./docs/recorder.png'/></p>

# 4. factor
>"故经之以五事，校之以计，而索其情：一曰道，二曰天，三曰地，四曰将，五曰法。"------孙子兵法  

我看过各种量化平台的因子库,成千上万的,它们甚至用机器学习的方法试图去找出因子跟股价的关系,然而却忘了最简单的"乘法原理",或者说因子的正交.这一点,缠中说禅曾经有过非常精彩的论述:
>"当然，上面这三个独立的程序只是本ID随手而写，任何人都可以设计自己的独立交易程序组，但原则是一致的，就是三个程序组之间必须是互相独立的，像人气指标和资金面其实是一回事情，各种技术指标都是互相相关的等等，如果把三个非独立的程序弄在一起，一点意义都没有。就像有人告诉你，面首的鼻子大就不会“早泄”，另一个告诉你耳朵大不会“早泄”，第三个告诉你胡子多不会“早泄”，如果真按这三样来选人，估计连武则天大姐的奶妈的邻居的奶妈的邻居的奶妈的奶妈的奶妈，都会不满意的"

所以,只拥有一台破电脑的你,在后工业时代,最重要的是:你必须知道**标的们**在**某个时刻**在**某一方面**在**整个市场**中的位置.  
生存,还是死亡? 离散,还是连续?  
[*MustFactor*](./zvt/factors/factor.py#L120)  
[*ScoreFactor*](./zvt/factors/factor.py#L129)  

### 在一年内有被主人抛弃的个股
```bash
In [39]: factor = ManagerGiveUpFactor(the_timestamp='2018-12-31', window=pd.DateOffset(days=365)) 
In [40]: factor.run()
In [41]: factor.df
Out[41]: 
                                  volume  score
security_id     timestamp                      
stock_sh_600031 2018-12-31 -2.618000e+05  False
                2018-12-31 -2.209000e+05  False
                2018-12-31 -2.067667e+05  False
stock_sh_600089 2018-12-31 -2.226000e+03  False
stock_sh_600136 2018-12-31 -7.510333e+06  False
                2018-12-31 -6.791000e+06  False

stock_sz_300635 2018-12-31 -3.922000e+06  False
                2018-12-31 -2.020000e+06  False
stock_sz_300637 2018-12-31 -5.670000e+04  False
                2018-12-31 -5.670000e+04  False
                2018-12-31 -4.723667e+04  False
                2018-12-31 -4.133500e+04  False
                2018-12-31 -4.440800e+04  False
                2018-12-31 -3.937333e+04  False
                2018-12-31 -4.184857e+04  False
stock_sz_300699 2018-12-31 -1.506000e+04  False
                2018-12-31 -3.238000e+04  False
                2018-12-31 -2.784333e+04  False
                2018-12-31 -5.105750e+04  False
                2018-12-31 -4.494400e+04  False
                2018-12-31 -3.756417e+04  False
                2018-12-31 -3.234029e+04  False
                2018-12-31 -3.085900e+04  False

[318 rows x 2 columns]

```
### 营收利润增速评分
```bash
In [42]: from zvt.factors.finance_factor import *
In [43]: factor = FinanceGrowthFactor(window=pd.DateOffset(days=365), start_timestamp='2017-12-31',end_timestamp='2018-12-31')
In [43]: factor.run() 
In [44]: factor.df
Out[44]: 
                            op_income_growth_yoy  net_profit_growth_yoy
security_id     timestamp                                              
stock_sh_600000 2017-12-31                   NaN                    0.3
                2018-03-31                   NaN                    0.3
                2018-06-30                   NaN                    0.3
                2018-09-30                   NaN                    0.3
                2018-12-31                   NaN                    0.3
stock_sh_600004 2017-12-31                   0.3                    0.3
                2018-03-31                   NaN                    0.3
                2018-06-30                   0.3                    0.3
                2018-09-30                   0.3                    0.3
stock_sh_600006 2017-12-31                   0.3                    NaN
                2018-03-31                   NaN                    NaN
                2018-06-30                   0.0                    0.5
                2018-09-30                   0.0                    0.7
                2018-12-31                   0.0                    0.9
...                                          ...                    ...
stock_sz_300763 2017-12-31                   0.9                    0.9
                2018-12-31                   NaN                    0.3
stock_sz_300765 2017-12-31                   0.3                    NaN
                2018-06-30                   0.3                    0.3
                2018-12-31                   0.5                    0.3
stock_sz_300766 2017-12-31                   0.9                    0.9
                2018-12-31                   0.9                    0.7

[16116 rows x 2 columns]

```
# 4. selector
selector不过是各种factor的组合和权重的调整
# 5. trader
trader不过是selector在时间轴上的应用,然后看其表现
# 6. 如果贡献代码

## 6.1 架构图
<p align="center"><img src='./docs/architecture.png'/></p>

## 6.2 贡献方式

* 测试代码
* bug fix
* 数据源recorder实现
* score factor算法
* trader
* UI
* 文档教程

# 联系方式  
QQ群:300911873  
如果你喜欢该项目,请加星支持一下,并在申请入群时告知github user name.  
