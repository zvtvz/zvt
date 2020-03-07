-- 由于创建的table有不少使用了enum,导致有类似的约束
-- 	constraint provider
-- 		check (provider IN ('eastmoney', 'sina', 'netease'))
-- 当需要在原来的数据文件上做扩展时,可以去掉约束并做数据迁移
create table indices1
(
  id          VARCHAR(128) not null,
  provider    VARCHAR(9)   not null,
  timestamp   DATETIME,
  exchange    VARCHAR(32),
  type        VARCHAR(5),
  code        VARCHAR(32),
  name        VARCHAR(32),
  is_delisted BOOLEAN,
  category    VARCHAR(8),
  primary key (id, provider),
  check (is_delisted IN (0, 1))
);

INSERT INTO indices1
SELECT *
FROM index;


DROP TABLE index;
ALTER TABLE indices1
  RENAME TO indices;

update income_statement set report_period='season3' where report_period='seanson3'
update finance_factor set report_period='season3' where report_period='seanson3'
update balance_sheet set report_period='season3' where report_period='seanson3'
update cash_flow_statement set report_period='season3' where report_period='seanson3'
