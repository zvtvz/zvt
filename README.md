[![image](https://img.shields.io/pypi/v/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/pyversions/zvt.svg)](https://pypi.org/project/zvt/)
[![Build Status](https://api.travis-ci.org/zvtvz/zvt.svg?branch=master)](https://travis-ci.org/zvtvz/zvt)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
[![HitCount](http://hits.dwyl.io/zvtvz/zvt.svg)](http://hits.dwyl.io/zvtvz/zvt)

**Read this in other languages: [English](README-en.md).**  

ZVT是在[fooltrader](https://github.com/foolcage/fooltrader)的基础上重新思考后编写的量化项目，其包含可扩展的数据recorder，api，因子计算，选股，回测，交易,以及统一的可视化，定位为**中低频** **多级别** **多因子** **多标的** 全市场分析和交易框架。

##  🔖5分钟用起来

>"一个系统，如果5分钟用不起来，那肯定是设计软件的人本身就没想清楚，并且其压根就没打算自己用。" ------ foolcage

假设你已经在>=python3.6的环境中(建议新建一个干净的virtual env环境)
```
pip3 install zvt ipython
```

如果慢，试下这样
```
pip3 install zvt ipython -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
```

进入ipython,体验一把
```
In [1]: import os

In [2]: os.environ["TESTING_ZVT"] = "1"

In [3]: from zvt import *
start unzip /Users/xuanqi/workspace/github/zvtvz/zvt/zvt/sample_data/data.zip to /Users/xuanqi/zvt-test-home/data
finish unzip /Users/xuanqi/workspace/github/zvtvz/zvt/zvt/sample_data/data.zip to /Users/xuanqi/zvt-test-home/data
zvt env:{'data_path': '/Users/xuanqi/zvt-test-home/data', 'domain_module': 'zvt.domain', 'ui_path': '/Users/xuanqi/zvt-test-home/ui', 'log_path': '/Users/xuanqi/zvt-test-home/logs', 'jq_username': None, 'jq_password': None}

In [5]: from zvt.api import *

In [6]: df = get_kdata(entity_id='stock_sz_000338',provider='joinquant')

n [8]: df.tail()
Out[8]:
                                    id        entity_id  timestamp   provider    code  name level   open  close   high    low       volume      turnover change_pct turnover_rate
timestamp
2019-10-29  stock_sz_000338_2019-10-29  stock_sz_000338 2019-10-29  joinquant  000338  潍柴动力    1d  12.00  11.78  12.02  11.76   28533132.0  3.381845e+08       None          None
2019-10-30  stock_sz_000338_2019-10-30  stock_sz_000338 2019-10-30  joinquant  000338  潍柴动力    1d  11.74  12.05  12.08  11.61   42652561.0  5.066013e+08       None          None
2019-10-31  stock_sz_000338_2019-10-31  stock_sz_000338 2019-10-31  joinquant  000338  潍柴动力    1d  12.05  11.56  12.08  11.50   77329380.0  9.010439e+08       None          None
2019-11-01  stock_sz_000338_2019-11-01  stock_sz_000338 2019-11-01  joinquant  000338  潍柴动力    1d  11.55  12.69  12.70  11.52  160732771.0  1.974125e+09       None          None
2019-11-04  stock_sz_000338_2019-11-04  stock_sz_000338 2019-11-04  joinquant  000338  潍柴动力    1d  12.77  13.00  13.11  12.77  126673139.0  1.643788e+09       None          None
```

财务数据
```
In [12]: from zvt.domain import *
In [13]: df = get_finance_factor(entity_id='stock_sz_000338',columns=FinanceFactor.important_cols())

In [14]: df.tail()
Out[14]:
            basic_eps  total_op_income    net_profit  op_income_growth_yoy  net_profit_growth_yoy     roe    rota  gross_profit_margin  net_margin  timestamp
timestamp
2018-10-31       0.73     1.182000e+11  6.001000e+09                0.0595                 0.3037  0.1647  0.0414               0.2164      0.0681 2018-10-31
2019-03-26       1.08     1.593000e+11  8.658000e+09                0.0507                 0.2716  0.2273  0.0589               0.2233      0.0730 2019-03-26
2019-04-29       0.33     4.521000e+10  2.591000e+09                0.1530                 0.3499  0.0637  0.0160               0.2166      0.0746 2019-04-29
2019-08-30       0.67     9.086000e+10  5.287000e+09                0.1045                 0.2037  0.1249  0.0315               0.2175      0.0759 2019-08-30
2019-10-31       0.89     1.267000e+11  7.058000e+09                0.0721                 0.1761  0.1720  0.0435               0.2206      0.0736 2019-10-31

```

跑个策略
```
In [15]: from zvt.samples import *
In [16]: t = MyMaTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
   ...:                end_timestamp='2019-06-30', trader_name='000338_ma_trader')
In [17]: t.run()

```
<p align="center"><img src='./docs/imgs/output-value.jpg'/></p>

## 📝配置正式环境

>待完善

**注意**：
>可视化方面，master分支只保留行情指标功能，其他复杂功能在[draft分支](https://github.com/zvtvz/zvt/tree/draft)里面存档
>项目将专注于一般行情软件难以实现的自定义统计指标，回测，交易通知上面
## 详细文档
文档地址(两个是一样的,只是为了方便有些不方便访问github的同学)  
[http://zvt.foolcage.com](http://zvt.foolcage.com)  
[https://zvtvz.github.io/zvt](https://zvtvz.github.io/zvt)
> 目前整个框架基本稳定下来,文档完善中。

##  ✨ 特性
- **丰富全面开箱即用且可持续增量更新的数据**
    - A股数据:行情,财务报表,大股东行为,高管交易,分红融资详情,个股板块资金流向,融资融券,龙虎榜等数据
    - 市场整体pe,pb,资金流，融资融券，外资动向等数据
    - 数字货币数据
- 数据的标准化,多数据源(provider)交叉验证,补全
- **简洁可扩展的数据框架**
- **统一简洁的API,支持sql查询,支持pandas**
- 可扩展的factor,对单标的和多标的的运算抽象了一种统一的计算方式
- **支持多标的,多factor,多级别的回测方式**
- 支持交易信号和策略使用到的factor的实时可视化
- 支持多种实盘交易(实现中)

##  🔰安装

### 注册聚宽(可选)
项目数据支持多provider，在数据schema一致性的基础上，可根据需要进行选择和扩展，目前支持新浪，东财，网易,交易所，ccxt等免费数据。

但免费数据的缺点是显而易见的:不稳定，爬取清洗数据耗时耗力，维护代价巨大，且随时可能不可用。  
个人建议：如果只是学习研究，可以使用免费数据；如果是真正有意投身量化，还是选一家可靠的数据提供商。

项目支持聚宽的数据，可戳以下链接申请使用（目前可免费使用一年）  
https://www.joinquant.com/default/index/sdk?channelId=953cbf5d1b8683f81f0c40c9d4265c0d

需要提高每日使用限额或者购买也可加我微信(foolcage)，申请相应的优惠

> 项目中大部分的免费数据目前都是比较稳定的，且做过严格测试，特别是东财的数据，可放心使用

> 添加其他数据提供商，请参考[数据扩展教程](http://www.foolcage.com/#/data_extending)

### 快速开始(只需3部)
#### 1.clone代码

```
git clone https://github.com/zvtvz/zvt.git
```

设置项目的virtual env(python>=3.6),安装依赖
```
pip3 install -r requirements.txt
```

#### 2.pycharm导入工程(推荐,你也可以使用其他ide)

解压data sample,用于快速跑测试
```
python3 init_data_sample.py
```

#### 3.下载数据，运行
更改DATA_PATH（否则会污染datasample,datasample只用于测试用）
```
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
```

东财数据: https://pan.baidu.com/s/1CMAlCRYwlhGVxS6drYUEgA 提取码: q2qn  
日线数据(网易): https://pan.baidu.com/s/1kMhEVO0kH_Pn6wXKyqvJEA 提取码: ijxg  
资金流，板块数据(新浪): https://pan.baidu.com/s/1eusW65sdK_WE4icnt8JS1g 提取码: uux3  
市场概况，沪/深港通，融资融券数据(聚宽): https://pan.baidu.com/s/1ijrgjUd1WkRMONrwRQU-4w 提取码: dipd  

把下载的数据解压到DATA_PATH


增量更新数据，只需要运行[recorders](./zvt/recorders)里面的脚本


## 💌请作者喝杯咖啡

如果你觉得项目对你有帮助,可以请作者喝杯咖啡  
<img src="./docs/imgs/alipay-cn.png" width="25%" alt="Alipay">　　　　　
<img src="./docs/imgs/wechat-cn.png" width="25%" alt="Wechat">


## 💡 贡献

期待能有更多的开发者参与到 zvt 的开发中来，我会保证尽快 Reivew PR 并且及时回复。但提交 PR 请确保

1. 通过所有单元测试，如若是新功能，请为其新增单元测试
2. 遵守开发规范
3. 如若需要，请更新相对应的文档

也非常欢迎开发者能为 zvt 提供更多的示例，共同来完善文档，文档项目位于 [zvt/docs](https://github.com/zvtvz/zvt/docs)

## 联系方式  

QQ群:300911873  

个人微信:foolcage 添加暗号:zvt

公众号(后续会不定时更新一些教程):  
<img src="./docs/imgs/gongzhonghao.jpg" width="25%" alt="Wechat">

知乎专栏会结合zvt写一些日常使用的例子:　
https://zhuanlan.zhihu.com/automoney
