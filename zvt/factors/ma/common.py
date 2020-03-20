# -*- coding: utf-8 -*-
import logging

from zvdata import IntervalLevel
from zvdata.api import get_entities
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.domain import Stock
from zvt.factors.ma.ma_factor import MaFactor
from zvt.factors.ma.ma_stats import MaStateStatsFactor

logger = logging.getLogger(__name__)


def cal_ma_states(start='000001', end='002000'):
    logger.info(f'start cal day ma stats {start}:{end}')

    entities = get_entities(provider='eastmoney', entity_type='stock', columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    ma_1d_stats = MaStateStatsFactor(codes=codes, start_timestamp='2005-01-01',
                                     end_timestamp=now_pd_timestamp(),
                                     level=IntervalLevel.LEVEL_1DAY)

    ma_1d_factor = MaFactor(codes=codes, start_timestamp='2005-01-01',
                            end_timestamp=now_pd_timestamp(),
                            level=IntervalLevel.LEVEL_1DAY)

    logger.info(f'finish cal day ma stats {start}:{end}')

    ma_1wk_stats = MaStateStatsFactor(codes=codes, start_timestamp='2005-01-01',
                                      end_timestamp=now_pd_timestamp(),
                                      level=IntervalLevel.LEVEL_1WEEK)

    logger.info(f'finish cal week ma stats {start}:{end}')
