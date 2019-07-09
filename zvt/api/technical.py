# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd
from sqlalchemy.orm import Session

from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import get_data, decode_security_id
from zvt.api.common import get_security_schema, get_kdata_schema
from zvt.domain import get_db_engine, TradingLevel, Provider, get_store_category, SecurityType, get_db_session, \
    StoreCategory, Index
from zvt.utils.pd_utils import df_is_not_null


def init_securities(df, security_type='stock', provider=Provider.EASTMONEY):
    df = df.drop_duplicates(subset=['id'])
    data_schema = get_security_schema(security_type)
    store_category = get_store_category(data_schema=data_schema)

    db_engine = get_db_engine(provider, store_category=store_category)
    security_schema = get_security_schema(security_type)

    current = get_securities(security_type=security_type, columns=[security_schema.id, security_schema.code],
                             provider=provider)

    if df_is_not_null(current):
        df = df[~df['id'].isin(current['id'])]

    df.to_sql(security_schema.__tablename__, db_engine, index=False, if_exists='append')


def df_to_db(df, data_schema, provider):
    store_category = get_store_category(data_schema)
    db_engine = get_db_engine(provider, store_category=store_category)

    current = get_data(data_schema=data_schema, columns=[data_schema.id], provider=provider)
    if df_is_not_null(current):
        df = df[~df['id'].isin(current['id'])]

    df.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists='append')


def get_securities_in_blocks(block_names=['HS300_'], block_category='concept', provider='eastmoney'):
    session = get_db_session(provider=provider, store_category=StoreCategory.meta)

    filters = [Index.category == block_category]
    name_filters = None
    for block_name in block_names:
        if name_filters:
            name_filters |= (Index.name == block_name)
        else:
            name_filters = (Index.name == block_name)
    filters.append(name_filters)
    blocks = get_securities(security_type='index', provider='eastmoney',
                            filters=filters,
                            return_type='domain', session=session)
    securities = []
    for block in blocks:
        securities += [item.stock_id for item in block.stocks]

    return securities


def get_securities(security_list: List[str] = None,
                   security_type: Union[SecurityType, str] = 'stock',
                   exchanges: List[str] = None,
                   codes: List[str] = None,
                   columns: List = None,
                   return_type: str = 'df',
                   session: Session = None,
                   start_timestamp: Union[str, pd.Timestamp] = None,
                   end_timestamp: Union[str, pd.Timestamp] = None,
                   filters: List = None,
                   order: object = None,
                   limit: int = None,
                   provider: Union[str, Provider] = 'eastmoney',
                   index: str = 'code',
                   index_is_time: bool = False) -> object:
    data_schema = get_security_schema(security_type)

    if not order:
        order = data_schema.code.asc()

    if exchanges:
        if filters:
            filters.append(data_schema.exchange.in_(exchanges))
        else:
            filters = [data_schema.exchange.in_(exchanges)]

    return get_data(data_schema=data_schema, security_list=security_list, security_id=None, codes=codes, level=None,
                    provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters,
                    session=session, order=order, limit=limit, index=index, index_is_time=index_is_time)


def get_kdata(security_id, level=TradingLevel.LEVEL_1DAY.value, provider='eastmoney', columns=None,
              return_type='df', start_timestamp=None, end_timestamp=None,
              filters=None, session=None, order=None, limit=None):
    security_type, exchange, code = decode_security_id(security_id)
    data_schema = get_kdata_schema(security_type, level=level)

    return get_data(data_schema=data_schema, security_id=security_id, level=level, provider=provider, columns=columns,
                    return_type=return_type,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_current_price(security_list=None, security_type=SecurityType.coin):
    result = {}
    if security_type == SecurityType.coin:
        if security_list:
            for security_id in security_list:
                a, exchange, code = decode_security_id(security_id)
                assert SecurityType(a) == security_type
                ccxt_exchange = CCXTAccount.get_ccxt_exchange(exchange_str=exchange)

                if not ccxt_exchange:
                    raise Exception('{} not support'.format(exchange))

                orderbook = ccxt_exchange.fetch_order_book(code)

                bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
                ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
                security_id = f'coin_{exchange}_{code}'
                result[security_id] = (bid, ask)

    return result


if __name__ == '__main__':
    # print(get_securities())
    # print(get_kdata(security_id='stock_sz_300027', provider='netease'))
    # print(get_kdata(security_id='coin_binance_EOS/USDT', provider='ccxt', level=TradingLevel.LEVEL_1MIN))
    # print(get_finance_factor(security_id='stock_sh_601318', session=get_db_session('eastmoney')))
    # a = get_stock_category('stock_sz_000029')
    # print(a)
    # a = get_securities(codes=['000029', '000778'], return_type='dict')
    # b = get_securities(codes=['000029', '000778'], return_type='df')
    # c = get_securities(codes=['000029', '000778'], return_type='domain')
    # d = get_securities(security_type='index', codes=['BK0451'], return_type='dict')
    #
    # print(get_securities())
    # print(get_securities(columns=[Stock.code]))
    # df = get_securities(codes=['000029', '000778'], session=get_db_session('eastmoney'))
    # print(df)
    #
    # print(get_securities(codes=['000338', '000778', '600338'], exchanges=['sz']))
    print(get_current_price(['coin_huobipro_EOS/USDT', 'coin_binance_EOS/USDT']))
