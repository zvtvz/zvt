# -*- coding: utf-8 -*-

from zvt.api.common import get_data
from zvt.domain.account import SimAccount, Position


def get_account(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                filters=None, session=None, order=None, limit=None):
    if trader_name:
        if filters:
            filters = filters + [SimAccount.trader_name == trader_name]
        else:
            filters = [SimAccount.trader_name == trader_name]

    return get_data(data_schema=SimAccount, security_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_position(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                 filters=None, session=None, order=None, limit=None):
    if trader_name:
        if filters:
            filters = filters + [Position.trader_name == trader_name]
        else:
            filters = [Position.trader_name == trader_name]

    return get_data(data_schema=Position, security_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


if __name__ == '__main__':
    print(get_account())
