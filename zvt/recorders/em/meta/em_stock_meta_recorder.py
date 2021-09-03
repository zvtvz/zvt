# -*- coding: utf-8 -*-

from zvt.contract import Exchange
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import Stock
from zvt.recorders.em import em_api


class EMStockRecorder(Recorder):
    provider = 'em'
    data_schema = Stock

    def run(self):
        for exchange in [Exchange.sh, Exchange.sz]:
            df = em_api.get_tradable_list(entity_type='stock', exchange=exchange)
            self.logger.info(df)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=True)


if __name__ == '__main__':
    recorder = EMStockRecorder()
    recorder.run()
# the __all__ is generated
__all__ = ['EMStockRecorder']