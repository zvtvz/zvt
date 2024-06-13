# -*- coding: utf-8 -*-


class Registry(object):
    """
    Class storing zvt registering meta
    """

    def __init__(self) -> None:
        #: all registered providers
        self.providers = []

        #: all registered entity types(str)
        self.tradable_entity_types = []

        #: all entity schemas
        self.tradable_entity_schemas = []

        #: all registered schemas
        self.schemas = []

        #: tradable entity  type -> schema
        self.tradable_schema_map = {}

        #: global sessions
        self.sessions = {}

        #: provider_dbname -> engine
        self.db_engine_map = {}

        #: provider_dbname -> session
        self.db_session_map = {}

        #: provider -> [db_name1,db_name2...]
        self.provider_map_dbnames = {}

        #: db_name -> [declarative_base1,declarative_base2...]
        self.dbname_map_base = {}

        #: db_name -> [declarative_meta1,declarative_meta2...]
        self.dbname_map_schemas = {}

        #: entity_type -> related schemas
        self.entity_map_schemas = {}

        #: factor class registry
        self.factor_cls_registry = {}


#: :class:`~.zvt.contract.context.Registry` instance
zvt_context = Registry()


# the __all__ is generated
__all__ = ["Registry"]
