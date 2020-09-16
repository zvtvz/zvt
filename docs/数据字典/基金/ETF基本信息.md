#### ETF基本资料表

|报表简称|英文简称|报表简介|| |
|:---------:|:------:|--------|-----|-----|
|ETF基本资料|etf|该表主要提供了上市etf的基本信息|||
#### ETF基本资料字段说明
| 字段        | 含义     | 数据类型     | 主键 | 索引     |
| ----------- | -------- | ------------ | ---- | -------- |
| id          | 索引id   | varchar(128) | √    | 主键索引 |
| entity_id   | 数据id   | varchar(128) |      |          |
| timestamp   | 日期     | datetime     |      |          |
| entity_type | 数据类型 | varchar(64)  |      |          |
| exchange    | 证券市场 | varchar(32)  |      |          |
| code        | 证券代码 | varchar(64)  |      |          |
| name        | 证券简称 | varchar(128) |      |          |
| list_date   | 上市日   | datetime     |      |          |
| end_date    | 退市日   | datetime     |      |          |
| category    | 类别     | varchar(64)  |      |          |