# -*- coding: utf-8 -*-
import datetime
import logging
import time

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from examples.reports import risky_company
from zvt import init_log
from zvt.contract.api import get_entities, get_entity_code
from zvt.domain import Stock1dKdata, Stock
from zvt.factors import TargetSelector
from zvt.factors.ma.ma_factor import ImprovedMaFactor
from zvt.factors.ma.ma_stats import MaStateStatsFactor
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=19, minute=30, day_of_week='mon-fri')
def report_state():
    while True:
        error_count = 0
        email_action = EmailInformer(ssl=True)

        try:
            latest_day: Stock1dKdata = Stock1dKdata.query_data(order=Stock1dKdata.timestamp.desc(), limit=1,
                                                               return_type='domain')
            target_date = latest_day[0].timestamp
            # target_date = to_pd_timestamp('2020-01-02')

            # 计算均线
            my_selector = TargetSelector(start_timestamp='2018-01-01', end_timestamp=target_date)
            # add the factors
            factor1 = ImprovedMaFactor(start_timestamp='2018-01-01', end_timestamp=target_date)

            my_selector.add_filter_factor(factor1)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)
            stock_map_slope = {}

            logger.info(long_stocks)

            msg = 'no targets'

            if long_stocks:
                pre_date = target_date - datetime.timedelta(2 * 365)
                ma_state = MaStateStatsFactor(entity_ids=long_stocks, start_timestamp=pre_date,
                                              end_timestamp=target_date, need_persist=False)

                ma_state.factor_df['slope'] = 100 * ma_state.factor_df['current_pct'] / ma_state.factor_df[
                    'current_count']

                high_stocks = []
                for entity_id, df in ma_state.factor_df.groupby(level=0):
                    if df['current_pct'].max() >= 0.7:
                        high_stocks.append(entity_id)

                    stock_map_slope[entity_id] = round(df['slope'].iat[-1], 2)

                if high_stocks:
                    stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=high_stocks,
                                          return_type='domain')
                    info = [f'{stock.name}({stock.code})[{stock_map_slope.get(stock.entity_id)}]' for stock in stocks]
                    msg = msg + '2年内高潮过:' + ' '.join(info) + '\n'

            # 过滤风险股
            if long_stocks:
                risky_codes = risky_company(the_date=target_date, entity_ids=long_stocks, income_yoy=-0.8,
                                            profit_yoy=-0.8)

                if risky_codes:
                    long_stocks = [entity_id for entity_id in long_stocks if
                                   get_entity_code(entity_id) not in risky_codes]

                    stocks = get_entities(provider='joinquant', entity_schema=Stock, codes=risky_codes,
                                          return_type='domain')
                    info = [f'{stock.name}({stock.code})[{stock_map_slope.get(stock.entity_id)}]' for stock in stocks]
                    msg = msg + '风险股:' + ' '.join(info) + '\n'
            if long_stocks:
                stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=long_stocks,
                                      return_type='domain')
                # add them to eastmoney
                try:
                    try:
                        eastmoneypy.del_group('real')
                    except:
                        pass
                    eastmoneypy.create_group('real')
                    for stock in stocks:
                        eastmoneypy.add_to_group(stock.code, group_name='real')
                except Exception as e:
                    email_action.send_message("5533061@qq.com", f'report state error',
                                              'report state error:{}'.format(e))

                info = [f'{stock.name}({stock.code})[{stock_map_slope.get(stock.entity_id)}]' for stock in stocks]
                msg = msg + '选中:' + ' '.join(info) + '\n'

            logger.info(msg)
            email_action.send_message('5533061@qq.com', f'{target_date} 放量突破年线state选股结果', msg)
            break
        except Exception as e:
            logger.exception('report state error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message("5533061@qq.com", f'report state error',
                                          'report state error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_state.log')

    report_state()

    sched.start()

    sched._thread.join()
