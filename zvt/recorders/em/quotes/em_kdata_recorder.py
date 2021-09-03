# -*- coding: utf-8 -*-

from zvt.api.kdata import get_kdata_schema
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Stock, Index, Block, StockKdataCommon, IndexKdataCommon, StockhkKdataCommon, StockusKdataCommon
from zvt.domain.meta.stockhk_meta import Stockhk
from zvt.domain.meta.stockus_meta import Stockus
from zvt.recorders.em.em_api import get_kdata
from zvt.utils import pd_is_not_null


class BaseEMStockKdataRecorder(FixedCycleDataRecorder):
    default_size = 50000
    entity_provider: str = 'eastmoney'

    provider = 'em'

    def __init__(self,
                 force_update=True,
                 sleeping_time=10,
                 exchanges=None,
                 entity_ids=None,
                 code=None,
                 codes=None,
                 day_data=False,
                 entity_filters=None,
                 ignore_failed=True,
                 real_time=False,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 level=IntervalLevel.LEVEL_1DAY,
                 kdata_use_begin_time=False,
                 one_day_trading_minutes=24 * 60,
                 adjust_type=AdjustType.qfq) -> None:
        level = IntervalLevel(level)
        self.adjust_type = AdjustType(adjust_type)
        self.entity_type = self.entity_schema.__name__.lower()

        self.data_schema = get_kdata_schema(entity_type=self.entity_type, level=level, adjust_type=self.adjust_type)

        super().__init__(force_update, sleeping_time, exchanges, entity_ids, code, codes, day_data, entity_filters,
                         ignore_failed, real_time, fix_duplicate_way, start_timestamp, end_timestamp, level,
                         kdata_use_begin_time, one_day_trading_minutes)

    def record(self, entity, start, end, size, timestamps):
        df = get_kdata(entity_id=entity.id, limit=size, adjust_type=self.adjust_type)
        if pd_is_not_null(df):
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        else:
            self.logger.info(f'no kdata for {entity.id}')


class EMStockKdataRecorder(BaseEMStockKdataRecorder):
    entity_schema = Stock
    data_schema = StockKdataCommon


class EMStockusKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = 'em'
    entity_schema = Stockus
    data_schema = StockusKdataCommon


class EMStockhkKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = 'em'
    entity_schema = Stockhk
    data_schema = StockhkKdataCommon


class EMIndexKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    data_schema = IndexKdataCommon


class EMBlockKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = 'eastmoney'
    entity_schema = Block

    data_schema = IndexKdataCommon


if __name__ == '__main__':
    recorder = EMIndexKdataRecorder(level=IntervalLevel.LEVEL_1DAY, codes=['000300'])
    recorder.run()
# the __all__ is generated
__all__ = ['BaseEMStockKdataRecorder', 'EMStockKdataRecorder', 'EMStockusKdataRecorder', 'EMStockhkKdataRecorder',
           'EMIndexKdataRecorder', 'EMBlockKdataRecorder']
