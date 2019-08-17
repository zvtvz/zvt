# -*- coding: utf-8 -*-
from zvdata.api import get_entities, decode_entity_id, get_data
from zvdata.domain import get_db_session
from zvdata.structs import IntervalLevel

from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import get_kdata_schema
from zvt.domain.stock_meta import Index


def get_securities_in_blocks(block_names=['HS300_'], block_category='concept', provider='eastmoney'):
    session = get_db_session(provider=provider, data_schema=Index)

    filters = [Index.category == block_category]
    name_filters = None
    for block_name in block_names:
        if name_filters:
            name_filters |= (Index.name == block_name)
        else:
            name_filters = (Index.name == block_name)
    filters.append(name_filters)
    blocks = get_entities(entity_type='index', provider='eastmoney',
                          filters=filters, return_type='domain', session=session)
    securities = []
    for block in blocks:
        securities += [item.stock_id for item in block.stocks]

    return securities


def get_kdata(entity_id, level=IntervalLevel.LEVEL_1DAY.value, provider='eastmoney', columns=None,
              return_type='df', start_timestamp=None, end_timestamp=None,
              filters=None, session=None, order=None, limit=None):
    entity_type, exchange, code = decode_entity_id(entity_id)
    data_schema = get_kdata_schema(entity_type, level=level)

    return get_data(data_schema=data_schema, entity_id=entity_id, level=level, provider=provider, columns=columns,
                    return_type=return_type,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


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
    get_entities(provider='linkedin', entity_type='user', limit=10)
