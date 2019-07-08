## 1. data structure
concepts

### 1.1 provider

which means data source provider,e.g joinquant,eastmoney,sina,netease,ccxt

### 1.2 store category

logical classification of data,represents one db file physically which storing data schema with relations

### 1.3 data schema

the data schema for the db table

#### *logic view* ####
<p align="center"><img src='./imgs/data_structure.png'/></p>

#### *physical view* ####
<p align="center"><img src='./imgs/data_structure_physics.png'/></p>

> generally speaking,the data schema is stable.Some data would be generated from several provider the main provider would be treated as the provider.
When the data has multiple providers, you could verify each other by specifying the different providers on the api.


## 2. Principle of recorder

To make the data provided by each provider (or crawl it yourself) into  data that conforms to the data schema, you need to do the following:

* Initialize the target to be crawled
Can grab a single target to debug, and then grab the full amount of the targets

* Ability to grab from the last crawled place
Reduce unnecessary requests, incremental crawling

* Encapsulate commonly used request methods
For the request of time series data, we abstract them to: start, end, size, time list

* Ability to automatically handle duplicate

* Ability to set the crawl rate

* Provide callback functions for the completion of the fetching
Convenient data verification and multi-provider data completion

The flow chart is as follows:

<p align="center"><img src='./imgs/recorder.png'/></p>

check the details at[*recorder*](https://github.com/zvtvz/zvt/blob/master/zvt/recorders/recorder.py). Part of the project's recorder implementation is provided directly in current project, with some closed source, only the final database file (which will be published in the dropbox and qq group).

The entire eastmoney recorder is based on the basic recorder class. Basically, a type of data is processed in about 10 lines of code; mastering the method, I believe that everyone can easily write other recorders.


## 3. how to add provder

Here is an example of joinquant


### 2.1 add joinquant provider ###

[*code*](https://github.com/zvtvz/zvt/blob/master/zvt/domain/common.py#L54) 

```
class Provider(enum.Enum):
    # add
    JOINQUANT = 'joinquant'
```

### 2.2 add store category ###
[*code*](https://github.com/zvtvz/zvt/blob/master/zvt/domain/common.py#L59)  

```
class StoreCategory(enum.Enum):
    meta = 'meta'
    stock_1m_kdata = 'stock_1m_kdata'
    stock_5m_kdata = 'stock_5m_kdata'
    stock_15m_kdata = 'stock_15m_kdata'
    stock_1h_kdata = 'stock_1h_kdata'
    stock_1d_kdata = 'stock_1d_kdata'
    stock_1wk_kdata = 'stock_1wk_kdata'

    etf_1d_kdata = 'etf_1d_kdata'
    index_1d_kdata = 'index_1d_kdata'

    finance = 'finance'
    dividend_financing = 'dividend_financing'
    holder = 'holder'
    trading = 'trading'
    money_flow = 'money_flow'
    macro = 'macro'
    business = 'business'

    coin_meta = 'coin_meta'
    coin_tick_kdata = 'coin_tick_kdata'
    coin_1m_kdata = 'coin_1m_kdata'
    coin_5m_kdata = 'coin_5m_kdata'
    coin_15m_kdata = 'coin_15m_kdata'
    coin_1h_kdata = 'coin_1h_kdata'
    coin_1d_kdata = 'coin_1d_kdata'
    coin_1wk_kdata = 'coin_1wk_kdata'
```

### 2.3 set store category the provider providing###
```

provider_map_category = {
    Provider.EASTMONEY: [StoreCategory.meta,
                         StoreCategory.finance,
                         StoreCategory.dividend_financing,
                         StoreCategory.holder,
                         StoreCategory.trading],

    Provider.SINA: [StoreCategory.meta,
                    StoreCategory.etf_1d_kdata,
                    StoreCategory.stock_1d_kdata,
                    StoreCategory.money_flow],

    Provider.NETEASE: [StoreCategory.stock_1d_kdata,
                       StoreCategory.index_1d_kdata],

    Provider.EXCHANGE: [StoreCategory.meta, StoreCategory.macro],

    Provider.ZVT: [StoreCategory.business],

    # TODO:would add other data from joinquant
    Provider.JOINQUANT: [StoreCategory.stock_1m_kdata,
                         StoreCategory.stock_5m_kdata,
                         StoreCategory.stock_15m_kdata,
                         StoreCategory.stock_1h_kdata,
                         StoreCategory.stock_1d_kdata,
                         StoreCategory.stock_1wk_kdata, ],

    Provider.CCXT: [StoreCategory.coin_meta,
                    StoreCategory.coin_tick_kdata,
                    StoreCategory.coin_1m_kdata,
                    StoreCategory.coin_5m_kdata,
                    StoreCategory.coin_15m_kdata,
                    StoreCategory.coin_1h_kdata,
                    StoreCategory.coin_1d_kdata,
                    StoreCategory.coin_1wk_kdata],
}

```
### 2.4 define data schema ###
[*代码*](https://github.com/zvtvz/zvt/blob/master/zvt/domain/quote.py#L9)  

stock market data structure

```
class StockKdataCommon(object):
    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # level = Column(Enum(TradingLevel, values_callable=enum_value))
    level = Column(String(length=32))

    open = Column(Float)
    hfq_open = Column(Float)
    qfq_open = Column(Float)
    close = Column(Float)
    hfq_close = Column(Float)
    qfq_close = Column(Float)
    high = Column(Float)
    hfq_high = Column(Float)
    qfq_high = Column(Float)
    low = Column(Float)
    hfq_low = Column(Float)
    qfq_low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)
    factor = Column(Float)

class Stock1DKdata(Stock1DKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1d_kdata'
```


### 2.5 implement the recorder

[*代码*](https://github.com/zvtvz/zvt/blob/master/zvt/recorders/joinquant/quotes/jq_china_stock__kdata_recorder.py)  

core code

```
#Convert joinquant data to standard zvt data

class MyApiWrapper(ApiWrapper):
    def request(self, url=None, method='get', param=None, path_fields=None):
        security_item = param['security_item']
        start_timestamp = param['start_timestamp']
        end_timestamp = param['end_timestamp']
        # 不复权
        df = get_price(to_jq_security_id(security_item), start_date=to_time_str(start_timestamp),
                       end_date=end_timestamp,
                       frequency=param['jq_level'],
                       fields=['open', 'close', 'low', 'high', 'volume', 'money'],
                       skip_paused=True, fq=None)
        df.index.name = 'timestamp'
        df.reset_index(inplace=True)
        df['name'] = security_item.name
        df.rename(columns={'money': 'turnover'}, inplace=True)

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['provider'] = Provider.JOINQUANT.value
        df['level'] = param['level']

        # remove the unfinished kdata
        if is_in_trading(security_type='stock', exchange='sh', timestamp=df.iloc[-1, :]['timestamp']):
            df = df.iloc[:-1, :]

        return df.to_dict(orient='records')

#Completion of re-weighting data
def on_finish(self, security_item):
    kdatas = get_kdata(security_id=security_item.id, level=self.level.value, order=StockDayKdata.timestamp.asc(),
                       return_type='domain',
                       session=self.session,
                       filters=[StockDayKdata.hfq_close.is_(None),
                                StockDayKdata.timestamp >= to_pd_timestamp('2005-01-01')])
    if kdatas:
        start = kdatas[0].timestamp
        end = kdatas[-1].timestamp

        # get hfq from joinquant
        df = get_price(to_jq_security_id(security_item), start_date=to_time_str(start), end_date=now_time_str(),
                       frequency='daily',
                       fields=['factor', 'open', 'close', 'low', 'high'],
                       skip_paused=True, fq='post')
        if df is not None and not df.empty:
            # fill hfq data
            for kdata in kdatas:
                if kdata.timestamp in df.index:
                    kdata.hfq_open = df.loc[kdata.timestamp, 'open']
                    kdata.hfq_close = df.loc[kdata.timestamp, 'close']
                    kdata.hfq_high = df.loc[kdata.timestamp, 'high']
                    kdata.hfq_low = df.loc[kdata.timestamp, 'low']
                    kdata.factor = df.loc[kdata.timestamp, 'factor']
            self.session.commit()

            latest_factor = df.factor[-1]
            # factor not change yet, no need to reset the qfq past
            if latest_factor == self.current_factors.get(security_item.id):
                sql = 'UPDATE stock_day_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                      'security_id=\'{}\' and level=\'{}\' and (qfq_close isnull or qfq_high isnull or qfq_low isnull or qfq_open isnull)'.format(
                    latest_factor, latest_factor, latest_factor, latest_factor, security_item.id, self.level.value)
            else:
                sql = 'UPDATE stock_day_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                      'security_id=\'{}\' and level=\'{}\''.format(latest_factor,
                                                                   latest_factor,
                                                                   latest_factor,
                                                                   latest_factor,
                                                                   security_item.id,
                                                                   self.level.value)
            self.logger.info(sql)
            self.session.execute(sql)
            self.session.commit()

    # TODO:use netease provider to get turnover_rate
    self.logger.info('use netease provider to get turnover_rate')
```

There is an exercise left here. Since the data of the joinquant does not provide the turnover rate and changing percentage, it can be completed by other data sources or by calculation.

Netease's data has no re-rights factor information, and it is complemented by a joinquant re-rights factor. Similarly, Netease's turnover rate and  changing percentage can be used to complement the joinquant data.

[*参考代码*](https://github.com/zvtvz/zvt/blob/master/zvt/recorders/netease/china_stock_day_kdata_recorder.py)

### 2.6 runt the recorder

set your joinquant JQ_ACCOUNT/JQ_PASSWD[settings](https://github.com/zvtvz/zvt/blob/master/zvt/settings.py)

>Jqdata is currently free for one year, the registered address is as follows:
>https://www.joinquant.com/default/index/sdk?channelId=953cbf5d1b8683f81f0c40c9d4265c0d  
>if you need to increase the amount of free usage,please contact me

```
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in TradingLevel])
    parser.add_argument('--codes', help='codes', default=SAMPLE_STOCK_CODES, nargs='+')

    args = parser.parse_args()

    level = TradingLevel(args.level)
    codes = args.codes

    init_process_log('jq_china_stock_{}_kdata.log'.format(args.level))
    JQChinaStockKdataRecorder(level=level, sleeping_time=0, codes=codes).run()
```

the level means different time intervals of the kdata,codes means the stock codes and if you dont' set it,the recorder would get full china market data.

# 3. automatically acquired ability

after you add the provider,you could use api,factor,selector,trader,visualization of the zvt basing the data

```
In [1]: from zvt.api.technical import * 
In [2]: from zvt.api.domain import * 
In [3]: df1=get_kdata(security_id='stock_sz_300027', provider='joinquant',start_timestamp='2019-01-01',limit=10)
In [4]: df1                                                                     
                           id   provider  timestamp      security_id    code  name level  open  hfq_open  qfq_open  close  hfq_close  qfq_close  high  hfq_high  qfq_high   low  hfq_low   qfq_low      volume      turnover change_pct turnover_rate  factor
0  stock_sz_300027_2019-01-02  joinquant 2019-01-02  stock_sz_300027  300027  华谊兄弟    1d  4.54     68.58  4.539918   4.40      66.47   4.400238  4.58     69.19  4.580299  4.35    65.71  4.349927  29554330.0  1.306117e+08       None          None  15.106
1  stock_sz_300027_2019-01-03  joinquant 2019-01-03  stock_sz_300027  300027  华谊兄弟    1d  4.40     66.47  4.400238   4.42      66.77   4.420098  4.45     67.22  4.449887  4.36    65.86  4.359857  15981569.0  7.052363e+07       None          None  15.106
2  stock_sz_300027_2019-01-04  joinquant 2019-01-04  stock_sz_300027  300027  华谊兄弟    1d  4.36     65.86  4.359857   4.52      68.28   4.520058  4.54     68.58  4.539918  4.33    65.41  4.330068  17103081.0  7.657399e+07       None          None  15.106
3  stock_sz_300027_2019-01-07  joinquant 2019-01-07  stock_sz_300027  300027  华谊兄弟    1d  4.54     68.58  4.539918   4.59      69.34   4.590229  4.63     69.94  4.629948  4.48    67.67  4.479677  16163938.0  7.383168e+07       None          None  15.106
4  stock_sz_300027_2019-01-08  joinquant 2019-01-08  stock_sz_300027  300027  华谊兄弟    1d  4.59     69.34  4.590229   4.60      69.49   4.600159  4.66     70.39  4.659738  4.56    68.88  4.559778  10908603.0  5.034655e+07       None          None  15.106
5  stock_sz_300027_2019-01-09  joinquant 2019-01-09  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.58      69.19   4.580299  4.73     71.45  4.729909  4.58    69.19  4.580299  16901976.0  7.881876e+07       None          None  15.106
6  stock_sz_300027_2019-01-10  joinquant 2019-01-10  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.61      69.64   4.610089  4.76     71.90  4.759698  4.59    69.34  4.590229  20855469.0  9.717176e+07       None          None  15.106
7  stock_sz_300027_2019-01-11  joinquant 2019-01-11  stock_sz_300027  300027  华谊兄弟    1d  4.60     69.49  4.600159   4.67      70.55   4.670330  4.67     70.55  4.670330  4.56    68.88  4.559778  13216260.0  6.089670e+07       None          None  15.106
8  stock_sz_300027_2019-01-14  joinquant 2019-01-14  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.57      69.03   4.569707  4.65     70.24  4.649808  4.55    68.73  4.549848  12421993.0  5.705187e+07       None          None  15.106
9  stock_sz_300027_2019-01-15  joinquant 2019-01-15  stock_sz_300027  300027  华谊兄弟    1d  4.56     68.88  4.559778   4.64      70.09   4.639878  4.66     70.39  4.659738  4.54    68.58  4.539918  14403671.0  6.637258e+07       None          None  15.106


#compare with netease data
In [24]: df2=get_kdata(security_id='stock_sz_300027', provider='netease',start_timestamp='2019-01-01',limit=10)                                                                          

In [25]: df2                                                                                                                                                                             
Out[25]: 
                           id provider  timestamp      security_id    code  name level  open  hfq_open  qfq_open  close  hfq_close  qfq_close  high  hfq_high  qfq_high   low  hfq_low   qfq_low      volume      turnover  change_pct  turnover_rate  factor
0  stock_sz_300027_2019-01-02  netease 2019-01-02  stock_sz_300027  300027  华谊兄弟    1d  4.54     68.58  4.539918   4.40      66.47   4.400238  4.58     69.19  4.580299  4.35    65.71  4.349927  29554330.0  1.306117e+08     -6.1834         1.0652  15.106
1  stock_sz_300027_2019-01-03  netease 2019-01-03  stock_sz_300027  300027  华谊兄弟    1d  4.40     66.47  4.400238   4.42      66.77   4.420098  4.45     67.22  4.449887  4.36    65.86  4.359857  15981569.0  7.052363e+07      0.4545         0.5760  15.106
2  stock_sz_300027_2019-01-04  netease 2019-01-04  stock_sz_300027  300027  华谊兄弟    1d  4.36     65.86  4.359857   4.52      68.28   4.520058  4.54     68.58  4.539918  4.33    65.41  4.330068  17103081.0  7.657399e+07      2.2624         0.6164  15.106
3  stock_sz_300027_2019-01-07  netease 2019-01-07  stock_sz_300027  300027  华谊兄弟    1d  4.54     68.58  4.539918   4.59      69.34   4.590229  4.63     69.94  4.629948  4.48    67.67  4.479677  16163938.0  7.383168e+07      1.5487         0.5826  15.106
4  stock_sz_300027_2019-01-08  netease 2019-01-08  stock_sz_300027  300027  华谊兄弟    1d  4.59     69.34  4.590229   4.60      69.49   4.600159  4.66     70.39  4.659738  4.56    68.88  4.559778  10908603.0  5.034655e+07      0.2179         0.3932  15.106
5  stock_sz_300027_2019-01-09  netease 2019-01-09  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.58      69.19   4.580299  4.73     71.45  4.729909  4.58    69.19  4.580299  16901976.0  7.881876e+07     -0.4348         0.6092  15.106
6  stock_sz_300027_2019-01-10  netease 2019-01-10  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.61      69.64   4.610089  4.76     71.90  4.759698  4.59    69.34  4.590229  20855469.0  9.717176e+07      0.6550         0.7517  15.106
7  stock_sz_300027_2019-01-11  netease 2019-01-11  stock_sz_300027  300027  华谊兄弟    1d  4.60     69.49  4.600159   4.67      70.55   4.670330  4.67     70.55  4.670330  4.56    68.88  4.559778  13216260.0  6.089670e+07      1.3015         0.4763  15.106
8  stock_sz_300027_2019-01-14  netease 2019-01-14  stock_sz_300027  300027  华谊兄弟    1d  4.63     69.94  4.629948   4.57      69.03   4.569707  4.65     70.24  4.649808  4.55    68.73  4.549848  12421993.0  5.705187e+07     -2.1413         0.4477  15.106
9  stock_sz_300027_2019-01-15  netease 2019-01-15  stock_sz_300027  300027  华谊兄弟    1d  4.56     68.88  4.559778   4.64      70.09   4.639878  4.66     70.39  4.659738  4.54    68.58  4.539918  14403671.0  6.637258e+07      1.5317         0.5191  15.106

```
the result
```
In [26]: df1.loc[:,['open','close','high','low','volume']]-df2.loc[:,['open','close','high','low','volume']]                                                                             
Out[26]: 
   open  close  high  low  volume
0   0.0    0.0   0.0  0.0     0.0
1   0.0    0.0   0.0  0.0     0.0
2   0.0    0.0   0.0  0.0     0.0
3   0.0    0.0   0.0  0.0     0.0
4   0.0    0.0   0.0  0.0     0.0
5   0.0    0.0   0.0  0.0     0.0
6   0.0    0.0   0.0  0.0     0.0
7   0.0    0.0   0.0  0.0     0.0
8   0.0    0.0   0.0  0.0     0.0
9   0.0    0.0   0.0  0.0     0.0
```

Well, the data of the two companies are consistent, and the accuracy of the data is further confirmed.