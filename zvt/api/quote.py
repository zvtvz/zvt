# -*- coding: utf-8 -*-
from typing import Union, List

from zvt.core import IntervalLevel, Mixin
from zvt.core.api import get_entities, decode_entity_id
from zvt.core.contract import get_db_session
from zvt.api.common import get_kdata_schema
from zvt.domain import BlockCategory, BlockMoneyFlow
from zvt.domain.meta.stock_meta import Index


def get_securities_in_blocks(provider: str = 'eastmoney',
                             categories: List[Union[str, BlockCategory]] = ['concept', 'industry'],
                             names=None, codes=None, ids=None):
    session = get_db_session(provider=provider, data_schema=Index)

    categories = [BlockCategory(category).value for category in categories]

    filters = [Index.category.in_(categories)]

    # add name filters
    if names:
        filters.append(Index.name.in_(names))

    blocks = get_entities(entity_ids=ids, codes=codes, entity_type='index', provider=provider,
                          filters=filters, return_type='domain', session=session)
    securities = []
    for block in blocks:
        securities += [item.stock_id for item in block.stocks]

    return securities


def get_kdata(entity_id=None, level=IntervalLevel.LEVEL_1DAY.value, provider='joinquant', columns=None,
              return_type='df', start_timestamp=None, end_timestamp=None,
              filters=None, session=None, order=None, limit=None, index='timestamp'):
    entity_type, exchange, code = decode_entity_id(entity_id)
    data_schema: Mixin = get_kdata_schema(entity_type, level=level)

    return data_schema.query_data(entity_id=entity_id, level=level, provider=provider,
                                  columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                                  end_timestamp=end_timestamp, filters=filters, session=session, order=order,
                                  limit=limit,
                                  index=index)

if __name__ == '__main__':
    money_flow_session = get_db_session(provider='sina', data_schema=BlockMoneyFlow)

    entities = get_entities(entity_type='index',
                            return_type='domain', provider='sina',
                            # 只抓概念和行业
                            filters=[Index.category.in_(
                                [BlockCategory.industry.value, BlockCategory.concept.value])])

    for entity in entities:
        sql = 'UPDATE index_money_flow SET name="{}" where code="{}"'.format(
            entity.name, entity.code)
        money_flow_session.execute(sql)
        money_flow_session.commit()
