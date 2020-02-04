[![github](https://img.shields.io/github/stars/zvtvz/zvt.svg)](https://github.com/zvtvz/zvt)
[![image](https://img.shields.io/pypi/v/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/pyversions/zvt.svg)](https://pypi.org/project/zvt/)
[![Build Status](https://api.travis-ci.org/zvtvz/zvt.svg?branch=master)](https://travis-ci.org/zvtvz/zvt)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
[![HitCount](http://hits.dwyl.io/zvtvz/zvt.svg)](http://hits.dwyl.io/zvtvz/zvt)

ZVT是在[fooltrader](https://github.com/foolcage/fooltrader)的基础上重新思考后编写的量化项目，其包含可扩展的数据recorder，api，因子计算，选股，回测，交易,以及统一的可视化，定位为**中低频** **多级别** **多因子** **多标的** 全市场分析和交易框架。

相比其他的量化系统，其不依赖任何中间件，**非常轻，可测试，可推断，可扩展**。

编写该系统的初心:
* 构造一个中立标准的数据schema
* 能够容易地把各provider的数据适配到系统
* 相同的算法，只写一次，可以应用到任何市场
* 适用于低耗能的人脑+个人电脑

## ✨特性
- **丰富全面开箱即用可扩展可持续增量更新的数据**
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

## 💯关于该文档

该文档由[项目docs](https://github.com/zvtvz/zvt/tree/master/docs)自动生成，主要内容为项目的**基本用法**和**整体设计**,你应该仔细地阅读所有的章节。

现实中的使用例子会在公众号和知乎专栏中长期更新，其假设你已经读过此文档。

------
微信公众号:  

<img src="./imgs/gongzhonghao.jpg" width="25%" alt="Wechat">

知乎专栏:

https://zhuanlan.zhihu.com/automoney