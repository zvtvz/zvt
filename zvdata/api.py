# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd
from sqlalchemy import func, exists, and_
from sqlalchemy.orm import Query, Session
from zvdata.domain import get_db_name, get_db_session, get_db_engine, entity_type_map_schema, global_providers
from zvdata.structs import IntervalLevel
from zvdata.utils.pd_utils import df_is_not_null, index_df
from zvdata.utils.time_utils import to_pd_timestamp


def get_entity_schema(entity_type):
    return entity_type_map_schema[entity_type]


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
             entity_ids: List[str] = None,
             entity_id: str = None,
             codes: List[str] = None,
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
             index: str = 'timestamp',
             index_is_time: bool = True,
             time_field: str = 'timestamp'):
    assert data_schema is not None
    assert provider is not None
    assert provider in global_providers

    local_session = False
    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)
        local_session = True

    try:
        time_col = eval('data_schema.{}'.format(time_field))

        if columns:
            # support str
            if type(columns[0]) == str:
                columns_ = []
                for col in columns:
                    columns_.append(eval('data_schema.{}'.format(col)))
                columns = columns_

            if time_col not in columns:
                columns.append(time_col)
            query = session.query(*columns)
        else:
            query = session.query(data_schema)

        if entity_id:
            query = query.filter(data_schema.entity_id == entity_id)
        if codes:
            query = query.filter(data_schema.code.in_(codes))
        if entity_ids:
            query = query.filter(data_schema.entity_id.in_(entity_ids))

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
            if df_is_not_null(df):
                return index_df(df, drop=False, index=index, index_is_time=index_is_time)
            return df
        elif return_type == 'domain':
            return query.all()
        elif return_type == 'dict':
            return [item.__dict__ for item in query.all()]
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


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
    local_session = False
    if not session:
        store_category = get_db_name(data_schema)
        session = get_db_session(provider=provider, store_category=store_category)
        local_session = True
    try:
        if group_func:
            query = session.query(column, group_func(column)).group_by(column)
        else:
            query = session.query(column).group_by(column)
        df = pd.read_sql(query.statement, query.session.bind)
        return df
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


def decode_entity_id(entity_id: str):
    result = entity_id.split('_')
    entity_type = result[0]
    exchange = result[1]
    code = ''.join(result[2:])
    return entity_type, exchange, code


def df_to_db(df, data_schema, provider):
    db_engine = get_db_engine(provider, data_schema=data_schema)

    current = get_data(data_schema=data_schema, columns=[data_schema.id], provider=provider)
    if df_is_not_null(current):
        df = df[~df['id'].isin(current['id'])]

    df.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists='append')


def init_entities(df, entity_type='stock', provider='exchange'):
    df = df.drop_duplicates(subset=['id'])
    data_schema = get_entity_schema(entity_type)
    store_category = get_db_name(data_schema=data_schema)

    db_engine = get_db_engine(provider, db_name=store_category)
    security_schema = get_entity_schema(entity_type)

    current = get_entities(entity_type=entity_type, columns=[security_schema.id, security_schema.code],
                           provider=provider)

    if df_is_not_null(current):
        df = df[~df['id'].isin(current['id'])]

    df.to_sql(security_schema.__tablename__, db_engine, index=False, if_exists='append')


def get_entities(
        entity_schema=None,
        entity_ids: List[str] = None,
        entity_type: str = None,
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
        provider: str = None,
        index: str = 'code',
        index_is_time: bool = False) -> object:
    assert provider in global_providers

    if not entity_schema:
        entity_schema = entity_type_map_schema[entity_type]

    if not order:
        order = entity_schema.code.asc()

    if exchanges:
        if filters:
            filters.append(entity_schema.exchange.in_(exchanges))
        else:
            filters = [entity_schema.exchange.in_(exchanges)]

    return get_data(data_schema=entity_schema, entity_ids=entity_ids, entity_id=None, codes=codes, level=None,
                    provider=provider, columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit,
                    index=index, index_is_time=index_is_time)
