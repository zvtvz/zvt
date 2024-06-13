# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from examples.factors.fundamental_selector import FundamentalSelector
from examples.reports import get_subscriber_emails, stocks_with_info
from zvt import init_log, zvt_config
from zvt.contract.api import get_entities
from zvt.domain import Stock
from zvt.factors.target_selector import TargetSelector
from zvt.informer.inform_utils import add_to_eastmoney
from zvt.informer.informer import EmailInformer
from zvt.utils.time_utils import now_pd_timestamp, to_time_str

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 基本面选股 每周一次即可 基本无变化
@sched.scheduled_job("cron", hour=16, minute=0, day_of_week="6")
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

            my_selector: TargetSelector = FundamentalSelector(start_timestamp="2016-01-01", end_timestamp=target_date)
            my_selector.run()

            long_targets = my_selector.get_open_long_targets(timestamp=target_date)
            if long_targets:
                stocks = get_entities(
                    provider="joinquant", entity_schema=Stock, entity_ids=long_targets, return_type="domain"
                )

                # add them to eastmoney
                try:
                    codes = [stock.code for stock in stocks]
                    add_to_eastmoney(codes=codes, entity_type="stock", group="core")
                except Exception as e:
                    email_action.send_message(
                        zvt_config["email_username"],
                        f"report_core_company error",
                        "report_core_company error:{}".format(e),
                    )

                infos = stocks_with_info(stocks)
                msg = "\n".join(infos)
            else:
                msg = "no targets"

            logger.info(msg)

            email_action.send_message(get_subscriber_emails(), f"{to_time_str(target_date)} 核心资产选股结果", msg)
            break
        except Exception as e:
            logger.exception("report_core_company error:{}".format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message(
                    zvt_config["email_username"], f"report_core_company error", "report_core_company error:{}".format(e)
                )


if __name__ == "__main__":
    init_log("report_core_company.log")

    report_core_company()

    sched.start()

    sched._thread.join()
