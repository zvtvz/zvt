# -*- coding: utf-8 -*-
from typing import List

from zvt.contract.api import get_group, get_data, get_db_session
from zvt.domain import trader_info
from zvt.domain.trader_info import AccountStats, Position, Order
from zvt.utils.pd_utils import pd_is_not_null


def get_traders() -> List[str]:
    df = get_group(provider='zvt', data_schema=AccountStats, column=AccountStats.trader_name, group_func=None)
    if pd_is_not_null(df):
        return df['trader_name'].tolist()
    return []


def get_trader_info(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                    filters=None, session=None, order=None, limit=None) -> List[trader_info.TraderInfo]:
    if trader_name:
        if filters:
            filters = filters + [trader_info.TraderInfo.trader_name == trader_name]
        else:
            filters = [trader_info.TraderInfo.trader_name == trader_name]

    return get_data(data_schema=trader_info.TraderInfo, entity_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_account_stats(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                      filters=None, session=None, order=None, limit=None):
    if trader_name:
        if filters:
            filters = filters + [AccountStats.trader_name == trader_name]
        else:
            filters = [AccountStats.trader_name == trader_name]

    return get_data(data_schema=AccountStats, entity_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_position(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                 filters=None, session=None, order=None, limit=None):
    if trader_name:
        if filters:
            filters = filters + [Position.trader_name == trader_name]
        else:
            filters = [Position.trader_name == trader_name]

    return get_data(data_schema=Position, entity_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_orders(trader_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
               filters=None, session=None, order=None, limit=None):
    if trader_name:
        if filters:
            filters = filters + [Order.trader_name == trader_name]
        else:
            filters = [Order.trader_name == trader_name]

    return get_data(data_schema=Order, entity_id=None, codes=None, level=None, provider='zvt',
                    columns=None, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_order_securities(trader_name):
    items = get_db_session(provider='zvt', data_schema=Order).query(Order.entity_id).filter(
        Order.trader_name == trader_name).group_by(Order.entity_id).all()

    return [item[0] for item in items]


if __name__ == '__main__':
    print(get_order_securities(trader_name='000338_ma_trader'))
