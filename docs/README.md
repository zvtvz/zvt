[![github](https://img.shields.io/github/stars/zvtvz/zvt.svg)](https://github.com/zvtvz/zvt)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![Build Status](https://api.travis-ci.org/zvtvz/zvt.svg?branch=master)](https://travis-ci.org/zvtvz/zvt)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
## ZVT是什么?

ZVT是在[fooltrader](https://github.com/foolcage/fooltrader)的基础上重新思考后编写的量化项目，其包含可扩展的数据recorder，api，因子计算，选股，回测，交易,定位为**中低频** **多级别** **多标的** **多因子** 全市场分析和交易框架。

## ZVT还是什么?

 - 从文字看,zero vector trader,寓意市场为各种向量合力的结果,而要看清市场,只能做一个零向量.
 - 从形态看,Z V T本身暗合市场的典型形态,寓意市场几何结构的重要性.
 - 而zvt图标的含义,大家可自行解读

<p align="center"><img src='./imgs/zvt-ok.gif'/></p>

## 功能

- A股数据:行情,财务报表,大股东行为,高管交易,分红融资详情,个股板块资金流向,融资融券,龙虎榜等数据
- 数字货币数据
- 数据的标准化,多数据源(provider)交叉验证,补全
- 数据recorder非常容易扩展
- 统一简洁的API,支持sql查询,支持pandas
- 可扩展的factor,对单标的和多标的的运算抽象了一种统一的计算方式
- 提供了factor统一的可视化方式
- 支持多标的,多factor,多级别的回测方式
- 支持交易信号和策略使用到的factor的实时可视化
- 支持多种实盘交易(实现中)