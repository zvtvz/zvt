select * from stock_valuation where CAST(strftime('%s', timestamp)  AS  integer) ==CAST(strftime('%s', '2009-12-14')  AS  integer) ;
