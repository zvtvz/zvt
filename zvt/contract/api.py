# -*- coding: utf-8 -*-
import logging
import os
import platform
from typing import List, Union, Type

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import func, exists, and_
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query
from sqlalchemy.orm import sessionmaker, Session

from zvt import zvt_env
from zvt.contract import IntervalLevel, EntityMixin
from zvt.contract import Mixin
from zvt.contract import zvt_context
from zvt.utils.pd_utils import pd_is_not_null, index_df
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


def get_db_name(data_schema: DeclarativeMeta) -> str:
    """
    get db name of the domain schema

    :param data_schema:
    :type data_schema:
    :return:
    :rtype:
    """
    for db_name, base in zvt_context.dbname_map_base.items():
        if issubclass(data_schema, base):
            return db_name


def get_db_engine(provider: str,
                  db_name: str = None,
                  data_schema: object = None,
                  data_path: str = zvt_env['data_path']) -> Engine:
    """
    get db engine of the (provider,db_name) or (provider,data_schema)


    :param data_path:
    :param provider:
    :type provider:
    :param db_name:
    :type db_name:
    :param data_schema:
    :type data_schema:
    :return:
    :rtype:
    """
    if data_schema:
        db_name = get_db_name(data_schema=data_schema)

    db_path = os.path.join(data_path, '{}_{}.db?check_same_thread=False'.format(provider, db_name))

    engine_key = '{}_{}'.format(provider, db_name)
    db_engine = zvt_context.db_engine_map.get(engine_key)
    if not db_engine:
        db_engine = create_engine('sqlite:///' + db_path, echo=False)
        zvt_context.db_engine_map[engine_key] = db_engine
    return db_engine


def get_schemas(provider: str) -> List[DeclarativeMeta]:
    """
    get domain schemas supported by the provider

    :param provider:
    :type provider:
    :return:
    :rtype:
    """
    schemas = []
    for provider1, dbs in zvt_context.provider_map_dbnames.items():
        if provider == provider1:
            for dbname in dbs:
                schemas1 = zvt_context.dbname_map_schemas.get(dbname)
                if schemas1:
                    schemas += schemas1
    return schemas


def get_db_session(provider: str,
                   db_name: str = None,
                   data_schema: object = None,
                   force_new: bool = False) -> Session:
    """
    get db session of the (provider,db_name) or (provider,data_schema)

    :param provider:
    :type provider:
    :param db_name:
    :type db_name:
    :param data_schema:
    :type data_schema:
    :param force_new:
    :type force_new:

    :return:
    :rtype:
    """
    if data_schema:
        db_name = get_db_name(data_schema=data_schema)

    session_key = '{}_{}'.format(provider, db_name)

    if force_new:
        return get_db_session_factory(provider, db_name, data_schema)()

    session = zvt_context.sessions.get(session_key)
    if not session:
        session = get_db_session_factory(provider, db_name, data_schema)()
        zvt_context.sessions[session_key] = session
    return session


def get_db_session_factory(provider: str,
                           db_name: str = None,
                           data_schema: object = None):
    """
    get db session factory of the (provider,db_name) or (provider,data_schema)

    :param provider:
    :type provider:
    :param db_name:
    :type db_name:
    :param data_schema:
    :type data_schema:
    :return:
    :rtype:
    """
    if data_schema:
        db_name = get_db_name(data_schema=data_schema)

    session_key = '{}_{}'.format(provider, db_name)
    session = zvt_context.db_session_map.get(session_key)
    if not session:
        session = sessionmaker()
        zvt_context.db_session_map[session_key] = session
    return session


def domain_name_to_table_name(domain_name: str) -> str:
    parts = []
    part = ''
    for c in domain_name:
        if c.isupper() or c.isdigit():
            if part:
                parts.append(part)
            part = c.lower()
        else:
            part = part + c

    parts.append(part)

    if len(parts) > 1:
        return '_'.join(parts)
    elif parts:
        return parts[0]


def table_name_to_domain_name(table_name: str) -> DeclarativeMeta:
    """
    the rules for table_name -> domain_class

    :param table_name:
    :type table_name:
    :return:
    :rtype:
    """
    parts = table_name.split('_')
    domain_name = ''
    for part in parts:
        domain_name = domain_name + part.capitalize()
    return domain_name


def get_entity_schema(entity_type: str) -> object:
    """
    get entity schema from name

    :param entity_type:
    :type entity_type:
    :return:
    :rtype:
    """
    return zvt_context.zvt_entity_schema_map[entity_type]


def get_schema_by_name(name: str) -> DeclarativeMeta:
    """
    get domain schema by the name

    :param name:
    :type name:
    :return:
    :rtype:
    """
    for schema in zvt_context.schemas:
        if schema.__name__ == name:
            return schema


def get_schema_columns(schema: DeclarativeMeta) -> object:
    """
    get all columns of the domain schema

    :param schema:
    :type schema:
    :return:
    :rtype:
    """
    return schema.__table__.columns.keys()


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


def del_data(data_schema: Type[Mixin], filters: List = None, provider=None):
    if not provider:
        provider = data_schema.providers[0]

    session = get_db_session(provider=provider, data_schema=data_schema)
    query = session.query(data_schema)
    if filters:
        for f in filters:
            query = query.filter(f)
    query.delete()
    session.commit()


def get_data(data_schema,
             ids: List[str] = None,
             entity_ids: List[str] = None,
             entity_id: str = None,
             codes: List[str] = None,
             code: str = None,
             level: Union[IntervalLevel, str] = None,
             provider: str = None,
             columns: List = None,
             col_label: dict = None,
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
    assert provider in zvt_context.providers

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

        if col_label:
            columns_ = []
            for col in columns:
                if col.name in col_label:
                    columns_.append(col.label(col_label.get(col.name)))
                else:
                    columns_.append(col)
            columns = columns_

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


def get_data_count(data_schema, filters=None, session=None):
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
             sub_size: int = 5000,
             drop_duplicates: bool = False) -> object:
    """
    FIXME:improve
    store the df to db

    :param df:
    :param data_schema:
    :param provider:
    :param force_update:
    :param sub_size:
    :param drop_duplicates:
    :return:
    """
    if not pd_is_not_null(df):
        return 0

    if drop_duplicates and df.duplicated(subset='id').any():
        logger.warning(f'remove duplicated:{df[df.duplicated()]}')
        df = df.drop_duplicates(subset='id', keep='last')

    db_engine = get_db_engine(provider, data_schema=data_schema)

    schema_cols = get_schema_columns(data_schema)
    cols = set(df.columns.tolist()) & set(schema_cols)

    if not cols:
        print('wrong cols')
        return 0

    df = df[cols]

    size = len(df)

    if platform.system() == "Windows":
        sub_size = 900

    if size >= sub_size:
        step_size = int(size / sub_size)
        if size % sub_size:
            step_size = step_size + 1
    else:
        step_size = 1

    saved = 0

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

        if pd_is_not_null(df_current):
            saved = saved + len(df_current)
            df_current.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists='append')

    return saved


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
        col_label: dict = None,
        return_type: str = 'df',
        start_timestamp: Union[pd.Timestamp, str] = None,
        end_timestamp: Union[pd.Timestamp, str] = None,
        filters: List = None,
        session: Session = None,
        order=None,
        limit: int = None,
        index: Union[str, list] = 'code') -> object:
    if not entity_schema:
        entity_schema = zvt_context.entity_schema_map[entity_type]

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
                    code=code, level=None, provider=provider, columns=columns, col_label=col_label,
                    return_type=return_type, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                    filters=filters, session=session, order=order, limit=limit, index=index)


def get_entity_ids(entity_type='stock', entity_schema: EntityMixin = None, exchanges=None, codes=None, provider=None):
    df = get_entities(entity_type=entity_type, entity_schema=entity_schema, exchanges=exchanges, codes=codes,
                      provider=provider)
    if pd_is_not_null(df):
        return df['entity_id'].to_list()
    return None
