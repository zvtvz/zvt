# -*- coding: utf-8 -*-

from zvt.api.kdata import get_kdata_schema, get_kdata
from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import (
    Stock,
    Index,
    Block,
    StockKdataCommon,
    IndexKdataCommon,
    StockhkKdataCommon,
    StockusKdataCommon,
    BlockKdataCommon,
    Indexus,
    IndexusKdataCommon,
    Future,
    FutureKdataCommon,
    Currency,
    CurrencyKdataCommon,
    IndexhkKdataCommon,
)
from zvt.domain.meta.indexhk_meta import Indexhk
from zvt.domain.meta.stockhk_meta import Stockhk
from zvt.domain.meta.stockus_meta import Stockus
from zvt.recorders.em import em_api
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import count_interval, now_pd_timestamp, current_date


class BaseEMStockKdataRecorder(FixedCycleDataRecorder):
    default_size = 50000
    entity_provider: str = "em"

    provider = "em"

    def __init__(
        self,
        force_update=True,
        sleeping_time=10,
        exchanges=None,
        entity_id=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="ignore",
        start_timestamp=None,
        end_timestamp=None,
        level=IntervalLevel.LEVEL_1DAY,
        kdata_use_begin_time=False,
        one_day_trading_minutes=24 * 60,
        adjust_type=AdjustType.qfq,
        return_unfinished=False,
    ) -> None:
        level = IntervalLevel(level)
        self.adjust_type = AdjustType(adjust_type)
        self.entity_type = self.entity_schema.__name__.lower()

        self.data_schema = get_kdata_schema(entity_type=self.entity_type, level=level, adjust_type=self.adjust_type)

        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
            entity_id,
            entity_ids,
            code,
            codes,
            day_data,
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

    def need_redownload_qfq(self, entity_id, df):
        if self.adjust_type == AdjustType.qfq and pd_is_not_null(df):
            datas = get_kdata(
                entity_id=entity_id,
                provider=self.provider,
                limit=1,
                level=self.level,
                adjust_type=self.adjust_type,
                order=self.data_schema.timestamp.desc(),
                return_type="domain",
            )
            if datas:
                latest_kdata = datas[0]
                check_df = df[df["timestamp"] == latest_kdata.timestamp]
                if pd_is_not_null(check_df):
                    old = latest_kdata.close
                    new = check_df.iloc[0, :]["close"]
                    # 相同时间的close不同，表明前复权需要重新计算
                    if round(old, 2) != round(new, 2):
                        # 删掉重新获取
                        self.session.query(self.data_schema).filter(self.data_schema.entity_id == entity_id).delete()
                        return True
                    else:
                        return False
                else:
                    raise Exception("前复权检查失败")
        return False

    def record(self, entity, start, end, size, timestamps):
        df = em_api.get_kdata(
            session=self.http_session, entity_id=entity.id, limit=size, adjust_type=self.adjust_type, level=self.level
        )

        if self.need_redownload_qfq(entity.id, df):
            df = em_api.get_kdata(
                session=self.http_session,
                entity_id=entity.id,
                limit=self.default_size,
                adjust_type=self.adjust_type,
                level=self.level,
            )

        delisted = False
        if pd_is_not_null(df):
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
            latest_timestamp = df.iloc[-1, :]["timestamp"]
            days = count_interval(latest_timestamp, now_pd_timestamp())
            if days > 200:
                delisted = True
        else:
            self.logger.info(f"no kdata for {entity.id}")

        if delisted and ("退市" not in entity.name):
            entity.name = entity.name + "退市"
            self.logger.info(f"set {entity.id} name as {entity.name}")
            self.entity_session.add(entity)
            self.entity_session.commit()

    def on_finish_entity(self, entity):
        # fill timestamp
        if not entity.timestamp or not entity.list_date:
            # get the first
            kdatas = self.data_schema.query_data(
                provider=self.provider,
                entity_id=entity.id,
                order=self.data_schema.timestamp.asc(),
                limit=1,
                return_type="domain",
            )
            if kdatas:
                timestamp = kdatas[0].timestamp

                self.logger.info(f"fill {entity.name} list_date as {timestamp}")

                if not entity.timestamp:
                    entity.timestamp = timestamp
                if not entity.list_date:
                    entity.list_date = timestamp
                self.entity_session.add(entity)
                self.entity_session.commit()


class EMStockKdataRecorder(BaseEMStockKdataRecorder):
    entity_schema = Stock
    data_schema = StockKdataCommon

    def on_finish_entity(self, entity):
        super().on_finish_entity(entity)
        # fill holder
        if not entity.holder_modified_date or (count_interval(entity.holder_modified_date, now_pd_timestamp()) > 30):
            holder = em_api.get_controlling_shareholder(code=entity.code)
            if holder:
                entity.controlling_holder = holder.get("holder")
                if holder.get("parent"):
                    entity.controlling_holder_parent = holder.get("parent")
                else:
                    entity.controlling_holder_parent = holder.get("holder")
                entity.holder_modified_date = current_date()
                self.entity_session.add(entity)
                self.entity_session.commit()
            holder_stats = em_api.get_top_ten_free_holder_stats(code=entity.code)
            if holder_stats:
                entity.top_ten_ratio = holder_stats.get("ratio")
                entity.holder_modified_date = current_date()
                self.entity_session.add(entity)
                self.entity_session.commit()


class EMStockusKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Stockus
    data_schema = StockusKdataCommon


class EMStockhkKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Stockhk
    data_schema = StockhkKdataCommon


class EMIndexhkKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Indexhk
    data_schema = IndexhkKdataCommon


class EMIndexKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Index

    data_schema = IndexKdataCommon


class EMIndexusKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Indexus

    data_schema = IndexusKdataCommon


class EMBlockKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Block

    data_schema = BlockKdataCommon


class EMFutureKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Future

    data_schema = FutureKdataCommon


class EMCurrencyKdataRecorder(BaseEMStockKdataRecorder):
    entity_provider = "em"
    entity_schema = Currency

    data_schema = CurrencyKdataCommon


if __name__ == "__main__":
    normal_ids = get_entity_ids_by_filter(entity_type="indexhk", provider="em")

    recorder = EMIndexhkKdataRecorder(
        entity_ids=normal_ids,
        level=IntervalLevel.LEVEL_1DAY,
        sleeping_time=2,
        adjust_type=AdjustType.qfq,
        day_data=True,
    )
    recorder.run()


# the __all__ is generated
__all__ = [
    "BaseEMStockKdataRecorder",
    "EMStockKdataRecorder",
    "EMStockusKdataRecorder",
    "EMStockhkKdataRecorder",
    "EMIndexhkKdataRecorder",
    "EMIndexKdataRecorder",
    "EMIndexusKdataRecorder",
    "EMBlockKdataRecorder",
    "EMFutureKdataRecorder",
    "EMCurrencyKdataRecorder",
]
