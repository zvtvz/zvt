# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

EventsBase = declarative_base()


class StockEvents(EventsBase, Mixin):
    __tablename__ = "stock_events"
    event_type = Column(String)
    specific_event_type = Column(String)
    notice_date = Column(DateTime)
    level1_content = Column(String)
    level2_content = Column(String)


register_schema(providers=["em"], db_name="stock_events", schema_base=EventsBase, entity_type="stock")
# the __all__ is generated
__all__ = ["StockEvents"]
