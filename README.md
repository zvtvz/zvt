[![image](https://img.shields.io/pypi/v/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/l/zvt.svg)](https://pypi.org/project/zvt/)
[![image](https://img.shields.io/pypi/pyversions/zvt.svg)](https://pypi.org/project/zvt/)
[![Build Status](https://api.travis-ci.org/zvtvz/zvt.svg?branch=master)](https://travis-ci.org/zvtvz/zvt)
[![codecov.io](https://codecov.io/github/zvtvz/zvt/coverage.svg?branch=master)](https://codecov.io/github/zvtvz/zvt)
[![HitCount](http://hits.dwyl.io/zvtvz/zvt.svg)](http://hits.dwyl.io/zvtvz/zvt)

**Read this in other languages: [English](README-en.md).**  

ZVT是在[fooltrader](https://github.com/foolcage/fooltrader)的基础上重新思考后编写的量化项目，其包含可扩展的数据recorder，api，因子计算，选股，回测，交易,以及统一的可视化，定位为**中低频** **多级别** **多因子** **多标的** 全市场分析和交易框架。

#  🔖使用展示

### 板块资金流分析
<p align="center"><img src='./docs/imgs/data-usage/money-flow.gif'/></p>

### 市场历史pe分布
<p align="center"><img src='./docs/imgs/data-usage/sh-pe-distribution.gif'/></p>

### 多市场pe对比
<p align="center"><img src='./docs/imgs/data-usage/compare-pe.gif'/></p>

### 融资融券趋势
<p align="center"><img src='./docs/imgs/data-usage/margin-trending.gif'/></p>

### 外资资金流(沪/深港通)
<p align="center"><img src='./docs/imgs/data-usage/cross-market-trading.gif'/></p>

### 分红比较
<p align="center"><img src='./docs/imgs/data-usage/compare-dividend.gif'/></p>

### 多标的分红融资对比
<p align="center"><img src='./docs/imgs/data-usage/filter-entity.gif'/></p>

### 资产负债表分析
<p align="center"><img src='./docs/imgs/data-usage/balance-sheet.gif'/></p>

### 自定义factor
<p align="center"><img src='./docs/imgs/data-usage/tech-factor.gif'/></p>


[*trader examples*](./examples)  

### 算法交易信号和性能
<p align="center"><img src='./docs/imgs/trader_list_view.gif'/></p>

### 多标的交易
<p align="center"><img src='./docs/imgs/multiple-stock-macd.gif'/></p>

### 1分钟实时数字货币交易
<p align="center"><img src='./docs/imgs/realtime_signals.gif'/></p>

### 选股器的应用
<p align="center"><img src='./docs/imgs/fundamental-selector-in-notebook.png'/></p>

<p align="center"><img src='./docs/imgs/technical-selector-in-notebook.gif'/></p>

整个框架有着极高的可扩展性，只需要写极少的代码就可以对各模块进行扩展，各模块的扩展教程待完善，也需要大家的贡献。
#  ✨ 特性

- **丰富全面开箱即用且可持续增量更新的数据**
    - A股数据:行情,财务报表,大股东行为,高管交易,分红融资详情,个股板块资金流向,融资融券,龙虎榜等数据
    - 市场整体pe,pb,资金流，融资融券，外资动向等数据
    - 数字货币数据
- 数据的标准化,多数据源(provider)交叉验证,补全
- **简洁可扩展的数据框架**
- **统一简洁的API,支持sql查询,支持pandas**
- 可扩展的factor,对单标的和多标的的运算抽象了一种统一的计算方式
- **简洁统一的可视化分析方式**
- **支持多标的,多factor,多级别的回测方式**
- 支持交易信号和策略使用到的factor的实时可视化
- 支持多种实盘交易(实现中)

#  🔰安装

## 快速开始(只需3部)
### 1.clone代码

```
git clone https://github.com/zvtvz/zvt.git
```

设置项目的virtual env(python>=3.6),安装依赖
```
pip3 install -r requirements.txt
```

### 2.pycharm导入工程(推荐,你也可以使用其他ide)

解压data sample,用于快速跑测试
```
python3 init_data_sample.py
```

### 3.下载数据，运行
更改DATA_PATH（否则会污染datasample,datasample只用于测试用）
```
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
```

东财数据: https://pan.baidu.com/s/1CMAlCRYwlhGVxS6drYUEgA 提取码: q2qn  
日线数据(网易): https://pan.baidu.com/s/1kMhEVO0kH_Pn6wXKyqvJEA 提取码: ijxg  
资金流，板块数据(新浪): https://pan.baidu.com/s/1eusW65sdK_WE4icnt8JS1g 提取码: uux3  
市场概况，沪/深港通，融资融券数据(聚宽): https://pan.baidu.com/s/1ijrgjUd1WkRMONrwRQU-4w 提取码: dipd  

把下载的数据解压到DATA_PATH

运行主程序
```
python3 index.py
```

增量更新数据，只需要运行[recorders](./zvt/recorders)里面的脚本

## 详细文档
文档地址(两个是一样的,只是为了方便有些不方便访问github的同学)  
[http://zvt.foolcage.com](http://zvt.foolcage.com)  
[https://zvtvz.github.io/zvt](https://zvtvz.github.io/zvt)
> 目前整个框架基本稳定下来,文档还比较欠缺,需要大家的贡献.

# 💌请作者喝杯咖啡

如果你觉得项目对你有帮助,可以请作者喝杯咖啡  
<img src="./docs/imgs/alipay-cn.png" width="21.7%" alt="Alipay">　　　　　
<img src="./docs/imgs/wechat-cn.png" width="22%" alt="Wechat">

有需要股票开户可以加我朋友微信,暗号:zvt  
<img src="./docs/imgs/stock-kaihu.jpeg" width="22%" alt="Wechat">

``
# 💡 贡献

期待能有更多的开发者参与到 zvt 的开发中来，我会保证尽快 Reivew PR 并且及时回复。但提交 PR 请确保

1. 通过所有单元测试，如若是新功能，请为其新增单元测试
2. 遵守开发规范
3. 如若需要，请更新相对应的文档

也非常欢迎开发者能为 zvt 提供更多的示例，共同来完善文档，文档项目位于 [zvt/docs](https://github.com/zvtvz/zvt/docs)

# 联系方式  

QQ群:300911873  
目前没有微信群，如果有，肯定是骗子