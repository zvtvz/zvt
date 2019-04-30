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


def get_db_engine(store_category):
    if isinstance(store_category, StoreCategory):
        store_category = store_category.value

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    db_path = os.path.join(DATA_PATH, '{}.db'.format(store_category))

    db_engine = _db_engine_map.get(store_category)
    if not db_engine:
        from sqlalchemy import create_engine
        db_engine = create_engine('sqlite:///' + db_path, echo=False)
        _db_engine_map[store_category] = db_engine
    return db_engine


def get_db_session(store_category) -> Session:
    return get_db_session_factory(store_category)()


def get_db_session_factory(store_category):
    session = _db_session_map.get(store_category)
    if not session:
        session = sessionmaker()
        _db_session_map[store_category] = session
    return session


def init_schema():
    for store_category in StoreCategory:
        engine = get_db_engine(store_category)
        store_map_base.get(store_category).metadata.create_all(engine)

        Session = get_db_session_factory(store_category)
        Session.configure(bind=engine)
