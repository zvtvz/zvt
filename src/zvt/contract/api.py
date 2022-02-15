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
from zvt.contract import IntervalLevel
from zvt.contract import zvt_context
from zvt.contract.schema import Mixin, TradableEntity
from zvt.utils.pd_utils import pd_is_not_null, index_df
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


def _get_db_name(data_schema: DeclarativeMeta) -> str:
    """
    get db name of the domain schema

    :param data_schema: the data schema
    :return: db name
    """
    for db_name, base in zvt_context.dbname_map_base.items():
        if issubclass(data_schema, base):
            return db_name


def get_db_engine(
    provider: str, db_name: str = None, data_schema: object = None, data_path: str = zvt_env["data_path"]
) -> Engine:
    """
    get db engine from (provider,db_name) or (provider,data_schema)

    :param provider: data provider
    :param db_name: db name
    :param data_schema: data schema
    :param data_path: data path
    :return: db engine
    """
    if data_schema:
        db_name = _get_db_name(data_schema=data_schema)

    db_path = os.path.join(data_path, "{}_{}.db?check_same_thread=False".format(provider, db_name))

    engine_key = "{}_{}".format(provider, db_name)
    db_engine = zvt_context.db_engine_map.get(engine_key)
    if not db_engine:
        db_engine = create_engine("sqlite:///" + db_path, echo=False)
        zvt_context.db_engine_map[engine_key] = db_engine
    return db_engine


def get_schemas(provider: str) -> List[DeclarativeMeta]:
    """
    get domain schemas supported by the provider

    :param provider: data provider
    :return: schemas provided by the provider
    """
    schemas = []
    for provider1, dbs in zvt_context.provider_map_dbnames.items():
        if provider == provider1:
            for dbname in dbs:
                schemas1 = zvt_context.dbname_map_schemas.get(dbname)
                if schemas1:
                    schemas += schemas1
    return schemas


def get_db_session(provider: str, db_name: str = None, data_schema: object = None, force_new: bool = False) -> Session:
    """
    get db session from (provider,db_name) or (provider,data_schema)

    :param provider: data provider
    :param db_name: db name
    :param data_schema: data schema
    :param force_new: True for new session, otherwise use global session
    :return: db session
    """
    if data_schema:
        db_name = _get_db_name(data_schema=data_schema)

    session_key = "{}_{}".format(provider, db_name)

    if force_new:
        return get_db_session_factory(provider, db_name, data_schema)()

    session = zvt_context.sessions.get(session_key)
    if not session:
        session = get_db_session_factory(provider, db_name, data_schema)()
        zvt_context.sessions[session_key] = session
    return session


def get_db_session_factory(provider: str, db_name: str = None, data_schema: object = None):
    """
    get db session factory from (provider,db_name) or (provider,data_schema)

    :param provider: data provider
    :param db_name: db name
    :param data_schema: data schema
    :return: db session factory
    """
    if data_schema:
        db_name = _get_db_name(data_schema=data_schema)

    session_key = "{}_{}".format(provider, db_name)
    session = zvt_context.db_session_map.get(session_key)
    if not session:
        session = sessionmaker()
        zvt_context.db_session_map[session_key] = session
    return session


def get_entity_schema(entity_type: str) -> Type[TradableEntity]:
    """
    get entity schema from name

    :param entity_type: entity type, e.g. stock, stockus.
    :return: the Schema of the entity
    """
    return zvt_context.tradable_schema_map[entity_type]


def get_schema_by_name(name: str) -> DeclarativeMeta:
    """
    get domain schema by the name

    :param name: schema name
    :return: schema
    """
    for schema in zvt_context.schemas:
        if schema.__name__ == name:
            return schema


def get_schema_columns(schema: DeclarativeMeta) -> List[str]:
    """
    get all columns of the domain schema

    :param schema: data schema
    :return: columns of the schema
    """
    return schema.__table__.columns.keys()


def common_filter(
    query: Query,
    data_schema,
    start_timestamp=None,
    end_timestamp=None,
    filters=None,
    order=None,
    limit=None,
    time_field="timestamp",
):
    """
    build filter by the arguments

    :param query: sql query
    :param data_schema: data schema
    :param start_timestamp: start timestamp
    :param end_timestamp: end timestamp
    :param filters: sql filters
    :param order: sql order
    :param limit: sql limit size
    :param time_field: time field in columns
    :return: result query
    """
    assert data_schema is not None
    time_col = eval("data_schema.{}".format(time_field))

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
    """
    delete data by filters

    :param data_schema: data schema
    :param filters: filters
    :param provider: data provider
    """
    if not provider:
        provider = data_schema.providers[0]

    session = get_db_session(provider=provider, data_schema=data_schema)
    query = session.query(data_schema)
    if filters:
        for f in filters:
            query = query.filter(f)
    query.delete()
    session.commit()


def get_one(data_schema, id: str, provider: str = None, session: Session = None):
    """
    get one record by id from data schema

    :param data_schema: data schema
    :param id: the record id
    :param provider: data provider
    :param session: db session
    :return: the record of the id
    """
    if "providers" not in data_schema.__dict__:
        logger.error("no provider registered for: {}", data_schema)
    if not provider:
        provider = data_schema.providers[0]

    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)

    return session.query(data_schema).get(id)


def get_data(
    data_schema: Type[Mixin],
    ids: List[str] = None,
    entity_ids: List[str] = None,
    entity_id: str = None,
    codes: List[str] = None,
    code: str = None,
    level: Union[IntervalLevel, str] = None,
    provider: str = None,
    columns: List = None,
    col_label: dict = None,
    return_type: str = "df",
    start_timestamp: Union[pd.Timestamp, str] = None,
    end_timestamp: Union[pd.Timestamp, str] = None,
    filters: List = None,
    session: Session = None,
    order=None,
    limit: int = None,
    index: Union[str, list] = None,
    drop_index_col=False,
    time_field: str = "timestamp",
):
    """
    query data by the arguments

    :param data_schema:
    :param ids:
    :param entity_ids:
    :param entity_id:
    :param codes:
    :param code:
    :param level:
    :param provider:
    :param columns:
    :param col_label: dict with key(column), value(label)
    :param return_type: df, domain or dict. default is df
    :param start_timestamp:
    :param end_timestamp:
    :param filters:
    :param session:
    :param order:
    :param limit:
    :param index: index field name, str for single index, str list for multiple index
    :param drop_index_col: whether drop the col if it's in index, default False
    :param time_field:
    :return: results basing on return_type.
    """
    if "providers" not in data_schema.__dict__:
        logger.error("no provider registered for: {}", data_schema)
    if not provider:
        provider = data_schema.providers[0]

    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)

    time_col = eval("data_schema.{}".format(time_field))

    if columns:
        # support str
        if type(columns[0]) == str:
            columns_ = []
            for col in columns:
                if isinstance(col, str):
                    columns_.append(eval("data_schema.{}".format(col)))
                else:
                    columns_.append(col)
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
            #: some schema has no level,just ignore it
            data_schema.level
            if type(level) == IntervalLevel:
                level = level.value
            query = query.filter(data_schema.level == level)
        except Exception as e:
            pass

    query = common_filter(
        query,
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        filters=filters,
        order=order,
        limit=limit,
        time_field=time_field,
    )

    if return_type == "df":
        df = pd.read_sql(query.statement, query.session.bind)
        if pd_is_not_null(df):
            if index:
                df = index_df(df, index=index, drop=drop_index_col, time_field=time_field)
        return df
    elif return_type == "domain":
        return query.all()
    elif return_type == "dict":
        return [item.__dict__ for item in query.all()]


def data_exist(session, schema, id):
    """
    whether exist data of the id

    :param session:
    :param schema:
    :param id:
    :return:
    """
    return session.query(exists().where(and_(schema.id == id))).scalar()


def get_data_count(data_schema, filters=None, session=None):
    """
    get record count basing on the filters

    :param data_schema:
    :param filters:
    :param session:
    :return:
    """
    query = session.query(data_schema)
    if filters:
        for filter in filters:
            query = query.filter(filter)

    count_q = query.statement.with_only_columns([func.count(data_schema.id)]).order_by(None)
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
    """
    decode entity id to entity_type, exchange, code

    :param entity_id:
    :return: tuple with format (entity_type, exchange, code)
    """
    result = entity_id.split("_")
    entity_type = result[0]
    exchange = result[1]
    code = "".join(result[2:])
    return entity_type, exchange, code


def get_entity_type(entity_id: str):
    """
    get entity type by entity id

    :param entity_id:
    :return: entity type
    """
    entity_type, _, _ = decode_entity_id(entity_id)
    return entity_type


def get_entity_exchange(entity_id: str):
    """
    get exchange by entity id

    :param entity_id:
    :return: exchange
    """
    _, exchange, _ = decode_entity_id(entity_id)
    return exchange


def get_entity_code(entity_id: str):
    """
    get code by entity id

    :param entity_id:
    :return: code
    """
    _, _, code = decode_entity_id(entity_id)
    return code


def df_to_db(
    df: pd.DataFrame,
    data_schema: DeclarativeMeta,
    provider: str,
    force_update: bool = False,
    sub_size: int = 5000,
    drop_duplicates: bool = True,
) -> object:
    """
    store the df to db

    :param df: data with columns of the schema
    :param data_schema: data schema
    :param provider: data provider
    :param force_update: whether update the data with id existed
    :param sub_size: update batch size
    :param drop_duplicates: whether drop duplicates
    :return:
    """
    if not pd_is_not_null(df):
        return 0

    if drop_duplicates and df.duplicated(subset="id").any():
        logger.warning(f"remove duplicated:{df[df.duplicated()]}")
        df = df.drop_duplicates(subset="id", keep="last")

    db_engine = get_db_engine(provider, data_schema=data_schema)

    schema_cols = get_schema_columns(data_schema)
    cols = set(df.columns.tolist()) & set(schema_cols)

    if not cols:
        print("wrong cols")
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
        df_current = df.iloc[sub_size * step : sub_size * (step + 1)]
        if force_update:
            session = get_db_session(provider=provider, data_schema=data_schema)
            ids = df_current["id"].tolist()
            if len(ids) == 1:
                sql = f'delete from `{data_schema.__tablename__}` where id = "{ids[0]}"'
            else:
                sql = f"delete from `{data_schema.__tablename__}` where id in {tuple(ids)}"

            session.execute(sql)
            session.commit()

        else:
            current = get_data(
                data_schema=data_schema, columns=[data_schema.id], provider=provider, ids=df_current["id"].tolist()
            )
            if pd_is_not_null(current):
                df_current = df_current[~df_current["id"].isin(current["id"])]

        if pd_is_not_null(df_current):
            saved = saved + len(df_current)
            df_current.to_sql(data_schema.__tablename__, db_engine, index=False, if_exists="append")

    return saved


def get_entities(
    entity_schema: Type[TradableEntity] = None,
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
    return_type: str = "df",
    start_timestamp: Union[pd.Timestamp, str] = None,
    end_timestamp: Union[pd.Timestamp, str] = None,
    filters: List = None,
    session: Session = None,
    order=None,
    limit: int = None,
    index: Union[str, list] = "code",
) -> List:
    """
    get entities by the arguments

    :param entity_schema:
    :param entity_type:
    :param exchanges:
    :param ids:
    :param entity_ids:
    :param entity_id:
    :param codes:
    :param code:
    :param provider:
    :param columns:
    :param col_label:
    :param return_type:
    :param start_timestamp:
    :param end_timestamp:
    :param filters:
    :param session:
    :param order:
    :param limit:
    :param index:
    :return:
    """
    if not entity_schema:
        entity_schema = zvt_context.tradable_schema_map[entity_type]

    if not provider:
        provider = entity_schema.providers[0]

    if not order:
        order = entity_schema.code.asc()

    if exchanges:
        if filters:
            filters.append(entity_schema.exchange.in_(exchanges))
        else:
            filters = [entity_schema.exchange.in_(exchanges)]

    return get_data(
        data_schema=entity_schema,
        ids=ids,
        entity_ids=entity_ids,
        entity_id=entity_id,
        codes=codes,
        code=code,
        level=None,
        provider=provider,
        columns=columns,
        col_label=col_label,
        return_type=return_type,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        filters=filters,
        session=session,
        order=order,
        limit=limit,
        index=index,
    )


def get_entity_ids(
    entity_type="stock", entity_schema: TradableEntity = None, exchanges=None, codes=None, provider=None, filters=None
):
    """
    get entity ids by the arguments

    :param entity_type:
    :param entity_schema:
    :param exchanges:
    :param codes:
    :param provider:
    :param filters:
    :return:
    """
    df = get_entities(
        entity_type=entity_type,
        entity_schema=entity_schema,
        exchanges=exchanges,
        codes=codes,
        provider=provider,
        filters=filters,
    )
    if pd_is_not_null(df):
        return df["entity_id"].to_list()
    return None


if __name__ == "__main__":
    print(get_entities(entity_type="block"))
# the __all__ is generated
__all__ = [
    "_get_db_name",
    "get_db_engine",
    "get_schemas",
    "get_db_session",
    "get_db_session_factory",
    "get_entity_schema",
    "get_schema_by_name",
    "get_schema_columns",
    "common_filter",
    "del_data",
    "get_one",
    "get_data",
    "data_exist",
    "get_data_count",
    "get_group",
    "decode_entity_id",
    "get_entity_type",
    "get_entity_exchange",
    "get_entity_code",
    "df_to_db",
    "get_entities",
    "get_entity_ids",
]
