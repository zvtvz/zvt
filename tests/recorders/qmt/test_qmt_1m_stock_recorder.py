import unittest

import pandas as pd

from zvt.contract import AdjustType, IntervalLevel
from zvt.domain import Stock1mKdata
from zvt.recorders.qmt.quotes import QMTStockKdataRecorder


class MyTestCase(unittest.TestCase):
    def test_qmt_stock_recorder(self):
        # 注意这里回测时，timestamp是当前时间，是需要15:00这一根额外的k线用于分析完整当日数据的，
        # 但是实时交易时，可能取不到这根K线
        trade_start_minute = pd.Timestamp('2024-01-02 9:30')
        trade_end_minute = pd.Timestamp('2024-01-02 15:00')
        old_trade_start_minute = pd.Timestamp('2014-01-02 9:30')
        old_trade_end_minute = pd.Timestamp('2014-01-02 15:00')
        recorder = QMTStockKdataRecorder(
            entity_id="stock_sz_000488", adjust_type=AdjustType.qfq, level=IntervalLevel.LEVEL_1MIN,
            start_timestamp=trade_start_minute, end_timestamp=trade_end_minute,
            download_history_data=True
        )
        # 先手动删除了这股票的全部数据，恢复初始状态
        recorder.session.query(recorder.data_schema).filter(
            recorder.data_schema.entity_id == "stock_sz_000488",
            recorder.data_schema.timestamp >= trade_start_minute,
            recorder.data_schema.timestamp <= trade_end_minute
        ).delete()
        recorder.session.query(recorder.data_schema).filter(
            recorder.data_schema.entity_id == "stock_sz_000488",
            recorder.data_schema.timestamp >= old_trade_start_minute,
            recorder.data_schema.timestamp <= old_trade_end_minute
        ).delete()
        recorder.run()
        records = Stock1mKdata.query_data(provider="qmt", entity_ids=["stock_sz_000488"],
                                          start_timestamp=trade_start_minute, end_timestamp=trade_end_minute, )
        self.assertEqual(records.shape[0], 241)
        # 不使用download_history_data参数则无视历史数据，直接认为
        QMTStockKdataRecorder(
            entity_id="stock_sz_000488", adjust_type=AdjustType.qfq, level=IntervalLevel.LEVEL_1MIN,
            start_timestamp=old_trade_start_minute, end_timestamp=old_trade_end_minute,
        ).run()
        records = Stock1mKdata.query_data(
            provider="qmt", entity_ids=["stock_sz_000488"],
            start_timestamp=old_trade_start_minute, end_timestamp=old_trade_end_minute,

        )
        self.assertEqual(records.shape[0], 0)

        # 历史数据也要下载，因为不太可能一次性把全部数据爬下来，边跑回测边下载河里一点
        QMTStockKdataRecorder(
            entity_id="stock_sz_000488", adjust_type=AdjustType.qfq, level=IntervalLevel.LEVEL_1MIN,
            start_timestamp=old_trade_start_minute, end_timestamp=old_trade_end_minute,
            download_history_data=True
        ).run()
        records = Stock1mKdata.query_data(
            provider="qmt", entity_ids=["stock_sz_000488"],
            start_timestamp=old_trade_start_minute, end_timestamp=old_trade_end_minute,

        )
        self.assertEqual(records.shape[0], 241)


if __name__ == '__main__':
    unittest.main()
