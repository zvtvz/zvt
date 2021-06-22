# -*- coding: utf-8 -*-

# all registered providers
providers = []

# all registered entity types(str)
tradable_entity_types = []

# all entity schemas
entity_schemas = []

# all registered schemas
schemas = []

# tradable entity  type -> schema
tradable_schema_map = {}

# global sessions
sessions = {}

# provider_dbname -> engine
db_engine_map = {}

# provider_dbname -> session
db_session_map = {}

# provider -> [db_name1,db_name2...]
provider_map_dbnames = {}

# db_name -> [declarative_base1,declarative_base2...]
dbname_map_base = {}

# db_name -> [declarative_meta1,declarative_meta2...]
dbname_map_schemas = {}

# entity_type -> related schemas
entity_map_schemas = {}

# factor class registry
factor_cls_registry = {}
