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

打开另外一个终端，读取数据
```

```

