# -*- coding: utf-8 -*-
import os

from zvt.domain.account import *
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

    session_key = '{}_{}'.format(provider, store_category.value)
    session = _db_session_map.get(session_key)
    if not session:
        session = sessionmaker()
        _db_session_map[session_key] = session
    return session


def init_schema():
    for provider in Provider:
        dbs = provider_map_category.get(provider)
        if dbs:
            for store_category in dbs:
                engine = get_db_engine(provider, store_category)
                category_map_db.get(store_category).metadata.create_all(engine)

                Session = get_db_session_factory(provider, store_category)
                Session.configure(bind=engine)
