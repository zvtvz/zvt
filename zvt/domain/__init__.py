# -*- coding: utf-8 -*-
import logging
import os

from sqlalchemy import schema

from zvt.domain.business import *
from zvt.domain.coin_meta import *
from zvt.domain.common import *
from zvt.domain.dividend_financing import *
from zvt.domain.finance import *
from zvt.domain.holder import *
from zvt.domain.macro import *
from zvt.domain.meta import *
from zvt.domain.money_flow import *
from zvt.domain.quote import *
from zvt.domain.trading import *
from zvt.settings import DATA_PATH

logger = logging.getLogger(__name__)

_db_engine_map = {}
_db_session_map = {}

from sqlalchemy.orm import sessionmaker, Session


def get_db_engine(provider, store_category):
    if isinstance(store_category, StoreCategory):
        store_category = store_category.value
    if isinstance(provider, Provider):
        provider = provider.value

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    db_path = os.path.join(DATA_PATH, '{}_{}.db'.format(provider, store_category))

    engine_key = '{}_{}'.format(provider, store_category)
    db_engine = _db_engine_map.get(engine_key)
    if not db_engine:
        from sqlalchemy import create_engine
        db_engine = create_engine('sqlite:///' + db_path, echo=False)
        _db_engine_map[engine_key] = db_engine
    return db_engine


def get_db_session(provider, store_category) -> Session:
    return get_db_session_factory(provider, store_category)()


def get_db_session_factory(provider, store_category):
    if isinstance(provider, Provider):
        provider = provider.value
    if isinstance(store_category, StoreCategory):
        store_category = store_category.value

    session_key = '{}_{}'.format(provider, store_category)
    session = _db_session_map.get(session_key)
    if not session:
        session = sessionmaker()
        _db_session_map[session_key] = session
    return session


def init_schema():
    # create table at first
    for provider in Provider:
        dbs = provider_map_category.get(provider)
        if dbs:
            for store_category in dbs:
                engine = get_db_engine(provider, store_category)
                category_map_db.get(store_category).metadata.create_all(engine)

                Session = get_db_session_factory(provider, store_category)
                Session.configure(bind=engine)

    # create index
    for provider in Provider:
        dbs = provider_map_category.get(provider)
        if dbs:
            for store_category in dbs:
                engine = get_db_engine(provider, store_category)
                # create index for 'timestamp','security_id','code','report_period
                for table_name, table in iter(category_map_db.get(store_category).metadata.tables.items()):
                    index_list = []
                    with engine.connect() as con:
                        rs = con.execute("PRAGMA INDEX_LIST('{}')".format(table_name))
                        for row in rs:
                            index_list.append(row[1])

                    logger.debug('engine:{},table:{},index:{}'.format(engine, table_name, index_list))

                    for col in ['timestamp', 'security_id', 'code', 'report_period']:
                        if col in table.c:
                            column = eval('table.c.{}'.format(col))
                            index = schema.Index('{}_{}_index'.format(table_name, col), column)
                            if index.name not in index_list:
                                index.create(engine)
                    for cols in [('timestamp', 'security_id'), ('timestamp', 'code')]:
                        if (cols[0] in table.c) and (col[1] in table.c):
                            column0 = eval('table.c.{}'.format(col[0]))
                            column1 = eval('table.c.{}'.format(col[1]))
                            index = schema.Index('{}_{}_{}_index'.format(table_name, col[0], col[1]), column0, column1)
                            if index.name not in index_list:
                                index.create(engine)


init_schema()

if __name__ == '__main__':
    init_schema()
