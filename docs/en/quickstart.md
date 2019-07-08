## install

> Since the project can be customized and expanded in many cases, the pip installing is only suitable for demonstration, please clone the code directly and refer to related documents.

```
pip install zvt
```
upgrade
```
pip install -U zvt
```

clone the code(**recommended way**)

```
git clone https://github.com/zvtvz/zvt.git
```
**assume that you operate in the project root directory**
****

## setup env

- python>=3.6(recommended using virtualenv)

- install requirements
```
pip install -r requirements.txt
```

**assume the env is ready** 

## init sample data
```
python init_data_sample.py
```

The script decompresses the data sample which the tests and examples in the project depend on.

please change the DATA_PATH,if you're using the full data coming from the recorders

```
# please change the path to your real store path
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasample'))

```


for how to use and extend the data, please refer to [data usage](./data_usage.md)

## run the main interface
```
python main.py
```
you could run zvt/main.py in pycharm directly


open your browser:[127.0.0.1:8050](http://127.0.0.1:8050)

## run the strategies
[trader examples](https://github.com/zvtvz/zvt/tree/master/examples/trader)

set the factors for your trader,e.g,cross ma
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

set the targets as many as you want
```
    # single stock with cross ma factor
    MyMaTrader(codes=['000338'], level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='000338_ma_trader').run()
    
    # multiple stocks with bull factor
    MyBullTrader(codes=SAMPLE_STOCK_CODES, level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                 end_timestamp='2019-06-30', trader_name='sample_stocks_bull_trader').run()
```


open the running interface from the browser,check the results
<p align="center"><img src='./imgs/trader_list_view.gif'/></p>

The above is the market value curve of the strategy. The following is the k-line diagram of the targetS and trading signal mark, as well as the factor used in the strategy.

**<span style="color:#073785">You can see the factor and trading signals used in the strategy, so you can judge the accuracy and performance of the strategy very intuitively.</span>**