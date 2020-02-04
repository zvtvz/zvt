# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvdata.utils.pd_utils import normal_index_df
from zvt.domain import BlockMoneyFlow, Block, BlockCategory
from zvt.factors import ScoreFactor, Union, Scorer
from zvt.factors.algorithm import RankScorer


#     # 净流入
#     net_inflows = Column(Float)
#     # 净流入率
#     net_inflow_rate = Column(Float)
#
#     # 主力=超大单+大单
#     net_main_inflows = Column(Float)
#     net_main_inflow_rate = Column(Float)
class BlockMoneyFlowFactor(ScoreFactor):
    def __init__(self,
                 provider: str = 'sina',
                 entity_provider: str = 'sina',
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [BlockMoneyFlow.net_inflows, BlockMoneyFlow.net_main_inflows],
                 category=BlockCategory.industry.value,
                 window=20,
                 scorer: Scorer = RankScorer(ascending=True)) -> None:
        df = Block.query_data(provider=entity_provider, filters=[Block.category == category])
        entity_ids = df['entity_id'].tolist()
        self.window = window
        super().__init__(BlockMoneyFlow, Block, provider=provider, entity_provider=entity_provider,
                         entity_ids=entity_ids, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                         end_timestamp=end_timestamp, columns=columns, scorer=scorer)

    def pre_compute(self):
        super().pre_compute()
        self.pipe_df = self.pipe_df.groupby(level=1).rolling(window=self.window).mean()
        self.pipe_df = self.pipe_df.reset_index(level=0, drop=True)
        self.pipe_df = self.pipe_df.reset_index()
        self.pipe_df = normal_index_df(self.pipe_df)


__all__ = ['BlockMoneyFlowFactor']

if __name__ == '__main__':
    f1 = BlockMoneyFlowFactor(start_timestamp='2019-01-01')

    print(f1.result_df)
