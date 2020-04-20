# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd
from sqlalchemy import func, exists, and_
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query, Session

from zvt.core import IntervalLevel, EntityMixin
from zvt.core.contract import get_db_session, get_db_engine, global_entity_schema, global_providers, \
    get_schema_columns
from zvt.core.utils.pd_utils import pd_is_not_null, index_df
from zvt.core.utils.time_utils import to_pd_timestamp


def get_entity_schema(entity_type: str) -> object:
    """
    get entity schema from name

    :param entity_type:
    :type entity_type:
    :return:
    :rtype:
    """
    return global_entity_schema[entity_type]


def common_filter(query: Query,
                  data_schema,
                  start_timestamp=None,
                  end_timestamp=None,
                  filters=None,
                  order=None,
                  limit=None,
                  time_field='timestamp'):
    assert data_schema is not None
    time_col = eval('data_schema.{}'.format(time_field))

    if start_timestamp:
        query = query.filter(time_col >= to_pd_timestamp(start_timestamp))
    if end_timestamp:
        query = query.filter(time_col <= to_pd_timestamp(end_timestamp))

    if filters:
        for filter in filters:
            query = query.filter(filter)
    if order is not None:
        query = query.order_by(order)
    else:
        query = query.order_by(time_col.asc())
    if limit:
        query = query.limit(limit)

    return query


def get_data(data_schema,
             ids: List[str] = None,
             entity_ids: List[str] = None,
             entity_id: str = None,
             codes: List[str] = None,
             code: str = None,
             level: Union[IntervalLevel, str] = None,
             provider: str = None,
             columns: List = None,
             return_type: str = 'df',
             start_timestamp: Union[pd.Timestamp, str] = None,
             end_timestamp: Union[pd.Timestamp, str] = None,
             filters: List = None,
             session: Session = None,
             order=None,
             limit: int = None,
             index: Union[str, list] = None,
             time_field: str = 'timestamp'):
    assert data_schema is not None
    assert provider is not None
    assert provider in global_providers

    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)

    time_col = eval('data_schema.{}'.format(time_field))

    if columns:
        # support str
        if type(columns[0]) == str:
            columns_ = []
            for col in columns:
                assert isinstance(col, str)
                columns_.append(eval('data_schema.{}'.format(col)))
            columns = columns_

        # make sure get timestamp
        if time_col not in columns:
            columns.append(time_col)

        query = session.query(*columns)
    else:
        query = session.query(data_schema)

    if entity_id:
        query = query.filter(data_schema.entity_id == entity_id)
    if entity_ids:
        query = query.filter(data_schema.entity_id.in_(entity_ids))
    if code:
        query = query.filter(data_schema.code == code)
    if codes:
        query = query.filter(data_schema.code.in_(codes))
    if ids:
        query = query.filter(data_schema.id.in_(ids))

    # we always store different level in different schema,the level param is not useful now
    if level:
        try:
            # some schema has no level,just ignore it
            data_schema.level
            if type(level) == IntervalLevel:
                level = level.value
            query = query.filter(data_schema.level == level)
        except Exception as e:
            pass

    query = common_filter(query, data_schema=data_schema, start_timestamp=start_timestamp,
                          end_timestamp=end_timestamp, filters=filters, order=order, limit=limit,
                          time_field=time_field)

    if return_type == 'df':
        df = pd.read_sql(query.statement, query.session.bind)
        if pd_is_not_null(df):
            if index:
                df = index_df(df, index=index, time_field=time_field)
        return df
    elif return_type == 'domain':
        return query.all()
    elif return_type == 'dict':
        return [item.__dict__ for item in query.all()]


def data_exist(session, schema, id):
    return session.query(exists().where(and_(schema.id == id))).scalar()


def get_count(data_schema, filters=None, session=None):
    query = session.query(data_schema)
    if filters:
        for filter in filters:
            query = query.filter(filter)

    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = session.execute(count_q).scalar()
    return count


def get_group(provider, data_schema, column, group_func=func.count, session=None):
    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)
    if group_func:
        query = session.query(column, group_func(column)).group_by(column)
    else:
        query = session.query(column).group_by(column)
    df = pd.read_sql(query.statement, query.session.bind)
    return df


def decode_entity_id(entity_id: str):
    result = entity_id.split('_')
    entity_type = result[0]
    exchange = result[1]
    code = ''.join(result[2:])
    return entity_type, exchange, code


def get_entity_type(entity_id: str):
    entity_type, _, _ = decode_entity_id(entity_id)
    return entity_type


def get_entity_exchange(entity_id: str):
    _, exchange, _ = decode_entity_id(entity_id)
    return exchange


def get_entity_code(entity_id: str):
    _, _, code = decode_entity_id(entity_id)
    return code


def df_to_db(df: pd.DataFrame,
             data_schema: DeclarativeMeta,
             provider: str,
             force_update: bool = False,
             sub_size: int = 5000) -> object:
    """
    store the df to db

    :param df:
    :type df:
    :param data_schema:
    :type data_schema:
    :param provider:
    :type provider:
    :param force_update:
    :type force_update:
    :param sub_size:
    :return:
    :rtype:
    """
    if not pd_is_not_null(df):
        return

    db_engine = get_db_engine(provider, data_schema=data_schema)

    schema_cols = get_schema_columns(data_schema)
    cols = set(df.columns.tolist()) & set(schema_cols)

    if not cols:
        print('wrong cols')
        return

    df = df[cols]

    size = len(df)

    if size >= sub_size:
        step_size = int(size / sub_size)
        if size % sub_size:
            step_size = step_size + 1
    else:
        step_size = 1

    for step in range(step_size):
        df_current = df.iloc[sub_size * step:sub_size * (step + 1)]
        if force_update:
            session = get_db_session(provider=provider, data_schema=data_schema)
            ids = df_current["id"].tolist()
            if len(ids) == 1:
                sql = f'delete from {data_schema.__tablename__} where id = "{ids[0]}"'
            else:
                sql = f'delete from {data_schema.__tablename__} where id in {tuple(ids)}'

            session.execute(sql)
            session.commit()

        else:
            current = get_data(data_schema=data_schema, columns=[data_schema.id], provider=provider,
                               ids=df_current['id'].tolist())
            if pd_is_not_null(current):
                df_current = df_current[~df_current['id'].isin(current['id'])]

        df_current.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists='append')


def get_entities(
        entity_schema: EntityMixin = None,
        entity_type: str = None,
        exchanges: List[str] = None,
        ids: List[str] = None,
        entity_ids: List[str] = None,
        entity_id: str = None,
        codes: List[str] = None,
        code: str = None,
        provider: str = None,
        columns: List = None,
        return_type: str = 'df',
        start_timestamp: Union[pd.Timestamp, str] = None,
        end_timestamp: Union[pd.Timestamp, str] = None,
        filters: List = None,
        session: Session = None,
        order=None,
        limit: int = None,
        index: Union[str, list] = 'code') -> object:
    if not entity_schema:
        entity_schema = global_entity_schema[entity_type]

    if not provider:
        provider = entity_schema.providers[0]

    if not order:
        order = entity_schema.code.asc()

    if exchanges:
        if filters:
            filters.append(entity_schema.exchange.in_(exchanges))
        else:
            filters = [entity_schema.exchange.in_(exchanges)]

    return get_data(data_schema=entity_schema, ids=ids, entity_ids=entity_ids, entity_id=entity_id, codes=codes,
                    code=code, level=None, provider=provider, columns=columns, return_type=return_type,
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, filters=filters, session=session,
                    order=order, limit=limit,
                    index=index)


def get_entity_ids(entity_type='stock', entity_schema: EntityMixin = None, exchanges=None, codes=None, provider=None):
    df = get_entities(entity_type=entity_type, entity_schema=entity_schema, exchanges=exchanges, codes=codes,
                      provider=provider)
    if pd_is_not_null(df):
        return df['entity_id'].to_list()
    return None
