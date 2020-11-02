# -*- coding: utf-8 -*-
import datetime
import logging
import time

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.contract.api import get_entities
from zvt.domain import Stock, Stock1dKdata, StockValuation
from zvt.factors.target_selector import TargetSelector
from zvt.factors.technical import ImprovedMaFactor
from zvt.factors.technical import SoloFactor
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=19, minute=30, day_of_week='mon-fri')
def report_solo():
    while True:
        error_count = 0
        email_action = EmailInformer()

        try:
            latest_day: Stock1dKdata = Stock1dKdata.query_data(order=Stock1dKdata.timestamp.desc(), limit=1,
                                                               return_type='domain')
            target_date = latest_day[0].timestamp

            # 计算均线
            my_selector = TargetSelector(start_timestamp='2018-10-01', end_timestamp=target_date)
            # add the factors
            factor1 = ImprovedMaFactor(start_timestamp='2018-10-01', end_timestamp=target_date)

            my_selector.add_filter_factor(factor1)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            if long_stocks:
                my_selector = TargetSelector(start_timestamp=target_date - datetime.timedelta(10),
                                             end_timestamp=target_date)
                # add the factors
                factor1 = SoloFactor(start_timestamp=target_date - datetime.timedelta(10), end_timestamp=target_date,
                                     entity_ids=long_stocks)

                my_selector.add_filter_factor(factor1)

                my_selector.run()

                long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            msg = 'no targets'

            # 过滤亏损股
            # check StockValuation data
            pe_date = target_date - datetime.timedelta(10)
            if StockValuation.query_data(start_timestamp=pe_date, limit=1, return_type='domain'):
                positive_df = StockValuation.query_data(provider='joinquant', entity_ids=long_stocks,
                                                        start_timestamp=pe_date,
                                                        filters=[StockValuation.pe > 0],
                                                        columns=['entity_id'])
                bad_stocks = set(long_stocks) - set(positive_df['entity_id'].tolist())
                if bad_stocks:
                    stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=bad_stocks,
                                          return_type='domain')
                    info = [f'{stock.name}({stock.code})' for stock in stocks]
                    msg = '亏损股:' + ' '.join(info) + '\n'

                long_stocks = set(positive_df['entity_id'].tolist())

            if long_stocks:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_stocks,
                                      return_type='domain')
                # add them to eastmoney
                try:
                    try:
                        eastmoneypy.del_group('high')
                    except:
                        pass
                    eastmoneypy.create_group('high')
                    for stock in stocks:
                        eastmoneypy.add_to_group(stock.code, group_name='high')
                except Exception as e:
                    email_action.send_message("5533061@qq.com", f'report_solo error',
                                              'report_solo error:{}'.format(e))

                info = [f'{stock.name}({stock.code})' for stock in stocks]
                msg = msg + '盈利股:' + ' '.join(info) + '\n'

            logger.info(msg)

            email_action.send_message("5533061@qq.com", f'{target_date} solo选股结果', msg)

            break
        except Exception as e:
            logger.exception('report_solo error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message("5533061@qq.com", f'report_solo error',
                                          'report_solo error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_solo.log')

    report_solo()

    sched.start()

    sched._thread.join()
