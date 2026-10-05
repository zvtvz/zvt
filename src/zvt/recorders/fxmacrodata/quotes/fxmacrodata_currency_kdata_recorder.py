# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain.meta.currency_meta import Currency
from zvt.domain.quotes.currency.currency_1d_kdata import Currency1dKdata
from zvt.recorders.fxmacrodata import fxmacrodata_api
from zvt.utils.pd_utils import pd_is_not_null


class FXMacroDataCurrencyKdataRecorder(FixedCycleDataRecorder):
    provider = fxmacrodata_api.PROVIDER
    entity_provider = fxmacrodata_api.PROVIDER
    entity_schema = Currency
    data_schema = Currency1dKdata

    def __init__(
        self,
        api_key=None,
        base_url=fxmacrodata_api.FXMACRODATA_API_BASE_URL,
        timeout=30,
        **kwargs,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        super().__init__(level=IntervalLevel.LEVEL_1DAY, **kwargs)

    def record(self, entity, start, end, size, timestamps):
        df = fxmacrodata_api.get_kdata(
            entity_id=entity.id,
            session=self.http_session,
            start_timestamp=start,
            end_timestamp=end,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )
        if pd_is_not_null(df):
            return df.to_dict("records")
        return []


__all__ = ["FXMacroDataCurrencyKdataRecorder"]
