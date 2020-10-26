#### ETF投资组合

|报表简称|英文简称|报表简介|| |
|:---------:|:------:|--------|-----|-----|
|ETF投资组合|etf_stock|该表主要提供了上市etf的投资组合|||
#### ETF投资组合表字段说明
| 字段          | 含义           | 数据类型     | 长度 | 主键 | 索引     |
| ------------- | -------------- | ------------ | ---- | ---- | -------- |
| id            | 索引id         | varchar(128) | 128  | √    | 主键索引 |
| entity_id     | 数据id         | varchar(128) | 128  |      |          |
| timestamp     | 更新日期       | datetime     |      |      |          |
| entity_type   | 数据类型       | varchar(64)  |      |      |          |
| exchange      | ETF市场        | varchar(32)  | 32   |      |          |
| code          | ETF代码        | varchar(64)  | 64   |      |          |
| name          | ETF名称        | varchar(128) | 128  |      |          |
| stock_id      | 证券id         | varchar(64)  | 64   |      |          |
| stock_code    | 证券代码       | varchar(64)  |      |      |          |
| stock_name    | 证券简称       | varchar(128) |      |      |          |
| report_period | 报告期         | varchar(32)  |      |      |          |
| report_date   | 报告日         | datetime     |      |      |          |
| proportion    | 占净值比例     | float        |      |      |          |
| shares        | 持有股票的数量 | float        |      |      |          |
| market_cap    | 持有股票的市值 | float        |      |      |          |