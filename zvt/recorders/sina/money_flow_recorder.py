# -*- coding: utf-8 -*-
from zvt.recorders.recorder import TimeSeriesDataRecorder


class MoneyFlowRecorder(TimeSeriesDataRecorder):
    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_zjlrqs?page=1&num=1000&sort=opendate&asc=0&bankuai=0%2Fnew_jrhy'
'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=1'
'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=0'