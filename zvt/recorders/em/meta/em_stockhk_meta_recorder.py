# -*- coding: utf-8 -*-

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.meta.stockhk_meta import Stockhk
from zvt.recorders.em import em_api


class EMStockhkRecorder(Recorder):
    provider = 'em'
    data_schema = Stockhk

    def run(self):
        df = em_api.get_tradable_list(entity_type='stockhk')
        self.logger.info(df)
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=True)


if __name__ == '__main__':
    recorder = EMStockhkRecorder()
    recorder.run()
# the __all__ is generated
__all__ = ['EMStockhkRecorder']
