# -*- coding: utf-8 -*-

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.meta.stockhk_meta import Stockhk
from zvt.recorders.em import em_api


class EMStockhkRecorder(Recorder):
    provider = "em"
    data_schema = Stockhk

    def run(self):
        df_south = em_api.get_tradable_list(entity_type="stockhk", hk_south=True)
        df_south = df_south.set_index("code", drop=False)
        df_south["south"] = True

        df = em_api.get_tradable_list(entity_type="stockhk")
        df = df.set_index("code", drop=False)
        df_other = df.loc[~df.index.isin(df_south.index)].copy()
        df_other["south"] = False
        df_to_db(df=df_south, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        df_to_db(df=df_other, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    recorder = EMStockhkRecorder()
    recorder.run()
# the __all__ is generated
__all__ = ["EMStockhkRecorder"]
