# -*- coding: utf-8 -*-
import datetime
import json
import os

from sqlalchemy import or_

from zvdata.utils.time_utils import to_pd_timestamp
from zvt.domain import FinanceFactor


def get_subscriber_emails():
    emails_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'subscriber_emails.json'))
    with open(emails_file) as f:
        return json.load(f)


def danger_company(the_date):
    start_timestamp = to_pd_timestamp(the_date) - datetime.timedelta(190)
    # 营收降，利润降,流动比率低，速动比率低
    danger_filter = or_(FinanceFactor.op_income_growth_yoy < -0.2,
                        FinanceFactor.net_profit_growth_yoy <= -0.3,
                        FinanceFactor.current_ratio < 0.7,
                        FinanceFactor.quick_ratio < 0.5)
    FinanceFactor.query_data(start_timestamp='2019-09-30', filters=[danger_filter],
                             columns=FinanceFactor.important_cols())


if __name__ == '__main__':
    print(get_subscriber_emails())
