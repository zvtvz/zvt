#### ETF行情表

| 报表简称 | 英文简称                     | 报表简介                                          | 表名                                                         |      |
| -------- | ---------------------------- | :------------------------------------------------ | :----------------------------------------------------------- | ------------------------------------------------------------ |
| ETF行情 | etf_1d_kdata |ETF行情数据，支持日线级别| etf_1d_kdata、（前复权）etf_1d_hfq_kdata、（后复权）etf_1d_bfq_kdata、（不复权） ||
#### ETF行情表字段说明

| 字段          | 含义     | 数据类型     | 备注 | 索引     |
| :-----------: | :------: | :----------: | ---- | -------- |
| id            | 索引id   | varchar(128) |     | 主键索引 |
| entity_id     | 数据id   | varchar(128) |      |          |
| timestamp     | 日期     | datetime     |      |          |
| provider      | 数据源   | varchar(32)  |      |          |
| code          | 证券代码 | varchar(32)  |      |          |
| name          | 证券简称 | varchar(32)  |      |          |
| level         | 开盘价   | varchar(32)  |      |          |
| open          | 开盘价   | float        |      |          |
| close         | 收盘价     | float        |      |          |
| high          | 最高价   | float        |      |          |
| low           | 最低价   | float        |      |          |
| volume        | 成交量   | float        |      |          |
| turnover      | 成交金额 | float        |      |          |
| change_pct    | 涨跌幅   | float        |      |          |
| turnover_rate | 换手率   | float        |      |          |