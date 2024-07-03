# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.domain import Block, BlockCategory, BlockStock
from zvt.recorders.em import em_api


class EMBlockRecorder(Recorder):
    provider = "em"
    data_schema = Block

    def run(self):
        for block_category in [BlockCategory.concept, BlockCategory.industry]:
            df = em_api.get_tradable_list(entity_type="block", block_category=block_category)
            self.logger.info(df)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


class EMBlockStockRecorder(TimeSeriesDataRecorder):
    entity_provider = "em"
    entity_schema = Block

    provider = "em"
    data_schema = BlockStock

    def record(self, entity, start, end, size, timestamps):
        the_list = em_api.get_block_stocks(entity.id, entity.name)
        if the_list:
            df = pd.DataFrame.from_records(the_list)
            df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)
            self.logger.info("finish recording block:{},{}".format(entity.category, entity.name))
            self.sleep()


if __name__ == "__main__":
    recorder = EMBlockStockRecorder(day_data=True, sleeping_time=0)
    recorder.run()


# the __all__ is generated
__all__ = ["EMBlockRecorder", "EMBlockStockRecorder"]
