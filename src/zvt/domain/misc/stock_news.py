# -*- coding: utf-8 -*-
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

NewsBase = declarative_base()


class StockNews(NewsBase, Mixin):
    __tablename__ = "stock_news"

    #: 新闻标题
    news_title = Column(String)


register_schema(providers=["em"], db_name="stock_news", schema_base=NewsBase, entity_type="stock")
# the __all__ is generated
__all__ = ["StockNews"]
