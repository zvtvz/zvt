# -*- coding: utf-8 -*-
from typing import Union, List

from zvdata import IntervalLevel, Mixin
from zvdata.api import get_entities, decode_entity_id
from zvdata.contract import get_db_session
from zvt.accounts.ccxt_account import CCXTAccount
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


def get_current_price(entity_ids=None, entity_type='coin'):
    result = {}
    if entity_type == 'coin':
        if entity_ids:
            for entity_id in entity_ids:
                a, exchange, code = decode_entity_id(entity_id)
                assert a == entity_type
                ccxt_exchange = CCXTAccount.get_ccxt_exchange(exchange_str=exchange)

                if not ccxt_exchange:
                    raise Exception('{} not support'.format(exchange))

                orderbook = ccxt_exchange.fetch_order_book(code)

                bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
                ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
                entity_id = f'coin_{exchange}_{code}'
                result[entity_id] = (bid, ask)

    return result


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
