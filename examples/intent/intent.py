# -*- coding: utf-8 -*-
def compare_kline():
    from zvt.api.intent import compare
    from zvt.domain import Index, Indexus, Index1dKdata, Indexus1dKdata

    Index.record_data()
    Indexus.record_data()
    Index1dKdata.record_data(entity_id="index_sh_000001")
    Indexus1dKdata.record_data(entity_id="indexus_us_SPX")

    compare(entity_ids=["index_sh_000001", "indexus_us_SPX"])


if __name__ == "__main__":
    compare_kline()
