# -*- coding: utf-8 -*-
import logging
import os
from typing import List

from sqlalchemy import create_engine, schema
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker, Session

from zvdata import EntityMixin
from zvdata.utils.utils import add_to_map_list

logger = logging.getLogger(__name__)

# all registered providers
global_providers = []

# all registered entity types
global_entity_types = []

# all registered schemas
global_schemas = []

# entity_type -> schema
global_entity_schema = {

}

# global sessions
global_sessions = {}

# provider_dbname -> engine
_db_engine_map = {}

# provider_dbname -> session
_db_session_map = {}

# provider -> [db_name1,db_name2...]
_provider_map_dbnames = {
}

# db_name -> [declarative_base1,declarative_base2...]
_dbname_map_base = {
}

# db_name -> [declarative_meta1,declarative_meta2...]
_dbname_map_schemas = {
}

# entity_type -> schema
_entity_map_schemas = {

}

zvdata_env = {}


def init_data_env(data_path: str, domain_module: str) -> None:
    """
    now we just support sqlite engine for storing the data,you need to set the path for the db

    :param data_path: the db file path
    :type data_path:
    :param domain_module: the module name of your domains
    :type domain_module:
    """
    zvdata_env['data_path'] = data_path
    zvdata_env['domain_module'] = domain_module

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    zvdata_env['api_dir'] = os.path.join(data_path, 'api')
    if not os.path.exists(zvdata_env['api_dir']):
        os.makedirs(zvdata_env['api_dir'])


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


def enum_value(x):
    return [e.value for e in x]


def get_db_name(data_schema: DeclarativeMeta) -> str:
    """
    get db name of the domain schema

    :param data_schema:
    :type data_schema:
    :return:
    :rtype:
    """
    for db_name, base in _dbname_map_base.items():
        if issubclass(data_schema, base):
            return db_name


def get_db_engine(provider: str,
                  db_name: str = None,
                  data_schema: object = None) -> Engine:
    """
    get db engine of the (provider,db_name) or (provider,data_schema)


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

    db_path = os.path.join(zvdata_env['data_path'], '{}_{}.db?check_same_thread=False'.format(provider, db_name))

    engine_key = '{}_{}'.format(provider, db_name)
    db_engine = _db_engine_map.get(engine_key)
    if not db_engine:
        db_engine = create_engine('sqlite:///' + db_path, echo=False)
        _db_engine_map[engine_key] = db_engine
    return db_engine


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

    session = global_sessions.get(session_key)
    if not session:
        session = get_db_session_factory(provider, db_name, data_schema)()
        global_sessions[session_key] = session
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
    session = _db_session_map.get(session_key)
    if not session:
        session = sessionmaker()
        _db_session_map[session_key] = session
    return session


def get_providers():
    return global_providers


def get_schemas(provider: str) -> List[DeclarativeMeta]:
    """
    get domain schemas supported by the provider

    :param provider:
    :type provider:
    :return:
    :rtype:
    """
    schemas = []
    for provider1, dbs in _provider_map_dbnames.items():
        if provider == provider1:
            for dbname in dbs:
                schemas1 = _dbname_map_schemas.get(dbname)
                if schemas1:
                    schemas += schemas1
    return schemas


def get_entity_types():
    return global_entity_types


def get_schema_by_name(name: str) -> DeclarativeMeta:
    """
    get domain schema by the name

    :param name:
    :type name:
    :return:
    :rtype:
    """
    for schema in global_schemas:
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


api_header = '''
# -*- coding: utf-8 -*-
# this file is generated by register_api function, dont't change it

from typing import List, Union

import pandas as pd
from sqlalchemy.orm import Session
from zvdata.api import get_data
from zvdata import IntervalLevel
'''
api_template = '''
{}

def get_{}(
        entity_ids: List[str] = None,
        entity_id: str = None,
        codes: List[str] = None,
        level: Union[IntervalLevel, str] = None,
        provider: str = \'{}\',
        columns: List = None,
        return_type: str = 'df',
        start_timestamp: Union[pd.Timestamp, str] = None,
        end_timestamp: Union[pd.Timestamp, str] = None,
        filters: List = None,
        session: Session = None,
        order=None,
        limit: int = None,
        index: str = 'timestamp',
        time_field: str = 'timestamp'):
    return get_data(data_schema={}, entity_ids=entity_ids, entity_id=entity_id, codes=codes, level=level,
                    provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit,
                    index=index, time_field=time_field)
'''


def register_api(provider: str) -> object:
    """
    decorator for registering api of the domain

    :param provider:
    :type provider:
    :return:
    :rtype:
    """

    def generate(cls):
        import_str = 'from {} import {}'.format(zvdata_env['domain_module'], cls.__name__)
        the_func = api_template.format(import_str, cls.__tablename__, provider, cls.__name__)

        with open(os.path.join(zvdata_env['api_dir'], f'{cls.__tablename__}.api'), "w") as myfile:
            myfile.write(the_func)
            myfile.write('\n')

        return cls

    return generate


def generate_api(api_path: str) -> object:
    """
    function for generate api.py for the register_api domain

    :param api_path:
    :type api_path:
    """
    from os import listdir
    from os.path import isfile, join
    api_files = [os.path.join(zvdata_env['api_dir'], f) for f in listdir(zvdata_env['api_dir']) if
                 isfile(join(zvdata_env['api_dir'], f)) and f.endswith('.api')]
    with open(os.path.join(api_path, 'api.py'), 'w') as outfile:
        outfile.write(api_header)

        for api_file in api_files:
            with open(api_file) as infile:
                outfile.write(infile.read())
            os.remove(api_file)


def register_entity(entity_type: str = None):
    """
    function for register entity type

    :param entity_type:
    :type entity_type:
    :return:
    :rtype:
    """

    def register(cls):
        # register the entity
        if issubclass(cls, EntityMixin):
            entity_type_ = entity_type
            if not entity_type:
                entity_type_ = cls.__name__.lower()

            if entity_type_ not in global_entity_types:
                global_entity_types.append(entity_type_)
            global_entity_schema[entity_type_] = cls

            add_to_map_list(the_map=_entity_map_schemas, key=entity_type, value=cls)
        return cls

    return register


def register_schema(providers: List[str],
                    db_name: str,
                    schema_base: DeclarativeMeta,
                    entity_type: str = 'stock'):
    """
    function for register schema,please declare them before register

    :param providers: the supported providers for the schema
    :type providers:
    :param db_name: database name for the schema
    :type db_name:
    :param schema_base:
    :type schema_base:
    :param entity_type: the schema related entity_type
    :type entity_type:
    :return:
    :rtype:
    """
    schemas = []
    for item in schema_base._decl_class_registry.items():
        cls = item[1]
        if type(cls) == DeclarativeMeta:
            if _dbname_map_schemas.get(db_name):
                schemas = _dbname_map_schemas[db_name]
            global_schemas.append(cls)
            add_to_map_list(the_map=_entity_map_schemas, key=entity_type, value=cls)
            schemas.append(cls)

    _dbname_map_schemas[db_name] = schemas

    for provider in providers:
        # track in in  _providers
        if provider not in global_providers:
            global_providers.append(provider)

        if not _provider_map_dbnames.get(provider):
            _provider_map_dbnames[provider] = []
        _provider_map_dbnames[provider].append(db_name)
        _dbname_map_base[db_name] = schema_base

        # create the db & table
        engine = get_db_engine(provider, db_name=db_name)
        schema_base.metadata.create_all(engine)

        session_fac = get_db_session_factory(provider, db_name=db_name)
        session_fac.configure(bind=engine)

    for provider in providers:
        engine = get_db_engine(provider, db_name=db_name)

        # create index for 'timestamp','entity_id','code','report_period','updated_timestamp
        for table_name, table in iter(schema_base.metadata.tables.items()):
            index_list = []
            with engine.connect() as con:
                rs = con.execute("PRAGMA INDEX_LIST('{}')".format(table_name))
                for row in rs:
                    index_list.append(row[1])

            logger.debug('engine:{},table:{},index:{}'.format(engine, table_name, index_list))

            for col in ['timestamp', 'entity_id', 'code', 'report_period', 'created_timestamp', 'updated_timestamp']:
                if col in table.c:
                    column = eval('table.c.{}'.format(col))
                    index = schema.Index('{}_{}_index'.format(table_name, col), column)
                    if index.name not in index_list:
                        index.create(engine)
            for cols in [('timestamp', 'entity_id'), ('timestamp', 'code')]:
                if (cols[0] in table.c) and (col[1] in table.c):
                    column0 = eval('table.c.{}'.format(col[0]))
                    column1 = eval('table.c.{}'.format(col[1]))
                    index = schema.Index('{}_{}_{}_index'.format(table_name, col[0], col[1]), column0, column1)
                    if index.name not in index_list:
                        index.create(engine)
