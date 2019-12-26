## 1. 财报数据更新

定时任务的运行，方法很多，下面是一个参考脚本:
```
# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import *

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定时运行时间
@sched.scheduled_job('cron', hour=2, minute=00)
def run():
    while True:
        try:
            FinanceFactor.record_data()
            BalanceSheet.record_data()
            IncomeStatement.record_data()
            CashFlowStatement.record_data()
            break
        except Exception as e:
            logger.exception('finance recorder error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_finance_recorder.log')

    run()

    sched.start()

    sched._thread.join()
```

然后可将该脚本作为后台任务一直运行，ubuntu的参考命令如下:

```
nohup python examples/recorders/finance_recorder.py  >/dev/null 2>&1 &
```

## 2. 实时数据更新
行情数据的更新，有**普通**和**实时**两种模式;普通模式没有新数据就会退出，适合抓取日线以上级别的数据，实时模式会在交易时间根据周期不停抓取，适合盘中记录分钟级别数据。

下面展示一下实时行情抓取的用法。

## 2.1 比特币tick数据抓取

```
In [3]: CoinTickKdata.record_data(entity_ids=['coin_binance_BTC/USDT'],real_time=True,force_update=False)
CoinTickKdata registered recorders:[<class 'zvt.recorders.ccxt.coin_tick_recorder.CoinTickRecorder'>]
INFO  MainThread  2019-12-25 18:18:31,928  CoinTickRecorder:recorder.py:349  run  entity_id:coin_binance_BTC/USDT,evaluate_start_end_size_timestamps result:2019-12-25 18:10:33.018000,None,97,None
INFO  MainThread  2019-12-25 18:18:33,908  CoinTickRecorder:recorder.py:313  persist  persist <class 'zvt.domain.quotes.coin.coin_tick_kdata.CoinTickKdata'> for entity_id:coin_binance_BTC/USDT,time interval:[2019-12-25 18:18:04.353000,2019-12-25 18:18:33.311000]
```

打开另外一个终端，读取数据,运行下面代码：
```
# -*- coding: utf-8 -*-
import time

import pandas as pd

from zvt.domain import *
from zvt.reader import *

r = DataReader(data_schema=CoinTickKdata, provider='ccxt', level='tick')


class CoinTickListener(DataListener):

    def on_data_loaded(self, data: pd.DataFrame) -> object:
        print(data)

    def on_data_changed(self, data: pd.DataFrame) -> object:
        pass

    def on_entity_data_changed(self, entity: str, added_data: pd.DataFrame) -> object:
        print(added_data)


r.register_data_listener(CoinTickListener())

while True:
    r.move_on()
    time.sleep(2)
```

数据刷新如下:
```
entity_id             timestamp
coin_binance_BTC/USDT 2019-12-26 17:07:04.714      coin_binance_BTC/USDT_2019-12-26T17:07:04.714  coin_binance_BTC/USDT 2019-12-26 17:07:04.714     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.030994   224.095918       buy       None
                      2019-12-26 17:07:04.714  coin_binance_BTC/USDT_2019-12-26T17:07:04.714_...  coin_binance_BTC/USDT 2019-12-26 17:07:04.714     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.369006  2668.027772       buy       None
                      2019-12-26 17:07:05.015      coin_binance_BTC/USDT_2019-12-26T17:07:05.015  coin_binance_BTC/USDT 2019-12-26 17:07:05.015     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.017069   123.413991       buy       None
                      2019-12-26 17:07:05.015  coin_binance_BTC/USDT_2019-12-26T17:07:05.015_...  coin_binance_BTC/USDT 2019-12-26 17:07:05.015     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.043217   312.472307       buy       None
                      2019-12-26 17:07:05.305      coin_binance_BTC/USDT_2019-12-26T17:07:05.305  coin_binance_BTC/USDT 2019-12-26 17:07:05.305     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.017069   123.413991       buy       None
                      2019-12-26 17:07:05.305  coin_binance_BTC/USDT_2019-12-26T17:07:05.305_...  coin_binance_BTC/USDT 2019-12-26 17:07:05.305     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.043023   311.069627       buy       None
                      2019-12-26 17:07:05.599      coin_binance_BTC/USDT_2019-12-26T17:07:05.599  coin_binance_BTC/USDT 2019-12-26 17:07:05.599     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.060222   435.423729       buy       None
                      2019-12-26 17:07:06.463      coin_binance_BTC/USDT_2019-12-26T17:07:06.463  coin_binance_BTC/USDT 2019-12-26 17:07:06.463     ccxt  BTC/USDT  BTC/USDT  tick  None  7229.97  0.049591   358.541442      sell       None
                      2019-12-26 17:07:06.741      coin_binance_BTC/USDT_2019-12-26T17:07:06.741  coin_binance_BTC/USDT 2019-12-26 17:07:06.741     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.06  0.259461  1875.918598      sell       None
                      2019-12-26 17:07:08.646      coin_binance_BTC/USDT_2019-12-26T17:07:08.646  coin_binance_BTC/USDT 2019-12-26 17:07:08.646     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.040835   295.249301       buy       None
                      2019-12-26 17:07:10.219      coin_binance_BTC/USDT_2019-12-26T17:07:10.219  coin_binance_BTC/USDT 2019-12-26 17:07:10.219     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.001565    11.315420       buy       None
                      2019-12-26 17:07:11.075      coin_binance_BTC/USDT_2019-12-26T17:07:11.075  coin_binance_BTC/USDT 2019-12-26 17:07:11.075     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.19  0.259707  1877.730954       buy       None
                      2019-12-26 17:07:11.084      coin_binance_BTC/USDT_2019-12-26T17:07:11.084  coin_binance_BTC/USDT 2019-12-26 17:07:11.084     ccxt  BTC/USDT  BTC/USDT  tick  None  7229.99  0.190700  1378.759093      sell       None
                      2019-12-26 17:07:11.785      coin_binance_BTC/USDT_2019-12-26T17:07:11.785  coin_binance_BTC/USDT 2019-12-26 17:07:11.785     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.29  0.400000  2892.116000       buy       None
                      2019-12-26 17:07:12.084      coin_binance_BTC/USDT_2019-12-26T17:07:12.084  coin_binance_BTC/USDT 2019-12-26 17:07:12.084     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.060239   435.546042       buy       None
                                                                                              id              entity_id               timestamp provider      code      name level order    price    volume     turnover direction order_type
entity_id             timestamp
coin_binance_BTC/USDT 2019-12-26 17:07:04.714      coin_binance_BTC/USDT_2019-12-26T17:07:04.714  coin_binance_BTC/USDT 2019-12-26 17:07:04.714     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.030994   224.095918       buy       None
                      2019-12-26 17:07:04.714  coin_binance_BTC/USDT_2019-12-26T17:07:04.714_...  coin_binance_BTC/USDT 2019-12-26 17:07:04.714     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.369006  2668.027772       buy       None
                      2019-12-26 17:07:05.015      coin_binance_BTC/USDT_2019-12-26T17:07:05.015  coin_binance_BTC/USDT 2019-12-26 17:07:05.015     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.017069   123.413991       buy       None
                      2019-12-26 17:07:05.015  coin_binance_BTC/USDT_2019-12-26T17:07:05.015_...  coin_binance_BTC/USDT 2019-12-26 17:07:05.015     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.043217   312.472307       buy       None
                      2019-12-26 17:07:05.305      coin_binance_BTC/USDT_2019-12-26T17:07:05.305  coin_binance_BTC/USDT 2019-12-26 17:07:05.305     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.017069   123.413991       buy       None
                      2019-12-26 17:07:05.305  coin_binance_BTC/USDT_2019-12-26T17:07:05.305_...  coin_binance_BTC/USDT 2019-12-26 17:07:05.305     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.043023   311.069627       buy       None
                      2019-12-26 17:07:05.599      coin_binance_BTC/USDT_2019-12-26T17:07:05.599  coin_binance_BTC/USDT 2019-12-26 17:07:05.599     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.31  0.060222   435.423729       buy       None
                      2019-12-26 17:07:06.463      coin_binance_BTC/USDT_2019-12-26T17:07:06.463  coin_binance_BTC/USDT 2019-12-26 17:07:06.463     ccxt  BTC/USDT  BTC/USDT  tick  None  7229.97  0.049591   358.541442      sell       None
                      2019-12-26 17:07:06.741      coin_binance_BTC/USDT_2019-12-26T17:07:06.741  coin_binance_BTC/USDT 2019-12-26 17:07:06.741     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.06  0.259461  1875.918598      sell       None
                      2019-12-26 17:07:08.646      coin_binance_BTC/USDT_2019-12-26T17:07:08.646  coin_binance_BTC/USDT 2019-12-26 17:07:08.646     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.040835   295.249301       buy       None
                      2019-12-26 17:07:10.219      coin_binance_BTC/USDT_2019-12-26T17:07:10.219  coin_binance_BTC/USDT 2019-12-26 17:07:10.219     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.001565    11.315420       buy       None
                      2019-12-26 17:07:11.075      coin_binance_BTC/USDT_2019-12-26T17:07:11.075  coin_binance_BTC/USDT 2019-12-26 17:07:11.075     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.19  0.259707  1877.730954       buy       None
                      2019-12-26 17:07:11.084      coin_binance_BTC/USDT_2019-12-26T17:07:11.084  coin_binance_BTC/USDT 2019-12-26 17:07:11.084     ccxt  BTC/USDT  BTC/USDT  tick  None  7229.99  0.190700  1378.759093      sell       None
                      2019-12-26 17:07:11.785      coin_binance_BTC/USDT_2019-12-26T17:07:11.785  coin_binance_BTC/USDT 2019-12-26 17:07:11.785     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.29  0.400000  2892.116000       buy       None
                      2019-12-26 17:07:12.084      coin_binance_BTC/USDT_2019-12-26T17:07:12.084  coin_binance_BTC/USDT 2019-12-26 17:07:12.084     ccxt  BTC/USDT  BTC/USDT  tick  None  7230.30  0.060239   435.546042       buy       None
```
