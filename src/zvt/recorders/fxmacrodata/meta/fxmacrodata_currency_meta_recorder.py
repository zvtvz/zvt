# -*- coding: utf-8 -*-
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.meta.currency_meta import Currency
from zvt.recorders.fxmacrodata import fxmacrodata_api


class FXMacroDataCurrencyRecorder(Recorder):
    provider = fxmacrodata_api.PROVIDER
    data_schema = Currency

    def __init__(self, codes=None, force_update=False, sleeping_time=10) -> None:
        self.codes = codes
        super().__init__(force_update=force_update, sleeping_time=sleeping_time)

    def run(self):
        df = fxmacrodata_api.get_currency_list(codes=self.codes)
        df_to_db(
            df=df,
            data_schema=self.data_schema,
            provider=self.provider,
            force_update=self.force_update,
        )


if __name__ == "__main__":
    recorder = FXMacroDataCurrencyRecorder(force_update=True)
    recorder.run()


__all__ = ["FXMacroDataCurrencyRecorder"]
