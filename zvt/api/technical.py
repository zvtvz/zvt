# -*- coding: utf-8 -*-

import pandas as pd

from zvt.api.common import common_filter, get_data, decode_security_id
from zvt.api.common import get_security_schema, get_kdata_schema
from zvt.domain import get_db_engine, get_db_session, TradingLevel, Provider, get_store_category
from zvt.utils.pd_utils import df_is_not_null


def init_securities(df, security_type='stock', provider=Provider.EASTMONEY):
    df = df.drop_duplicates(subset=['id'])
    data_schema = get_security_schema(security_type)
    store_category = get_store_category(data_schema=data_schema)

    db_engine = get_db_engine(provider, store_category=store_category)
    security_schema = get_security_schema(security_type)

    current = get_securities(security_type=security_type, columns=[security_schema.id], provider=provider)
    df = df[~df['id'].isin(current['id'])]

    df.to_sql(security_schema.__tablename__, db_engine, index=False, if_exists='append')


def df_to_db(df, data_schema, provider):
    store_category = get_store_category(data_schema)
    db_engine = get_db_engine(provider, store_category=store_category)

    current = get_data(data_schema=data_schema, columns=[data_schema.id], provider=provider)
    if df_is_not_null(current):
        df = df[~df['id'].isin(current['id'])]

    df.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists='append')


def get_securities(security_type='stock', exchanges=None, codes=None, columns=None,
                   return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                   filters=None, order=None, limit=None, provider='eastmoney'):
    local_session = False

    data_schema = get_security_schema(security_type)
    store_category = get_store_category(data_schema=data_schema)

    if not session:
        session = get_db_session(provider=provider, store_category=store_category)
        local_session = True

    if not order:
        order = data_schema.code.asc()

    try:
        if columns:
            query = session.query(*columns)
        else:
            query = session.query(data_schema)

        # filters
        if exchanges:
            query = query.filter(data_schema.exchange.in_(exchanges))
        if codes:
            query = query.filter(data_schema.code.in_(codes))

        query = common_filter(query, data_schema=data_schema, start_timestamp=start_timestamp,
                              end_timestamp=end_timestamp, filters=filters, order=order, limit=limit)

        if return_type == 'df':
            # TODO:add indices info
            return pd.read_sql(query.statement, query.session.bind)
        elif return_type == 'domain':
            return query.all()
        elif return_type == 'dict':
            return [item.to_json() for item in query.all()]
    except Exception as e:

        raise
    finally:
        if local_session:
            session.close()


def get_kdata(security_id, level=TradingLevel.LEVEL_1DAY.value, provider='eastmoney', columns=None,
              return_type='df', start_timestamp=None, end_timestamp=None,
              filters=None, session=None, order=None, limit=None):
    security_type, exchange, code = decode_security_id(security_id)
    data_schema = get_kdata_schema(security_type, level=level)

    return get_data(data_schema=data_schema, security_id=security_id, level=level, provider=provider, columns=columns,
                    return_type=return_type,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


if __name__ == '__main__':
    # print(get_securities())
    # print(get_kdata(security_id='stock_sz_300027', provider='netease'))
    print(get_kdata(security_id='coin_binance_EOS/USDT', provider='ccxt', level=TradingLevel.LEVEL_1MIN))
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
