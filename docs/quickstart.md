## 安装

```
pip install zvt
```
如果安装过
```
pip install -U zvt
```
如果想直接撸源码(推荐方式)
```
git clone https://github.com/zvtvz/zvt.git
```
## 运行主界面
假设你在项目root目录下
```
python main.py
```
也可pycharm中直接运行zvt/main.py

> 在命令行下直接python main.py这种方式,默认会把main.py所在的目录放到PYTHONPATH下,而如果main.py是在zvt目录下,zvt package的加载是有问题的,所以在zvt的外层放了一个main.py

在浏览器中打开:[127.0.0.1:8050](http://127.0.0.1:8050)

## 运行策略
[trader examples](https://github.com/zvtvz/zvt/tree/master/examples/trader)

设置策略使用的factor,下面例子为cross ma factor
```
class MyMaTrader(StockTrader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        myselector.add_filter_factor(
            CrossMaFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)

```
设置策略的应用标的,你可以设置任意多的标的
```
    # single stock with cross ma factor
    MyMaTrader(codes=['000338'], level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='000338_ma_trader').run()
    
    # multiple stocks with bull factor
    MyBullTrader(codes=SAMPLE_STOCK_CODES, level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                 end_timestamp='2019-06-30', trader_name='sample_stocks_bull_trader').run()
```

刷新刚才打开的运行界面,查看运行效果
<p align="center"><img src='trader_list_view.gif'/></p>

上面为策略运行的市值曲线,下面为策略操作标的的k线图和买卖信号标记,还有策略中用到的factor.

**<span style="color:#073785">你可以看到策略中用到的factor和买卖信号,从而可以非常直观的判断策略的准确性和性能</span>**