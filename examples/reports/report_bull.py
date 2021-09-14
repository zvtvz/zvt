# -*- coding: utf-8 -*-
import logging
import time

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from examples.reports import stocks_with_info
from zvt import init_log, zvt_config
from zvt.contract.api import get_entities
from zvt.domain import Stock, Stock1dHfqKdata
from zvt.factors import BullFactor, CrossMaVolumeFactor
from zvt.factors.target_selector import TargetSelector
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=18, minute=10, day_of_week='mon-fri')
def report_bull():
    while True:
        error_count = 0
        email_action = EmailInformer()

        try:
            latest_day: Stock1dHfqKdata = Stock1dHfqKdata.query_data(order=Stock1dHfqKdata.timestamp.desc(), limit=1,
                                                                     return_type='domain')
            target_date = latest_day[0].timestamp

            # 计算均线
            start = '2019-01-01'
            my_selector = TargetSelector(start_timestamp=start, end_timestamp=target_date)
            # add the factors
            factor1 = BullFactor(start_timestamp=start, end_timestamp=target_date)
            factor2 = CrossMaVolumeFactor(start_timestamp=start, end_timestamp=target_date,
                                          windows=[5, 120, 250])

            my_selector.add_filter_factor(factor1)
            my_selector.add_filter_factor(factor2)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            msg = 'no targets'

            if long_stocks:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_stocks,
                                      return_type='domain')
                # add them to eastmoney
                try:
                    try:
                        eastmoneypy.del_group('bull')
                    except:
                        pass
                    eastmoneypy.create_group('bull')
                    for stock in stocks:
                        eastmoneypy.add_to_group(stock.code, group_name='bull')
                except Exception as e:
                    email_action.send_message(zvt_config['email_username'], f'report_bull error',
                                              'report_bull error:{}'.format(e))

                infos = stocks_with_info(stocks)
                msg = '\n'.join(infos) + '\n'

            logger.info(msg)

            email_action.send_message(zvt_config['email_username'], f'{target_date} bull选股结果', msg)

            break
        except Exception as e:
            logger.exception('report_bull error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message(zvt_config['email_username'], f'report_bull error',
                                          'report_bull error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_bull.log')

    report_bull()

    sched.start()

    sched._thread.join()
