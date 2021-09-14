# -*- coding: utf-8 -*-
import logging
import time

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from examples.reports import get_subscriber_emails, stocks_with_info
from zvt import init_log, zvt_config
from zvt.contract.api import get_entities
from zvt.domain import Stock, Stock1dHfqKdata
from zvt.factors import VolumeUpMaFactor
from zvt.factors.target_selector import TargetSelector, SelectMode
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=19, minute=0, day_of_week='mon-fri')
def report_vol_up():
    while True:
        error_count = 0
        email_action = EmailInformer()

        try:
            # 抓取k线数据
            # StockTradeDay.record_data(provider='joinquant')
            # Stock1dKdata.record_data(provider='joinquant')

            latest_day: Stock1dHfqKdata = Stock1dHfqKdata.query_data(order=Stock1dHfqKdata.timestamp.desc(), limit=1,
                                                                     return_type='domain')
            target_date = latest_day[0].timestamp

            # 计算均线
            start = '2019-01-01'
            my_selector = TargetSelector(start_timestamp=start, end_timestamp=target_date,
                                         select_mode=SelectMode.condition_or)
            # add the factors
            factor1 = VolumeUpMaFactor(start_timestamp=start, end_timestamp=target_date, windows=[120, 250],
                                       over_mode='or')

            my_selector.add_filter_factor(factor1)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            msg = 'no targets'

            if long_stocks:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_stocks,
                                      return_type='domain')
                # add them to eastmoney
                try:
                    try:
                        eastmoneypy.del_group('tech')
                    except:
                        pass
                    eastmoneypy.create_group('tech')
                    for stock in stocks:
                        eastmoneypy.add_to_group(stock.code, group_name='tech')
                except Exception as e:
                    email_action.send_message(zvt_config['email_username'], f'report_vol_up error',
                                              'report_vol_up error:{}'.format(e))

                infos = stocks_with_info(stocks)
                msg = '\n'.join(infos) + '\n'

            logger.info(msg)

            email_action.send_message(get_subscriber_emails(), f'{target_date} 改进版放量突破(半)年线选股结果', msg)

            break
        except Exception as e:
            logger.exception('report_vol_up error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message(zvt_config['email_username'], f'report_vol_up error',
                                          'report_vol_up error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_vol_up.log')

    report_vol_up()

    sched.start()

    sched._thread.join()
