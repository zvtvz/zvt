# -*- coding: utf-8 -*-

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.meta.country_meta import Country
from zvt.recorders.wb import wb_api


class WBCountryRecorder(Recorder):
    provider = "wb"
    data_schema = Country

    def run(self):
        df = wb_api.get_countries()
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    recorder = WBCountryRecorder()
    recorder.run()


# the __all__ is generated
__all__ = ["WBCountryRecorder"]
