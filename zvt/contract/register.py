# -*- coding: utf-8 -*-
import logging
from typing import List

import sqlalchemy
from sqlalchemy.ext.declarative import DeclarativeMeta

from zvt.contract import EntityMixin, zvt_context, Mixin
from zvt.contract.api import get_db_engine, get_db_session_factory
from zvt.utils.utils import add_to_map_list

logger = logging.getLogger(__name__)


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

            if entity_type_ not in zvt_context.entity_types:
                zvt_context.entity_types.append(entity_type_)
            zvt_context.entity_schema_map[entity_type_] = cls
        return cls

    return register


def register_schema(providers: List[str],
                    db_name: str,
                    schema_base: DeclarativeMeta,
                    entity_type: str = None):
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
            # register provider to the schema
            for provider in providers:
                if issubclass(cls, Mixin):
                    cls.register_provider(provider)

            if zvt_context.dbname_map_schemas.get(db_name):
                schemas = zvt_context.dbname_map_schemas[db_name]
            zvt_context.schemas.append(cls)
            if entity_type:
                add_to_map_list(the_map=zvt_context.entity_map_schemas, key=entity_type, value=cls)
            schemas.append(cls)

    zvt_context.dbname_map_schemas[db_name] = schemas

    for provider in providers:
        # track in in  _providers
        if provider not in zvt_context.providers:
            zvt_context.providers.append(provider)

        if not zvt_context.provider_map_dbnames.get(provider):
            zvt_context.provider_map_dbnames[provider] = []
        zvt_context.provider_map_dbnames[provider].append(db_name)
        zvt_context.dbname_map_base[db_name] = schema_base

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
                    index_name = '{}_{}_index'.format(table_name, col)
                    if index_name not in index_list:
                        index = sqlalchemy.schema.Index(index_name, column)
                        index.create(engine)
            for cols in [('timestamp', 'entity_id'), ('timestamp', 'code')]:
                if (cols[0] in table.c) and (col[1] in table.c):
                    column0 = eval('table.c.{}'.format(col[0]))
                    column1 = eval('table.c.{}'.format(col[1]))
                    index_name = '{}_{}_{}_index'.format(table_name, col[0], col[1])
                    if index_name not in index_list:
                        index = sqlalchemy.schema.Index(index_name, column0,
                                                        column1)
                        index.create(engine)
