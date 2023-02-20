-- k线数据去除索引，方便传输原始数据，重跑zvt会重建
-- 再压缩一下，大小为原来的1/10
drop index stock_1d_hfq_kdata_entity_id_index;
drop index stock_1d_hfq_kdata_code_index;
drop index stock_1d_hfq_kdata_timestamp_index;
VACUUM;