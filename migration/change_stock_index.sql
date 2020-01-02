alter table stock_index
	add entity_id VARCHAR(128);

alter table stock_index
	add report_date DATETIME;

alter table stock_index
	add report_period VARCHAR(128);

alter table stock_index
	add proportion FLOAT;

alter table stock_index
	add shares FLOAT ;

alter table stock_index
	add market_cap FLOAT;