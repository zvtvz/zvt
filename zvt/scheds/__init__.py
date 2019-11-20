# -*- coding: utf-8 -*-
import logging

from zvdata.utils.time_utils import now_pd_timestamp, to_time_str
from zvt.domain import CashFlowStatement
from zvt.factors import TargetSelector, GoodCompanyFactor

logger = logging.getLogger(__name__)


def select_by_finance(timestamp=now_pd_timestamp(), entity_ids=None):
    if timestamp.dayofweek in (5, 6):
        logger.info(f'today:{timestamp} is {timestamp.day_name()},just ignore')

    today = to_time_str(timestamp)

    my_selector = TargetSelector(start_timestamp='2015-01-01', end_timestamp=today, entity_ids=entity_ids)
    # add the factors
    good_factor1 = GoodCompanyFactor(start_timestamp='2015-01-01', end_timestamp=today, entity_ids=entity_ids)
    good_factor2 = GoodCompanyFactor(start_timestamp='2015-01-01', end_timestamp=today, entity_ids=entity_ids,
                                     data_schema=CashFlowStatement,
                                     columns=[CashFlowStatement.report_period,
                                              CashFlowStatement.net_op_cash_flows],
                                     filters=[CashFlowStatement.net_op_cash_flows > 0],
                                     col_threshold={'net_op_cash_flows': 100000000})

    my_selector.add_filter_factor(good_factor1)
    my_selector.add_filter_factor(good_factor2)
    my_selector.run()

    long_targets = my_selector.get_open_long_targets(today)

    logger.info(f'selected:{len(long_targets)}')

    return long_targets
