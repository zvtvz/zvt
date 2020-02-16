# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata.api import get_entities
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import init_log
from zvt.domain import Stock, StockTradeDay
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.factors.target_selector import TargetSelector
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=18, minute=0, day_of_week='mon-fri')
def report_cross_ma():
    while True:
        error_count = 0
        email_action = EmailInformer()

        try:
            # 抓取k线数据
            # StockTradeDay.record_data(provider='joinquant')
            # Stock1dKdata.record_data(provider='joinquant')

            latest_day: StockTradeDay = StockTradeDay.query_data(order=StockTradeDay.timestamp.desc(), limit=1,
                                                                 return_type='domain')
            if latest_day:
                target_date = latest_day[0].timestamp
            else:
                target_date = now_pd_timestamp()

            # 计算均线
            my_selector = TargetSelector(start_timestamp='2018-01-01', end_timestamp=target_date)
            # add the factors
            ma_factor = CrossMaFactor(start_timestamp='2018-01-01', end_timestamp=target_date)

            my_selector.add_filter_factor(ma_factor)

            my_selector.run()

            long_targets = my_selector.get_open_long_targets(timestamp=target_date)
            if long_targets:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_targets,
                                      return_type='domain')
                info = [f'{stock.name}({stock.code})' for stock in stocks]
                msg = ' '.join(info)
            else:
                msg = 'no targets'

            logger.info(msg)

            email_action.send_message("5533061@qq.com", f'{target_date} 均线选股结果', msg)

            break
        except Exception as e:
            logger.exception('report_cross_ma error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message("5533061@qq.com", f'report_cross_ma error',
                                          'report_cross_ma error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_cross_ma.log')

    report_cross_ma()

    sched.start()

    sched._thread.join()
