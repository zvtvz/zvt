# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from jqdatasdk import auth,get_query_count

from zvt import init_log, zvt_env
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=15, minute=20)
def record_kdata():
    while True:
        email_action = EmailInformer()

        try:
            # Stock.record_data(provider='joinquant', sleeping_time=1)
            # StockDetail.record_data(provider='eastmoney',sleeping_time=1)
            # Stock1dKdata.record_data(provider='joinquant', sleeping_time=1)  # 前复权
            BalanceSheet.record_data(provider='joinquant', sleeping_time=1)

            # Index1dKdata.record_data(provider='joinquant',sleeping_time=1)
            # Index1monKdata.record_data(codes=['000001'],provider='joinquant' ,sleeping_time=1,real_time=True) # 前复权
            # Index1wkKdata.record_data(codes=['000001'],provider='joinquant' ,sleeping_time=1) # 前复权
            # Stock1dBfqKdata.record_data(codes=['000852'],provider='joinquant' ,sleeping_time=1) # 不复权
            # Stock1monBfqKdata.record_data(codes=['000852'],provider='joinquant' ,sleeping_time=1) # 不复权
            # StockValuation.record_data(provider='joinquant', sleeping_time=1)
            # Stock1dHfqKdata.record_data(codes=['000852'],provider='joinquant', sleeping_time=1) # 后复权

            # IncomeStatement.record_data(codes=['000852'],provider='joinquant',sleeping_time=1)
            # CashFlowStatement.record_data(codes=['000852'],provider='joinquant',sleeping_time=1)

            # StockTradeDay.record_data(provider='joinquant', sleeping_time=1)

            # Stock1wkKdata.record_data(codes=['000852'],provider='joinquant', sleeping_time=1)
            # Stock1wkHfqKdata.record_data(codes=['000852'],provider='joinquant', sleeping_time=1)
            # Stock1wkBfqKdata.record_data(codes=['000852'],provider='joinquant', sleeping_time=1) # 不复权
            # HolderTrading.record_data(codes=['000852'],provider='joinquant', sleeping_time=1)
            # email_action.send_message("327714319@qq.com", 'joinquant record kdata finished', '')

            # Etf.record_data(provider='joinquant', sleeping_time=1)
            # Fund.record_data(provider='joinquant', sleeping_time=1)
            # EtfStock.record_data(provider='joinquant', sleeping_time=1)
            # FundDetail.record_data(provider='joinquant', sleeping_time=0.5)
            # FundStock.record_data(provider='joinquant', sleeping_time=1)
            # FundNetValue.record_data(codes=['150008'],provider='joinquant', sleeping_time=1)
            # Etf1dKdata.record_data(codes=['050002'],provider='joinquant', sleeping_time=1)
            # Etf1dBfqKdata.record_data(codes=['512290'],provider='joinquant', sleeping_time=1)
            # Etf1dHfqKdata.record_data(codes=['512290'],provider='joinquant', sleeping_time=1)

            # DividendDetail.record_data(codes=['000852'],provider='emquantapi', sleeping_time=1)
            # RightsIssueDetail.record_data(codes=['000852'],provider='emquantapi', sleeping_time=1)
            break
        except Exception as e:
            msg = f'joinquant record kdata:{e}'
            logger.exception(msg)

            # email_action.send_message("327714319@qq.com", 'joinquant record kdata error', msg)
            time.sleep(60)


@sched.scheduled_job('cron', hour=19, minute=00, day_of_week=3)
def record_others():
    while True:
        email_action = EmailInformer()

        try:
            HolderTrading.record_data(provider='joinquant', sleeping_time=1)
            # Etf.record_data(provider='joinquant', sleeping_time=1)
            # Fund.record_data(provider='joinquant', sleeping_time=1)
            # EtfStock.record_data(provider='joinquant', sleeping_time=1)
            # Stock.record_data(provider='joinquant', sleeping_time=0.5)
            # FundDetail.record_data(provider='joinquant', sleeping_time=0.5)
            # EtfStock.record_data(provider='joinquant', sleeping_time=1)
            # FundStock.record_data(provider='joinquant', sleeping_time=1)
            # FundNetValue.record_data(codes=['150008'],provider='joinquant', sleeping_time=1)
            # EtfNetValue.record_data(provider='joinquant', sleeping_time=1)
            # EtfStock.record_data(codes=['159803'],provider='joinquant', sleeping_time=1)
            # Etf1dKdata.record_data(codes=['050002'],provider='joinquant', sleeping_time=1)
            # Etf1dBfqKdata.record_data(codes=['512290'],provider='joinquant', sleeping_time=1)
            # Etf1dHfqKdata.record_data(codes=['512290'],provider='joinquant', sleeping_time=1)
            # email_action.send_message("327714319@qq.com", 'joinquant record etf finished', '')
            break
        except Exception as e:
            msg = f'joinquant record etf error:{e}'
            logger.exception(msg)

            email_action.send_message("327714319@qq.com", 'joinquant record etf error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('joinquant_data_runner.log')
    auth(zvt_env['jq_username'], zvt_env['jq_password'])
    print(f"剩余{get_query_count()['spare'] / 10000}万")
    record_kdata()
    # record_others()
    sched.start()
    print(f"剩余{get_query_count()['spare'] / 10000}万")
    sched._thread.join()
