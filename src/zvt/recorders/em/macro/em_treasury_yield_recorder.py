# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Country
from zvt.domain.macro.monetary import TreasuryYield
from zvt.recorders.em import em_api


class EMTreasuryYieldRecorder(FixedCycleDataRecorder):
    entity_schema = Country
    data_schema = TreasuryYield
    entity_provider = "wb"
    provider = "em"

    def __init__(
        self,
        force_update=True,
        sleeping_time=10,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="ignore",
        start_timestamp=None,
        end_timestamp=None,
        level=IntervalLevel.LEVEL_1DAY,
        kdata_use_begin_time=False,
        one_day_trading_minutes=24 * 60,
        return_unfinished=False,
    ) -> None:
        super().__init__(
            force_update,
            sleeping_time,
            None,
            None,
            None,
            None,
            ["CN"],
            True,
            entity_filters,
            ignore_failed,
            real_time,
            fix_duplicate_way,
            start_timestamp,
            end_timestamp,
            level,
            kdata_use_begin_time,
            one_day_trading_minutes,
            return_unfinished,
        )

    def record(self, entity, start, end, size, timestamps):
        # record before
        if start:
            result = em_api.get_treasury_yield(pn=1, ps=size, fetch_all=False)
        else:
            result = em_api.get_treasury_yield(fetch_all=True)
        if result:
            df = pd.DataFrame.from_records(result)
            df_to_db(
                data_schema=self.data_schema,
                df=df,
                provider=self.provider,
                force_update=True,
                drop_duplicates=True,
            )


if __name__ == "__main__":
    r = EMTreasuryYieldRecorder()
    r.run()


# the __all__ is generated
__all__ = ["EMTreasuryYieldRecorder"]
