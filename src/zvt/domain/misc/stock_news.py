# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, JSON, Boolean, DateTime, Integer
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

NewsBase = declarative_base()


class StockNews(NewsBase, Mixin):
    __tablename__ = "stock_news"

    #: 新闻编号
    news_code = Column(String)
    #: 新闻地址
    news_url = Column(String)
    #: 新闻标题
    news_title = Column(String)
    #: 新闻内容
    news_content = Column(String)
    #: 新闻解读
    news_analysis = Column(JSON)
    #: 用户设置为忽略
    ignore_by_user = Column(Boolean, default=False)


class StockHotTopic(NewsBase, Mixin):
    __tablename__ = "stock_hot_topic"

    #: 出现时间
    created_timestamp = Column(DateTime)
    #: 热度排行
    position = Column(Integer)
    #: 相关标的
    entity_ids = Column(JSON)

    #: 新闻编号
    news_code = Column(String)
    #: 新闻标题
    news_title = Column(String)
    #: 新闻内容
    news_content = Column(String)
    #: 新闻解读
    news_analysis = Column(JSON)


register_schema(providers=["em"], db_name="stock_news", schema_base=NewsBase, entity_type="stock")


# the __all__ is generated
__all__ = ["StockNews", "StockHotTopic"]
