# -*- coding: utf-8 -*-
import logging
import time

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from examples.factors.fundamental_selector import FundamentalSelector
from examples.reports import get_subscriber_emails
from zvt.contract.api import get_entities
from zvt.utils.time_utils import now_pd_timestamp, to_time_str
from zvt import init_log
from zvt.domain import Stock
from zvt.factors.target_selector import TargetSelector
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 基本面选股 每周一次即可 基本无变化
@sched.scheduled_job('cron', hour=16, minute=0, day_of_week='6')
def report_core_company():
    while True:
        error_count = 0
        email_action = EmailInformer()

        try:
            # StockTradeDay.record_data(provider='joinquant')
            # Stock.record_data(provider='joinquant')
            # FinanceFactor.record_data(provider='eastmoney')
            # BalanceSheet.record_data(provider='eastmoney')

            target_date = to_time_str(now_pd_timestamp())

            my_selector: TargetSelector = FundamentalSelector(start_timestamp='2015-01-01', end_timestamp=target_date)
            my_selector.run()

            long_targets = my_selector.get_open_long_targets(timestamp=target_date)
            if long_targets:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_targets,
                                      return_type='domain')

                # add them to eastmoney
                try:
                    try:
                        eastmoneypy.del_group('core')
                    except:
                        pass
                    eastmoneypy.create_group('core')
                    for stock in stocks:
                        eastmoneypy.add_to_group(stock.code, group_name='core')
                except Exception as e:
                    email_action.send_message("5533061@qq.com", f'report_core_company error',
                                              'report_core_company error:{}'.format(e))

                info = [f'{stock.name}({stock.code})' for stock in stocks]
                msg = ' '.join(info)
            else:
                msg = 'no targets'

            logger.info(msg)

            email_action.send_message(get_subscriber_emails(), f'{to_time_str(target_date)} 核心资产选股结果', msg)
            break
        except Exception as e:
            logger.exception('report_core_company error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message("5533061@qq.com", f'report_core_company error',
                                          'report_core_company error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_core_company.log')

    report_core_company()

    sched.start()

    sched._thread.join()
