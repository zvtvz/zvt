## 安装

#### 1.clone代码

```
git clone https://github.com/zvtvz/zvt.git
```

**以下操作都在项目root目录下进行**

#### 2.环境

设置项目的virtual env(python>=3.6),安装依赖
```
pip install -r requirements.txt
```

解压data sample
```
python init_data_sample.py
```

#### 3.下载主要数据
更改DATA_PATH（否则会污染datasample,datasample只包含少量数据，用于跑测试案例）
```
# please change the path to your real store path
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
```

东财数据: https://pan.baidu.com/s/1CMAlCRYwlhGVxS6drYUEgA 提取码: q2qn  
日线数据(网易): https://pan.baidu.com/s/1kMhEVO0kH_Pn6wXKyqvJEA 提取码: ijxg  
资金流，板块数据(新浪): https://pan.baidu.com/s/1eusW65sdK_WE4icnt8JS1g 提取码: uux3  
市场概况，沪/深港通，融资融券数据(聚宽): https://pan.baidu.com/s/1ijrgjUd1WkRMONrwRQU-4w 提取码: dipd  

把下载的数据解压到DATA_PATH

>更多数据使用,请参考[数据使用](./data_usage.md)

#### ４.运行主程序

```
python3 zvt/index.py
```

在浏览器中打开:[127.0.0.1:8050](http://127.0.0.1:8050)


## 运行策略
[trader examples](https://github.com/zvtvz/zvt/tree/master/examples/trader)

设置策略使用的factor,下面例子为cross ma factor
```
class MyMaTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        myselector.add_filter_factor(
            CrossMaFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)

```
设置策略的应用标的,你可以设置任意多的标的
```
    # single stock with cross ma factor
    MyMaTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='000338_ma_trader').run()
    
    # multiple stocks with bull factor
    MyBullTrader(codes=SAMPLE_STOCK_CODES, level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                 end_timestamp='2019-06-30', trader_name='sample_stocks_bull_trader').run()
```

刷新刚才打开的运行界面,查看运行效果
<p align="center"><img src='./imgs/trader_list_view.gif'/></p>

上面为策略运行的市值曲线,下面为策略操作标的的k线图和买卖信号标记,还有策略中用到的factor.

**<span style="color:#073785">你可以看到策略中用到的factor和买卖信号,从而可以非常直观的判断策略的准确性和性能</span>**