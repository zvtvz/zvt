from typing import List, Union, Type

import pandas as pd

from zvt.api.quote import get_kdata_schema
from zvt.contract import IntervalLevel, EntityMixin, AdjustType
from zvt.contract.factor import Factor, Transformer, Accumulator, FactorMeta
from zvt.domain import Stock


class TechnicalFactor(Factor, metaclass=FactorMeta):
    def __init__(self,
                 entity_schema: Type[EntityMixin] = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 dry_run: bool = False,
                 factor_name: str = None,
                 clear_state: bool = False,
                 not_load_data: bool = False,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        if columns is None:
            columns = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low']

        # 股票默认使用后复权
        if entity_schema == Stock and not adjust_type:
            adjust_type = AdjustType.hfq

        self.adjust_type = adjust_type
        self.data_schema = get_kdata_schema(entity_schema.__name__, level=level, adjust_type=adjust_type)

        if not factor_name:
            if type(level) == str:
                factor_name = f'{type(self).__name__.lower()}_{level}'
            else:
                factor_name = f'{type(self).__name__.lower()}_{level.value}'

        super().__init__(self.data_schema, entity_schema, provider, entity_provider, entity_ids, exchanges, codes,
                         the_timestamp, start_timestamp, end_timestamp, columns, filters, order, limit, level,
                         category_field, time_field, computing_window, keep_all_timestamp, fill_method,
                         effective_number, transformer, accumulator, need_persist, dry_run, factor_name, clear_state,
                         not_load_data)


# the __all__ is generated
__all__ = ['TechnicalFactor']
