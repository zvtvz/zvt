# -*- coding: utf-8 -*-
import json

from zvt.api import china_stock_code_to_id
from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract.api import decode_entity_id, get_db_session
from zvt.domain import LimitUpInfo, Stock


def get_limit_up_reasons(entity_id):
    info = LimitUpInfo.query_data(
        entity_id=entity_id, order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain"
    )

    topics = []
    if info and info[0].reason:
        topics = topics + info[0].reason.split("+")
    return topics


def build_stock_tags_from_limit_up():
    normal_stock_ids = get_entity_ids_by_filter(
        provider="em", ignore_delist=True, ignore_st=False, ignore_new_stock=False
    )
    for entity_id in normal_stock_ids:
        tags = get_limit_up_reasons(entity_id=entity_id)
        for tag in tags:
            tag_stock(entity_id=entity_id, tag=tag, core_tag=False)


def tag_stock(entity_id=None, code=None, name=None, tag=None, reason=None, provider="em", core_tag=True):
    session = get_db_session(provider=provider, data_schema=Stock)
    if not entity_id:
        if code:
            entity_id = china_stock_code_to_id(code=code)

    stock = Stock.get_by_id(provider=provider, id=entity_id)
    if name:
        assert stock.name == name

    if stock:
        if stock.tags:
            tags = json.loads(stock.tags)
            if not reason:
                reason = tags.get(tag)
        else:
            tags = {}
        tags[tag] = reason

        stock.tags = json.dumps(tags, ensure_ascii=False)
        if core_tag:
            stock.core_tag = json.dumps({tag: reason}, ensure_ascii=False)
        session.add(stock)
        session.commit()


def get_stock_tags(entity_id=None, code=None, tags_only=False, provider="em"):
    if not entity_id:
        if code:
            entity_id = china_stock_code_to_id(code=code)

    stock = Stock.query_data(provider=provider, entity_id=entity_id, return_type="domain")
    if stock and stock[0].tags:
        tags = json.loads(stock[0].tags)
        if tags_only:
            return list(tags.keys())
        return tags


def get_stock_core_tag(entity_id, provider="em"):
    stock = Stock.query_data(provider=provider, entity_id=entity_id, return_type="domain")
    if stock and stock[0].core_tag:
        return json.loads(stock[0].core_tag)
