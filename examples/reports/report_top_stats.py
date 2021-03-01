# -*- coding: utf-8 -*-
import logging

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler
from tabulate import tabulate

from zvt import init_log, zvt_config
from zvt.api import get_top_performance_entities, get_top_volume_entities
from zvt.contract.api import get_entity_ids, decode_entity_id
from zvt.domain import Stock
from zvt.domain import Stock1dHfqKdata
from zvt.informer.informer import EmailInformer
from zvt.utils.time_utils import next_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=18, minute=30, day_of_week='mon-fri')
def report_top_stats(periods=[7, 30, 180, 365], ignore_new_stock=True):
    latest_day: Stock1dHfqKdata = Stock1dHfqKdata.query_data(order=Stock1dHfqKdata.timestamp.desc(), limit=1,
                                                             return_type='domain')
    current_timestamp = latest_day[0].timestamp
    email_action = EmailInformer()

    # 至少上市一年
    filters = None
    if ignore_new_stock:
        pre_year = next_date(current_timestamp, -365)

        stocks = get_entity_ids(provider='joinquant', entity_schema=Stock, filters=[Stock.timestamp <= pre_year])
        filters = [Stock1dHfqKdata.entity_id.in_(stocks)]

    stats = []
    ups = []
    downs = []

    for period in periods:
        start = next_date(current_timestamp, -period)
        df, _ = get_top_performance_entities(start_timestamp=start, filters=filters, pct=1, show_name=True)
        df.rename(columns={'score': f'score_{period}'}, inplace=True)
        ups.append(tabulate(df.iloc[:50], headers='keys'))
        downs.append(tabulate(df.iloc[-50:], headers='keys'))

        stats.append(tabulate(df.describe(), headers='keys'))

        # 最近一个月最靓仔的
        if period == 30:
            # add them to eastmoney
            try:
                try:
                    eastmoneypy.del_group('最靓仔')
                except:
                    pass
                eastmoneypy.create_group('最靓仔')
                for entity_id in df.index[:50]:
                    _, _, code = decode_entity_id(entity_id)
                    eastmoneypy.add_to_group(code=code, group_name='最靓仔')
            except Exception as e:
                logger.exception(e)
                email_action.send_message("5533061@qq.com", f'report_top_stats error',
                                          'report_top_stats error:{}'.format(e))

        # 一年内没怎么动的
        if period == 365:
            stable_df = df[(df['score_365'] > -0.1) & (df['score_365'] < 0.1)]
            vol_df = get_top_volume_entities(entity_ids=stable_df.index.tolist(), start_timestamp=start)

            # add them to eastmoney
            try:
                try:
                    eastmoneypy.del_group('躺尸一年')
                except:
                    pass
                eastmoneypy.create_group('躺尸一年')
                for entity_id in vol_df.index[:50]:
                    _, _, code = decode_entity_id(entity_id)
                    eastmoneypy.add_to_group(code=code, group_name='躺尸一年')
            except Exception as e:
                logger.exception(e)
                email_action.send_message(zvt_config['email_username'], f'report_top_stats error',
                                          'report_top_stats error:{}'.format(e))

    msg = '\n'
    for s in stats:
        msg = msg + s + '\n'
    email_action.send_message(zvt_config['email_username'], f'{current_timestamp} 统计报告', msg)

    msg = '\n'
    for up in ups:
        msg = msg + up + '\n'
    email_action.send_message(zvt_config['email_username'], f'{current_timestamp} 涨幅统计报告', msg)

    msg = '\n'
    for down in downs:
        msg = msg + down + '\n'

    email_action.send_message(zvt_config['email_username'], f'{current_timestamp} 跌幅统计报告', msg)


if __name__ == '__main__':
    init_log('report_top_stats.log')

    report_top_stats()

    sched.start()

    sched._thread.join()
